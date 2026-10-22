#ifndef FLEXIV_PDK_WATCH_STREAM_HPP_
#define FLEXIV_PDK_WATCH_STREAM_HPP_

// Internal implementation detail of watch::Subscriber. SDK users do not use
// these types directly; see subscriber.hpp, subscription.hpp and options.hpp
// for the public API. The comments below describe the implementation.

#include <grpcpp/client_context.h>
#include <grpcpp/support/sync_stream.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <functional>
#include <memory>
#include <mutex>
#include <thread>

#include "flexiv/pdk/watch/options.hpp"

namespace flexiv {
namespace pdk {
namespace watch {
namespace detail {

/// Non-templated base so a Subscription / Subscriber can hold and stop a stream
/// without knowing its event type.
class StreamBase
{
public:
  virtual ~StreamBase() = default;

  /// Cancel the stream, stop reconnecting and join the worker thread.
  /// Idempotent. After Stop() returns, the worker will not invoke the callback
  /// again (note: an asynchronous Executor remains responsible for the safety
  /// of any work it has already posted to another thread).
  void Stop();

  bool active() const noexcept { return active_.load(); }

protected:
  virtual void Join() = 0;

  std::atomic<bool> active_ {true};

  std::mutex ctx_mutex_;
  std::unique_ptr<grpc::ClientContext> ctx_;

  std::mutex wait_mutex_;
  std::condition_variable wait_cv_;
};

/// Owns one background thread that opens a server-streaming reader, reads
/// events and delivers them to a callback, reconnecting with backoff.
template <typename EventT>
class Stream : public StreamBase
{
public:
  using ReaderPtr = std::unique_ptr<grpc::ClientReaderInterface<EventT>>;
  using Opener = std::function<ReaderPtr(grpc::ClientContext*)>;
  using Callback = std::function<void(const EventT&)>;

  Stream(Opener opener, Callback callback, Options options)
  : opener_(std::move(opener))
  , callback_(std::move(callback))
  , options_(std::move(options))
  {
    worker_ = std::thread([this] { Run(); });
  }

  ~Stream() override { Stop(); }

protected:
  void Join() override
  {
    if (worker_.joinable() && worker_.get_id() != std::this_thread::get_id()) {
      worker_.join();
    }
  }

private:
  void Run()
  {
    auto backoff = options_.backoff_initial;
    int attempt = 0;

    while (active_.load()) {
      {
        std::lock_guard<std::mutex> lock(ctx_mutex_);
        if (!active_.load()) {
          break;
        }
        ctx_ = std::make_unique<grpc::ClientContext>();
      }

      auto reader = opener_(ctx_.get());

      EventT event;
      while (active_.load() && reader != nullptr && reader->Read(&event)) {
        // A successful read means the connection is healthy; reset backoff.
        attempt = 0;
        backoff = options_.backoff_initial;
        Deliver(event);
      }

      if (reader != nullptr) {
        reader->Finish();
      }

      {
        std::lock_guard<std::mutex> lock(ctx_mutex_);
        ctx_.reset();
      }

      if (!active_.load() || !options_.reconnect) {
        break;
      }
      if (options_.max_retries >= 0 && attempt >= options_.max_retries) {
        break;
      }
      ++attempt;

      // Sleep for the backoff interval, but wake immediately on Stop().
      std::unique_lock<std::mutex> wait_lock(wait_mutex_);
      wait_cv_.wait_for(wait_lock, backoff, [this] { return !active_.load(); });

      const auto next = static_cast<std::chrono::milliseconds::rep>(
          static_cast<double>(backoff.count()) * options_.backoff_factor);
      backoff = std::min(options_.backoff_max, std::chrono::milliseconds(next));
    }

    // The watch has given up (reconnect off or retries exhausted), so it is no longer active.
    active_.store(false);
  }

  void Deliver(const EventT& event)
  {
    if (options_.executor) {
      EventT copy = event;
      Callback callback = callback_;
      options_.executor->Post([callback, copy] { callback(copy); });
    } else {
      callback_(event);
    }
  }

  Opener opener_;
  Callback callback_;
  Options options_;
  std::thread worker_;
};

} // namespace detail
} // namespace watch
} // namespace pdk
} // namespace flexiv

#endif // FLEXIV_PDK_WATCH_STREAM_HPP_

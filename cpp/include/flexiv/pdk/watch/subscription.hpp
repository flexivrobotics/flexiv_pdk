#ifndef FLEXIV_PDK_WATCH_SUBSCRIPTION_HPP_
#define FLEXIV_PDK_WATCH_SUBSCRIPTION_HPP_

#include <memory>

#include "flexiv/pdk/watch/stream.hpp"

namespace flexiv {
namespace pdk {
namespace watch {

class Subscriber;

/**
 * @brief Handle to an active watch, returned by Subscriber::Subscribe().
 *
 * The watch keeps running for as long as this handle is alive. To stop it,
 * destroy the handle, call reset(), or assign a new value over it; the server
 * stream is then cancelled and no further callbacks are delivered.
 *
 * Store the Subscription (for example as a class member) to keep receiving
 * events. Discarding the returned value immediately ends the watch.
 * Subscriptions are move-only.
 */
class Subscription
{
public:
  /// @brief Creates an empty handle that refers to no watch.
  Subscription() = default;
  ~Subscription() { reset(); }

  Subscription(Subscription&&) noexcept = default;
  Subscription& operator=(Subscription&& other) noexcept
  {
    if (this != &other) {
      reset();
      stream_ = std::move(other.stream_);
    }
    return *this;
  }

  Subscription(const Subscription&) = delete;
  Subscription& operator=(const Subscription&) = delete;

  /**
   * @brief Stop the watch now.
   *
   * Cancels the stream and blocks until event delivery has fully stopped. Safe
   * to call multiple times; a no-op on an empty handle.
   */
  void reset()
  {
    if (stream_) {
      stream_->Stop();
      stream_.reset();
    }
  }

  /// @brief Returns true while the watch is running. False once it is stopped, or once it gives up
  /// because Options::reconnect is off or Options::max_retries is used up.
  bool active() const noexcept { return stream_ && stream_->active(); }
  /// @brief Returns true while the watch is running.
  explicit operator bool() const noexcept { return active(); }

private:
  friend class Subscriber;
  explicit Subscription(std::shared_ptr<detail::StreamBase> stream)
  : stream_(std::move(stream))
  {
  }

  std::shared_ptr<detail::StreamBase> stream_;
};

} // namespace watch
} // namespace pdk
} // namespace flexiv

#endif // FLEXIV_PDK_WATCH_SUBSCRIPTION_HPP_

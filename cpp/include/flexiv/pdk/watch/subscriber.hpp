#ifndef FLEXIV_PDK_WATCH_SUBSCRIBER_HPP_
#define FLEXIV_PDK_WATCH_SUBSCRIBER_HPP_

// An optional helper for consuming server-streaming ("watch") RPCs.
//
// watch::Subscriber turns a streaming RPC into a simple subscribe-and-callback
// API. Each Subscribe() call opens the stream on a background thread, invokes
// your callback for every event, and automatically reconnects if the stream
// drops. The returned Subscription controls how long the watch lives.
//
// Example:
//   watch::Subscriber subscriber;
//
//   watch::Subscription sub = subscriber.Subscribe<SceneEvent>(
//       // Open the stream (called again on each reconnect):
//       [client](grpc::ClientContext* ctx) {
//         WatchSceneEventsRequest req;
//         return client->scene_event().stub->WatchSceneEvents(ctx, req);
//       },
//       // Handle each event:
//       [](const SceneEvent& event) { /* ... */ });
//   // Keep `sub` alive for as long as you want to receive events.
//
// To run callbacks on a specific thread (such as a UI thread), set
// Options::executor. This helper has no dependency on any UI toolkit.

#include <grpcpp/client_context.h>
#include <grpcpp/support/sync_stream.h>

#include <functional>
#include <memory>
#include <mutex>
#include <vector>

#include "flexiv/pdk/watch/options.hpp"
#include "flexiv/pdk/watch/stream.hpp"
#include "flexiv/pdk/watch/subscription.hpp"

namespace flexiv {
namespace pdk {
namespace watch {

/// @brief Creates and tracks watch subscriptions opened against a server.
///
/// The Subscriber does not own or know about the Client; each Subscribe() call
/// supplies its own stream opener (which typically captures the client). The
/// Subscriber only tracks the resulting streams so it can stop them all on
/// destruction.
class Subscriber
{
public:
  template <typename EventT>
  using ReaderOpener
      = std::function<std::unique_ptr<grpc::ClientReaderInterface<EventT>>(grpc::ClientContext*)>;

  template <typename EventT>
  using EventCallback = std::function<void(const EventT&)>;

  Subscriber();
  ~Subscriber();

  Subscriber(const Subscriber&) = delete;
  Subscriber& operator=(const Subscriber&) = delete;

  /**
   * @brief Start watching a server-streaming RPC.
   *
   * @tparam EventT  The message type streamed by the RPC.
   * @param open     Opens the stream for one connection attempt; bind your stub
   *                 method and request here, e.g.
   *                 `[client, req](grpc::ClientContext* ctx) {
   *                    return client->scene_event().stub->WatchSceneEvents(ctx, req); }`.
   *                 Called again automatically on each reconnect.
   * @param on_event Called once per received event. Runs on
   *                 @ref Options::executor "options.executor"'s thread if set,
   *                 otherwise on a background thread.
   * @param options  Delivery thread and reconnect behaviour (see Options).
   * @return A handle that keeps the watch alive; destroy or reset() it to stop.
   */
  template <typename EventT>
  Subscription Subscribe(
      ReaderOpener<EventT> open, EventCallback<EventT> on_event, Options options = {})
  {
    auto stream = std::make_shared<detail::Stream<EventT>>(
        std::move(open), std::move(on_event), std::move(options));
    Register(stream);
    return Subscription(std::move(stream));
  }

  /**
   * @brief Stop every subscription created by this subscriber.
   *
   * Called automatically when the subscriber is destroyed.
   */
  void StopAll();

private:
  void Register(std::shared_ptr<detail::StreamBase> stream);

  std::mutex mutex_;
  std::vector<std::weak_ptr<detail::StreamBase>> streams_;
};

} // namespace watch
} // namespace pdk
} // namespace flexiv

#endif // FLEXIV_PDK_WATCH_SUBSCRIBER_HPP_

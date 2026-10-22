#ifndef FLEXIV_PDK_SESSION_HPP_
#define FLEXIV_PDK_SESSION_HPP_

// A Session bundles:
// 1. Client for making RPCs
// 2. watch::Subscriber for subscribing to server-streaming ("watch") events
//
// Example usage in main:
//   auto client = std::make_shared<flexiv::pdk::Client>();
//   flexiv::pdk::Session session(client);
//   MyEditor editor(&model, session);
//
// Example usage in an editor:
//   session.client().frame().stub->...
//   auto sub = session.watch().Subscribe<SceneEvent>(...);
//
// The Session (and therefore its Client and watch::Subscriber) must outlive
// every editor and viewer it is passed to. Destroying the Session stops all
// watch subscriptions it handed out.

#include <memory>

#include "flexiv/pdk/watch/subscriber.hpp"

namespace flexiv {
namespace pdk {

class Client;

/// @brief The shared SDK handle (connection + live-event subscriptions) given
/// to every GUI editor and viewer.
class Session
{
public:
  /**
   * @brief Create a session backed by @p client.
   * @param client Connected SDK client used for RPCs and for opening watch
   *               streams. May be null in tests/offline mode, in which case
   *               client() returns null and editors should skip any server
   *               interaction.
   */
  explicit Session(std::shared_ptr<Client> client);
  ~Session();

  Session(const Session&) = delete;
  Session& operator=(const Session&) = delete;

  /// @brief The connected client for making RPCs. May be null in offline mode.
  Client* client() { return client_.get(); }

  /// @brief Shared client pointer, for code that needs to capture it.
  std::shared_ptr<Client> client_ptr() const { return client_; }

  /// @brief The shared subscriber for subscribing to server-streaming RPCs.
  watch::Subscriber& watch() { return watch_; }

private:
  std::shared_ptr<Client> client_;
  watch::Subscriber watch_;
};

} // namespace pdk
} // namespace flexiv

#endif // FLEXIV_PDK_SESSION_HPP_

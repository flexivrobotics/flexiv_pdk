#ifndef FLEXIV_PDK_WATCH_OPTIONS_HPP_
#define FLEXIV_PDK_WATCH_OPTIONS_HPP_

#include <chrono>
#include <memory>

#include "flexiv/pdk/watch/executor.hpp"

namespace flexiv {
namespace pdk {
namespace watch {

/**
 * @brief Configures how a watch delivers events and recovers from disconnects.
 *
 * Pass an Options to Subscriber::Subscribe() to customize behaviour. The defaults
 * deliver events on a background thread and reconnect automatically using
 * exponential backoff, so you usually only need to set @ref executor.
 */
struct Options
{
  /**
   * @brief Thread on which event callbacks are delivered.
   *
   * Leave null to receive callbacks on the watch's background thread. Set it to
   * deliver callbacks on a specific thread, such as a UI thread (see Executor).
   */
  std::shared_ptr<Executor> executor;

  /// @brief Whether to automatically reopen the stream after it closes.
  bool reconnect = true;

  /// @brief Delay before the first reconnect attempt (reset after each
  /// successful event).
  std::chrono::milliseconds backoff_initial {500};
  /// @brief Maximum delay between reconnect attempts.
  std::chrono::milliseconds backoff_max {10000};
  /// @brief Multiplier applied to the delay after each failed attempt.
  double backoff_factor = 2.0;

  /// @brief Maximum number of reconnect attempts; -1 means unlimited.
  int max_retries = -1;
};

} // namespace watch
} // namespace pdk
} // namespace flexiv

#endif // FLEXIV_PDK_WATCH_OPTIONS_HPP_

#ifndef FLEXIV_PDK_WATCH_EXECUTOR_HPP_
#define FLEXIV_PDK_WATCH_EXECUTOR_HPP_

#include <functional>

namespace flexiv {
namespace pdk {
namespace watch {

/**
 * @brief Controls which thread a watch callback is delivered on.
 *
 * By default the SDK invokes your watch callbacks on an internal background
 * thread. If a callback must run on a particular thread (for example a UI
 * toolkit's main thread), implement an Executor that forwards work to that
 * thread and pass it via Options::executor.
 *
 * The SDK is UI-toolkit agnostic: typically you wrap your framework's
 * "run on the main thread" primitive inside Post().
 */
class Executor
{
public:
  virtual ~Executor() = default;

  /**
   * @brief Schedule @p fn to run on this executor's thread.
   * @param fn The work to run. It may execute before or after Post() returns.
   */
  virtual void Post(std::function<void()> fn) = 0;
};

/**
 * @brief Default executor that runs callbacks immediately, in place.
 *
 * With this executor (or when no executor is supplied) events are delivered
 * directly on the watch's background thread.
 */
class InlineExecutor : public Executor
{
public:
  void Post(std::function<void()> fn) override { fn(); }
};

} // namespace watch
} // namespace pdk
} // namespace flexiv

#endif // FLEXIV_PDK_WATCH_EXECUTOR_HPP_

#include "flexiv/pdk/watch/stream.hpp"

namespace flexiv {
namespace pdk {
namespace watch {
namespace detail {

void StreamBase::Stop()
{
  // Mark inactive first so the worker loop and read loop observe the request.
  active_.store(false);

  // Cancel any in-progress RPC so a blocking Read() returns promptly.
  {
    std::lock_guard<std::mutex> lock(ctx_mutex_);
    if (ctx_) {
      ctx_->TryCancel();
    }
  }

  // Wake the worker if it is sleeping between reconnect attempts.
  {
    std::lock_guard<std::mutex> lock(wait_mutex_);
  }
  wait_cv_.notify_all();

  Join();
}

} // namespace detail
} // namespace watch
} // namespace pdk
} // namespace flexiv

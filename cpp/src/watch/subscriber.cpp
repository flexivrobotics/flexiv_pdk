#include "flexiv/pdk/watch/subscriber.hpp"

#include <algorithm>

namespace flexiv {
namespace pdk {
namespace watch {

Subscriber::Subscriber() = default;

Subscriber::~Subscriber()
{
  StopAll();
}

void Subscriber::Register(std::shared_ptr<detail::StreamBase> stream)
{
  std::lock_guard<std::mutex> lock(mutex_);

  // Opportunistically drop expired entries to keep the registry from growing.
  streams_.erase(std::remove_if(streams_.begin(), streams_.end(),
                     [](const std::weak_ptr<detail::StreamBase>& w) { return w.expired(); }),
      streams_.end());

  streams_.push_back(stream);
}

void Subscriber::StopAll()
{
  std::vector<std::weak_ptr<detail::StreamBase>> streams;
  {
    std::lock_guard<std::mutex> lock(mutex_);
    streams.swap(streams_);
  }

  for (const auto& weak : streams) {
    if (auto stream = weak.lock()) {
      stream->Stop();
    }
  }
}

} // namespace watch
} // namespace pdk
} // namespace flexiv

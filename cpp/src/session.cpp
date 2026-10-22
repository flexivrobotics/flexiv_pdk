#include "flexiv/pdk/session.hpp"

namespace flexiv {
namespace pdk {

Session::Session(std::shared_ptr<Client> client)
: client_(std::move(client))
{
}

Session::~Session() = default;

} // namespace pdk
} // namespace flexiv

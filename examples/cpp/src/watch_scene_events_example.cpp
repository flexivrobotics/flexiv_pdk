/**
 * @file watch_scene_events_example.cpp
 * @brief Example: Watch server-side scene events using the Flexiv PDK.
 *
 * The scene-event service exposes a server-streaming RPC,
 * WatchSceneEvents(WatchSceneEventsRequest) returns (stream SceneEvent), the single
 * change-notification channel for the scene. It pushes a SceneEvent whenever a config model is
 * added/updated/removed/renamed (origin=CONFIG) or a frame is moved directly in the transform layer
 * (origin=FRAME). Each event names both the affected model (entity) and the affected frames
 * (frames).
 *
 * This program demonstrates two ways to consume such a stream:
 *   1. watch::Subscriber + callback (background thread, auto-reconnect) - best for GUIs and
 *      long-lived subscriptions.
 *   2. A blocking read loop on the calling thread - best for scripts. Unlike the Python watch()
 *      generator, it does not reconnect; use watch::Subscriber for that.
 */

#include <flexiv/pdk/client.hpp>
#include <flexiv/pdk/scene_event_service.pb.h>
#include <flexiv/pdk/watch/subscriber.hpp>

#include <chrono>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <thread>

using flexiv::pdk::Client;
using flexiv::pdk::ConfigType_Name;
using flexiv::pdk::SceneEvent;
using flexiv::pdk::WatchSceneEventsRequest;

namespace {

std::string ServerAddress()
{
  const char* address = std::getenv("PDK_SERVER_ADDR");
  return address != nullptr ? address : "localhost:50052";
}

std::string Describe(const SceneEvent& event)
{
  std::ostringstream text;
  text << "change=" << SceneEvent::Change_Name(event.change())
       << " origin=" << SceneEvent::Origin_Name(event.origin()) << " entity=";
  if (event.has_entity()) {
    text << ConfigType_Name(event.entity().type()) << ":'" << event.entity().name() << "'";
  } else {
    text << "-";
  }
  text << " frames=[";
  for (int i = 0; i < event.frames_size(); ++i) {
    text << (i > 0 ? ", " : "") << "'" << event.frames(i) << "'";
  }
  text << "]";
  return text.str();
}

} // namespace

int main()
{
  const std::string target = ServerAddress();
  std::cout << "Connecting to the PDK server at " << target << "..." << std::endl;

  Client client(target);
  const WatchSceneEventsRequest request; // empty filters => all origins/types

  // ---- Option 1: background Subscriber with a callback ----------------------
  std::cout << "Watching scene events on a background thread for 3 seconds..." << std::endl;
  {
    flexiv::pdk::watch::Subscriber subscriber;
    flexiv::pdk::watch::Subscription subscription = subscriber.Subscribe<SceneEvent>(
        // Open the stream; called again on each reconnect.
        [&client, &request](grpc::ClientContext* context) {
          return client.scene_event().stub->WatchSceneEvents(context, request);
        },
        // Called on the worker thread for each event.
        [](const SceneEvent& event) {
          std::cout << "  [callback] " << Describe(event) << std::endl;
        });

    std::this_thread::sleep_for(std::chrono::seconds(3)); // do other work meanwhile
    subscription.reset(); // stops the stream and waits for the worker to finish
  }
  std::cout << "Stopped background subscription." << std::endl;

  // ---- Option 2: blocking read loop -----------------------------------------
  std::cout << "Watching scene events synchronously (Ctrl-C to stop)..." << std::endl;
  grpc::ClientContext context;
  auto reader = client.scene_event().stub->WatchSceneEvents(&context, request);
  SceneEvent event;
  while (reader->Read(&event)) {
    std::cout << "  [blocking] " << Describe(event) << std::endl;
  }
  const grpc::Status status = reader->Finish();
  if (!status.ok()) {
    std::cerr << "WatchSceneEvents failed or no server running: " << status.error_message()
              << std::endl;
  }

  return 0;
}

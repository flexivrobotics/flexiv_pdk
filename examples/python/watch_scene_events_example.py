"""
Example: Watch server-side scene events using the Flexiv PDK.

The scene-event service exposes a server-streaming RPC,
``WatchSceneEvents(WatchSceneEventsRequest) returns (stream SceneEvent)``, the
single change-notification channel for the scene. It pushes a SceneEvent
whenever a config model is added/updated/removed/renamed (origin=CONFIG) or a
frame is moved directly in the transform layer (origin=FRAME). Each event names
both the affected model (``entity``) and the affected frames (``frames``).

This script demonstrates the two ways the SDK lets you consume such a stream:

  1. Subscriber + callback (background thread, auto-reconnect) — best for GUIs
     and long-lived subscriptions.
  2. The watch() generator (blocking, single-threaded) — best for scripts.
"""
import os
import time

import grpc

from flexiv.pdk import Client
from flexiv.pdk.watch import Subscriber, watch
from flexiv.pdk.config_service_pb2 import ConfigType
from flexiv.pdk.scene_event_service_pb2 import SceneEvent, WatchSceneEventsRequest


def describe(event) -> str:
    entity = (f"{ConfigType.Name(event.entity.type)}:{event.entity.name!r}"
              if event.HasField("entity") else "-")
    return (
        f"change={SceneEvent.Change.Name(event.change)} "
        f"origin={SceneEvent.Origin.Name(event.origin)} "
        f"entity={entity} frames={list(event.frames)}"
    )


def main():
    target = os.environ.get("PDK_SERVER_ADDR", "localhost:50052")
    print(f"Connecting to the PDK server at {target}...")

    with Client(target) as client:
        request = WatchSceneEventsRequest()  # empty filters => all origins/types

        # ---- Option 1: background Subscriber with a callback ----------------
        print("Watching scene events on a background thread for 3 seconds...")
        subscriber = Subscriber()
        subscription = subscriber.subscribe(
            lambda: client.scene_event.stub.WatchSceneEvents(request),
            lambda event: print(f"  [callback] {describe(event)}"),
        )
        try:
            time.sleep(3.0)  # do other work; events arrive on the worker thread
        finally:
            subscription.close()  # stops the stream and joins the worker
        print("Stopped background subscription.")

        # ---- Option 2: blocking generator -----------------------------------
        print("Watching scene events synchronously (Ctrl-C to stop)...")
        try:
            for event in watch(lambda: client.scene_event.stub.WatchSceneEvents(request)):
                print(f"  [generator] {describe(event)}")
        except KeyboardInterrupt:
            print("Interrupted; the underlying stream is cancelled on exit.")
        except grpc.RpcError as error:
            print(f"WatchSceneEvents failed or no server running: {error}")


if __name__ == "__main__":
    main()

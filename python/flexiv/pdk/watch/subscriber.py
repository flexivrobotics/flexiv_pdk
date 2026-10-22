"""Creates and tracks watch subscriptions.

Mirrors the C++ ``watch::Subscriber`` (see
``cpp/include/flexiv/pdk/watch/subscriber.hpp``). The Subscriber does not own
or know about a :class:`~flexiv.pdk.Client`; each :meth:`subscribe` call
supplies its own stream opener (which typically captures the client). The
Subscriber only tracks the resulting subscriptions so it can stop them all.
"""

import weakref
from typing import Optional

from .options import Options
from .subscription import EventCallback, OpenStream, Subscription


class Subscriber:
    """Opens server-streaming ("watch") RPCs as background subscriptions."""

    def __init__(self) -> None:
        # WeakSet is the Python analogue of the C++ ``vector<weak_ptr>``:
        # stop_all() only stops still-live subscriptions, and ones the caller
        # already dropped are collected automatically.
        self._subscriptions: "weakref.WeakSet[Subscription]" = weakref.WeakSet()

    def subscribe(
        self,
        open_stream: OpenStream,
        on_event: EventCallback,
        options: Optional[Options] = None,
    ) -> Subscription:
        """Start watching a server-streaming RPC.

        :param open_stream: Opens the stream for one connection attempt; bind
            your stub method and request here, e.g.
            ``lambda: client.scene_event.stub.WatchSceneEvents(request)``. Called again
            automatically on each reconnect.
        :param on_event: Called once per received event. Runs on
            ``options.executor``'s thread if set, otherwise on a background
            thread.
        :param options: Delivery thread and reconnect behaviour (see
            :class:`Options`).
        :return: A handle that keeps the watch alive; close it to stop.
        """
        subscription = Subscription(open_stream, on_event, options)
        self._subscriptions.add(subscription)
        return subscription

    def subscribe_rpc(
        self,
        stub_method,
        request,
        on_event: EventCallback,
        options: Optional[Options] = None,
    ) -> Subscription:
        """Convenience wrapper around :meth:`subscribe` for the common case of a
        single stub method and request.

        ``subscribe_rpc(stub.WatchSceneEvents, request, cb)`` is equivalent to
        ``subscribe(lambda: stub.WatchSceneEvents(request), cb)``.
        """
        return self.subscribe(lambda: stub_method(request), on_event, options)

    def stop_all(self) -> None:
        """Stop every subscription created by this subscriber."""
        for subscription in list(self._subscriptions):
            subscription.close()

    def __enter__(self) -> "Subscriber":
        return self

    def __exit__(self, *exc) -> None:
        self.stop_all()

    def __del__(self) -> None:  # best-effort
        try:
            self.stop_all()
        except Exception:
            pass

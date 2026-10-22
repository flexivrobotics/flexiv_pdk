"""Consume server-streaming ("watch") RPCs.

Two ways to watch a stream:

- :class:`Subscriber` / :class:`Subscription` — deliver events to a callback on
  a background thread, reconnecting automatically. Mirrors the C++
  ``watch::Subscriber``. Use this for GUIs / long-lived subscriptions.

- :func:`watch` — a blocking generator you iterate yourself
  (``for event in watch(...)``). Single-threaded; auto-reconnects. Use this for
  scripts and tests.

Both take an ``open_stream`` callable that opens the streaming RPC, e.g.
``lambda: client.scene_event.stub.WatchSceneEvents(request)``; it is called again on
each reconnect.
"""

import time
from typing import Iterator, Optional

from .options import Executor, Options
from .subscriber import Subscriber
from .subscription import OpenStream, Subscription, _stream_events

__all__ = ["Subscriber", "Subscription", "Options", "Executor", "watch"]


def watch(open_stream: OpenStream, options: Optional[Options] = None) -> Iterator:
    """Blocking generator that yields stream events, reconnecting with backoff.

    Stop by breaking out of the loop or closing the generator; either cancels
    the live server call. Single-threaded, so :attr:`Options.executor` is
    ignored.

    Example::

        for event in watch(lambda: client.scene_event.stub.WatchSceneEvents(req)):
            handle(event)
    """
    options = options or Options()
    # Plain interruptible sleep; the generator is stopped by the caller closing
    # it (GeneratorExit), not by a stop flag, so wait() never reports "stop".
    def wait(seconds: float) -> bool:
        time.sleep(seconds)
        return False

    yield from _stream_events(
        open_stream,
        options,
        is_active=lambda: True,
        wait=wait,
    )

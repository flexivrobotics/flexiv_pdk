"""Background-thread watch subscription.

Mirrors the C++ ``watch::Subscription`` + ``detail::Stream`` (see
``cpp/include/flexiv/pdk/watch/subscription.hpp`` and ``stream.hpp``). Python
duck-types events, so the templated ``Stream<EventT>`` collapses into this one
class: a :class:`Subscription` owns a single background worker thread that opens
a server-streaming call, delivers each event to a callback, and reconnects with
exponential backoff until closed.
"""

import logging
import threading
from typing import Callable, Iterator, Optional

import grpc

from .options import Options

_log = logging.getLogger("flexiv.pdk.watch")

#: Opens a fresh server-streaming call. Called again on each reconnect. Bind the
#: stub method and request here, e.g. ``lambda: stub.WatchSceneEvents(req)``.
OpenStream = Callable[[], Iterator]

#: Called once per received event. Runs on :attr:`Options.executor`'s thread if
#: set, otherwise on the watch's background worker thread.
EventCallback = Callable[[object], None]


class Subscription:
    """Handle to an active watch; the stream runs until this is closed.

    Closing the subscription (via :meth:`close`, the context manager, or
    garbage collection) cancels the server stream and stops delivering events.
    Store the subscription for as long as you want to keep receiving events.
    """

    def __init__(
        self,
        open_stream: OpenStream,
        on_event: EventCallback,
        options: Optional[Options] = None,
    ) -> None:
        self._open_stream = open_stream
        self._on_event = on_event
        self._options = options or Options()

        # ``_active`` is the "keep running" flag (C++ ``active_`` atomic).
        # ``_stop_event`` doubles as the interruptible backoff sleep (C++
        # ``wait_cv_``): set() both stops the loop and wakes a pending wait.
        self._active = True
        self._stop_event = threading.Event()

        # Guards the live call object so close() never cancels a stale/None call
        # (C++ ``ctx_mutex_``).
        self._call_lock = threading.Lock()
        self._call: Optional[Iterator] = None

        self._worker = threading.Thread(
            target=self._run, name="pdk-watch", daemon=True
        )
        self._worker.start()

    @property
    def active(self) -> bool:
        """True while the watch is running."""
        return self._active and self._worker.is_alive()

    def close(self, timeout: Optional[float] = None) -> None:
        """Stop the watch and join the worker thread.

        Idempotent and safe to call from any thread. If called from within the
        event callback (i.e. on the worker thread itself) the join is skipped to
        avoid a self-deadlock; the stream still stops promptly.

        :param timeout: Maximum seconds to wait for the worker to finish.
        """
        self._active = False
        self._stop_event.set()
        with self._call_lock:
            call = self._call
        if call is not None:
            try:
                call.cancel()
            except Exception:  # pragma: no cover - defensive
                pass

        if (
            self._worker.is_alive()
            and threading.get_ident() != self._worker.ident
        ):
            self._worker.join(timeout)

    def __enter__(self) -> "Subscription":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def __del__(self) -> None:  # best-effort; explicit close() is the supported path
        try:
            self.close(timeout=0)
        except Exception:
            pass

    # ------------------------------------------------------------------ worker

    def _run(self) -> None:
        for event in _stream_events(
            self._open_stream,
            self._options,
            is_active=lambda: self._active,
            wait=self._stop_event.wait,
            set_call=self._set_call,
        ):
            if not self._active:
                break
            self._deliver(event)

    def _set_call(self, call: Optional[Iterator]) -> None:
        with self._call_lock:
            self._call = call

    def _deliver(self, event: object) -> None:
        executor = self._options.executor
        if executor is not None:
            callback = self._on_event
            executor(lambda: _safe_call(callback, event))
        else:
            _safe_call(self._on_event, event)


def _safe_call(callback: EventCallback, event: object) -> None:
    """Invoke ``callback``; log and swallow exceptions so one bad event does not
    kill an auto-reconnecting stream.

    Note: this diverges from C++, where an exception escaping the callback
    terminates the worker thread.
    """
    try:
        callback(event)
    except Exception:
        _log.exception("watch event callback raised; continuing")


def _stream_events(
    open_stream: OpenStream,
    options: Options,
    is_active: Callable[[], bool],
    wait: Callable[[float], bool],
    set_call: Optional[Callable[[Optional[Iterator]], None]] = None,
) -> Iterator:
    """Shared open/read/reconnect loop, yielding each received event.

    Reused by both :class:`Subscription` (background thread) and the synchronous
    :func:`flexiv.pdk.watch.watch` generator, so the reconnect/backoff
    semantics live in one place and match the C++ ``Stream::Run`` exactly.

    :param is_active: Returns False once the consumer wants to stop.
    :param wait: Interruptible sleep; returns early (truthy) when stopping. For
        the threaded case this is ``threading.Event.wait``; for the generator a
        plain ``time.sleep``-style wrapper.
    :param set_call: If given, called with the live call object after each open
        (and ``None`` after it ends) so a background closer can cancel it.
    """
    backoff = options.backoff_initial_s
    attempt = 0

    while is_active():
        call = None
        try:
            call = open_stream()
            if set_call is not None:
                set_call(call)
            if not is_active():
                break
            for event in call:
                if not is_active():
                    break
                # A successful read means the connection is healthy.
                attempt = 0
                backoff = options.backoff_initial_s
                yield event
        except grpc.RpcError as error:
            # A stop sets is_active() False before cancelling the call, so this
            # tells our own cancel from a CANCELLED sent by the server, which
            # reconnects like any other error (as in C++).
            if not is_active():
                break
            _log.warning("watch stream error: %s", error)
        except Exception:
            _log.exception("watch stream opener/iteration failed")
        finally:
            if set_call is not None:
                set_call(None)
            if call is not None:
                try:
                    call.cancel()
                except Exception:
                    pass

        if not is_active() or not options.reconnect:
            break
        if options.max_retries >= 0 and attempt >= options.max_retries:
            break
        attempt += 1

        # Interruptible backoff sleep; wakes immediately on stop.
        if wait(backoff):
            break
        backoff = min(options.backoff_max_s, backoff * options.backoff_factor)

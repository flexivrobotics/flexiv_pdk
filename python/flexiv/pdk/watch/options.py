"""Configuration for watch subscriptions.

Mirrors the C++ ``watch::Options`` / ``watch::Executor`` (see
``cpp/include/flexiv/pdk/watch/options.hpp`` and ``executor.hpp``). The C++
``Executor`` abstract class collapses here into a plain callable: a function
that schedules a piece of work on a chosen thread.
"""

from dataclasses import dataclass
from typing import Callable, Optional

# Marshals a watch callback onto a chosen thread (for example a UI thread).
#
# Given ``fn``, an Executor runs ``fn()`` on its own thread. ``None`` (the
# default) means callbacks are delivered inline on the watch's background
# worker thread. This is the Python analogue of C++ ``watch::Executor::Post``.
Executor = Callable[[Callable[[], None]], None]


@dataclass
class Options:
    """How a watch delivers events and recovers from disconnects.

    The defaults deliver events on the watch's background thread and reconnect
    automatically using exponential backoff, so callers usually only set
    :attr:`executor`.
    """

    #: Thread on which event callbacks are delivered. ``None`` delivers them on
    #: the watch's background worker thread.
    executor: Optional[Executor] = None

    #: Whether to automatically reopen the stream after it closes.
    reconnect: bool = True

    #: Delay (seconds) before the first reconnect attempt; reset after each
    #: successful event. C++ default: 500 ms.
    backoff_initial_s: float = 0.5

    #: Maximum delay (seconds) between reconnect attempts. C++ default: 10 s.
    backoff_max_s: float = 10.0

    #: Multiplier applied to the delay after each failed attempt.
    backoff_factor: float = 2.0

    #: Maximum number of reconnect attempts; ``-1`` means unlimited.
    max_retries: int = -1

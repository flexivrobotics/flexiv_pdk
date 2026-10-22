Watching Scene Events
=====================

``SceneEventService.WatchSceneEvents`` is a **server-streaming** RPC and the
only change-notification channel for the scene. It sends one ``SceneEvent`` for
every committed change, in order. Use it to keep a GUI or a cache in sync with
the server.

Events
------

.. list-table:: ``SceneEvent``
   :header-rows: 1
   :widths: 18 82

   * - Field
     - Meaning
   * - ``change``
     - ``CHANGE_ADDED``, ``CHANGE_UPDATED``, ``CHANGE_REMOVED``,
       ``CHANGE_RENAMED``, or ``CHANGE_REFRESHED`` (bulk change: resynchronize
       everything).
   * - ``origin``
     - ``ORIGIN_CONFIG``: a saved config changed (persisted).
       ``ORIGIN_FRAME``: a frame moved in the transform layer only, such as an
       unsaved drag.
   * - ``entity``
     - Config type and name. Set only when ``origin == ORIGIN_CONFIG``.
   * - ``frames``
     - Names of frames created or moved. May be empty for a config event whose
       geometry was already current; that is normal.
   * - ``new_name``
     - For ``CHANGE_RENAMED``. ``entity.name`` and ``frames`` carry the old
       name.

``WatchSceneEventsRequest`` can filter by ``origin_filter`` (``ORIGIN_UNKNOWN``
streams all) and ``type_filter`` (``CONFIG_TYPE_ALL`` streams all; applies to
config events). An empty request streams everything.

Python
------

``flexiv.pdk.watch`` offers two ways to consume a stream. Both take an
``open_stream`` callable that opens the RPC, and call it again to **reconnect
automatically** with exponential backoff if the stream drops. A stream the
server ends, including with ``CANCELLED``, is reopened too; only ``close()``,
``stop_all()`` or leaving the loop stops it.

``Subscriber`` + callback
   Runs the stream on a background thread and calls your callback for each
   event. Best for GUIs and long-lived subscriptions. Call ``close()`` on the
   returned ``Subscription``, or ``stop_all()`` on the ``Subscriber``, to stop.
   Both also work as context managers.

``watch()`` generator
   A blocking generator you iterate yourself. Best for scripts and tests.
   Breaking out of the loop cancels the call.

.. literalinclude:: /../../examples/python/watch_scene_events_example.py
   :language: python
   :start-at: def describe(event)
   :end-before: if __name__ == "__main__":

Reconnection and threading are controlled by ``Options``:

.. code-block:: python

   from flexiv.pdk.watch import Options

   options = Options(
       executor=None,           # callable(fn) that runs fn on the thread you want
       reconnect=True,
       backoff_initial_s=0.5,
       backoff_max_s=10.0,
       backoff_factor=2.0,
       max_retries=-1,          # -1: retry forever
   )
   subscription = subscriber.subscribe(open_stream, on_event, options)

An ``executor`` lets you deliver events on a GUI thread. For example, with Qt:
``executor=lambda fn: QTimer.singleShot(0, fn)``. ``watch()`` is
single-threaded and ignores ``executor``.

Exceptions raised in your callback are logged (logger ``flexiv.pdk.watch``)
and the stream continues.

C++
---

``flexiv::pdk::watch::Subscriber`` (``<flexiv/pdk/watch/subscriber.hpp>``):

.. code-block:: cpp

   #include <flexiv/pdk/client.hpp>
   #include <flexiv/pdk/watch/subscriber.hpp>

   using flexiv::pdk::SceneEvent;
   using flexiv::pdk::WatchSceneEventsRequest;

   flexiv::pdk::watch::Subscriber subscriber;

   flexiv::pdk::watch::Subscription sub = subscriber.Subscribe<SceneEvent>(
       // Open the stream; called again on each reconnect.
       [&client](grpc::ClientContext* ctx) {
         WatchSceneEventsRequest req;
         return client.scene_event().stub->WatchSceneEvents(ctx, req);
       },
       // Handle each event.
       [](const SceneEvent& event) {
         std::cout << event.ShortDebugString() << std::endl;
       });

   // Events arrive while `sub` is alive. sub.reset() stops the stream and
   // waits until delivery has finished.

* ``Subscription`` is move-only. **Discarding the return value ends the
  watch immediately.**
* ``Options`` has the same fields as in Python, except that the backoff
  fields are ``backoff_initial`` and ``backoff_max`` (``std::chrono::milliseconds``)
  and ``executor`` is a ``std::shared_ptr<Executor>``.
* Implement ``watch::Executor::Post(std::function<void()>)`` to forward events
  to your UI thread. ``watch::InlineExecutor`` runs them directly.
* ``Subscriber::StopAll()`` stops every subscription; the destructor does too.
* Do not let exceptions escape the C++ callback.

Command line
------------

.. code-block:: bash

   pdk-scene watch     # prints events until Ctrl-C

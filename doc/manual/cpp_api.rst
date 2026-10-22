C++ API
=======

Hand-written reference for the C++ headers under ``include/flexiv/pdk/`` of an
installed ``flexiv_pdk`` (``cpp/include/flexiv/pdk/`` in the source repository).
Generated headers follow the proto paths: messages in ``.pb.h`` (for example
``flexiv/pdk/workcell/workcell_service.pb.h``) and stubs in ``.grpc.pb.h``.
Namespaces follow the proto packages (``flexiv::pdk::workcell``), with two
exceptions to note:

* ``SurfaceFinishService`` and its requests are in
  ``flexiv::pdk::surface_finish::generator``, not ``surface_finish``.
* ``MeshOperationService`` and its requests are in ``flexiv::pdk``, not
  ``flexiv::pdk::mesh_operation``.

CMake
-----

.. code-block:: cmake

   find_package(flexiv_pdk REQUIRED)
   target_link_libraries(my_app PRIVATE flexiv::flexiv_pdk)     # plain CMake
   ament_target_dependencies(my_node PUBLIC flexiv_pdk)        # ROS 2

The target requires C++17 and brings in Eigen3, gRPC and Protobuf. See
:doc:`/install_for_cpp`.

.. cpp:namespace:: flexiv::pdk

Client
------

``#include <flexiv/pdk/client.hpp>``

.. cpp:class:: template <typename ServiceT> ServiceClient

   Thin holder for a generated stub.

   .. cpp:member:: std::unique_ptr<typename ServiceT::Stub> stub

.. cpp:class:: Client

   Owns the gRPC channel and lazily creates service clients. Not copyable or
   movable.

   .. cpp:function:: explicit Client(const std::string& target = "localhost:50052")

      Create an insecure channel to *target*.

   .. cpp:function:: explicit Client(std::shared_ptr<grpc::Channel> channel)

      Use an existing channel. Throws ``std::invalid_argument`` if null.

   .. cpp:function:: VersionServiceClient& version()
   .. cpp:function:: LogServiceClient& log()
   .. cpp:function:: FrameServiceClient& frame()
   .. cpp:function:: SceneEventServiceClient& scene_event()
   .. cpp:function:: WorkcellServiceClient& workcell()
   .. cpp:function:: CollisionServiceClient& collision()
   .. cpp:function:: ComponentsServiceClient& system_config()
   .. cpp:function:: StateServiceClient& system_state()
   .. cpp:function:: SystemServiceClient& system()
   .. cpp:function:: KinematicsServiceClient& kinematics()
   .. cpp:function:: SurfaceFinishServiceClient& surface_finish()
   .. cpp:function:: ConfigServiceClient& config()
   .. cpp:function:: LicenseServiceClient& license()
   .. cpp:function:: PointToPointPathServiceClient& point_to_point_path()
   .. cpp:function:: MeshOperationServiceClient& mesh_operation()
   .. cpp:function:: CameraServiceClient& camera()
   .. cpp:function:: ReconstructionServiceClient& reconstruction()

      Service accessors; thread-safe. Throw ``std::runtime_error`` after
      :cpp:func:`close`.

.. cpp:class:: LicenseServiceClient : public ServiceClient<license::LicenseService>

   Returned by :cpp:func:`Client::license`, with a helper for installing
   license files.

   .. cpp:function:: grpc::Status InstallFile(const std::string& path, license::SaveResponse* response, const std::string& file_name = "")

      Install the ``.lic`` file Flexiv sent back; takes effect immediately. The
      file is read on this machine and its contents sent, base64-encoded unless
      it already is. *file_name* defaults to the file's own name, or to the
      license id when that name is not a plain one. Check
      ``response->status()`` as with any other call. Throws
      ``std::runtime_error`` if the file cannot be read or is empty.

   .. cpp:function:: bool CheckVersion(std::string* message = nullptr)

      Ask the server whether this client works with it: same major and minor
      version. Returns false when the versions differ or the server cannot be
      reached. If *message* is not null, it is set to why not, or to the server
      version.

   .. cpp:function:: std::shared_ptr<grpc::Channel> channel() const

      The channel; use it to create your own stubs, for example with custom
      call options.
      Returns null after :cpp:func:`close`.

   .. cpp:function:: void close()

      Release the channel. Every accessor called afterwards throws. Do not use
      service client references or stubs obtained before the call.

Session
-------

``#include <flexiv/pdk/session.hpp>``

.. cpp:class:: Session

   Bundles a client and a :cpp:class:`watch::Subscriber`. Must outlive every
   component it is passed to; its destructor stops all subscriptions it created.

   .. cpp:function:: explicit Session(std::shared_ptr<Client> client)

      *client* may be null (offline mode).

   .. cpp:function:: Client* client()
   .. cpp:function:: std::shared_ptr<Client> client_ptr() const
   .. cpp:function:: watch::Subscriber& watch()

.. cpp:namespace:: flexiv::pdk::watch

Watch
-----

``#include <flexiv/pdk/watch/subscriber.hpp>``

.. cpp:class:: Subscriber

   Opens server-streaming RPCs as background subscriptions. Not copyable.

   .. cpp:function:: template <typename EventT> Subscription Subscribe(ReaderOpener<EventT> open, EventCallback<EventT> on_event, Options options = {})

      *open* is ``std::function<std::unique_ptr<grpc::ClientReaderInterface<EventT>>(grpc::ClientContext*)>``
      and is called again on every reconnect. *on_event* is
      ``std::function<void(const EventT&)>``.

   .. cpp:function:: void StopAll()

.. cpp:class:: Subscription

   Move-only handle. The watch runs while the handle is alive; discarding it
   ends the watch.

   .. cpp:function:: void reset()

      Cancel the stream and block until delivery has stopped.

   .. cpp:function:: bool active() const noexcept
   .. cpp:function:: explicit operator bool() const noexcept

      True while the watch runs. False once it is stopped, or once it gives up
      because ``reconnect`` is off or ``max_retries`` is used up.

.. cpp:struct:: Options

   .. cpp:member:: std::shared_ptr<Executor> executor
   .. cpp:member:: bool reconnect = true
   .. cpp:member:: std::chrono::milliseconds backoff_initial = 500ms
   .. cpp:member:: std::chrono::milliseconds backoff_max = 10000ms
   .. cpp:member:: double backoff_factor = 2.0
   .. cpp:member:: int max_retries = -1

.. cpp:class:: Executor

   Decides which thread runs callbacks. Implement it to forward to a UI
   thread.

   .. cpp:function:: virtual void Post(std::function<void()> fn) = 0

.. cpp:class:: InlineExecutor : public Executor

   Runs callbacks immediately on the watch thread.

.. cpp:namespace:: flexiv::pdk::spatial

Eigen conversions
-----------------

``#include <flexiv/pdk/spatial/eigen_conversion.hpp>``

.. cpp:function:: Eigen::Vector3d ToEigen(const Vector3& v)
.. cpp:function:: Vector3 ToProto(const Eigen::Vector3d& v)
.. cpp:function:: Eigen::Quaterniond ToEigen(const Quaternion& q)
.. cpp:function:: Quaternion ToProto(const Eigen::Quaterniond& q)
.. cpp:function:: Eigen::Isometry3d ToEigen(const SE3Pose& p)
.. cpp:function:: SE3Pose ToProto(const Eigen::Isometry3d& p)
.. cpp:function:: Eigen::VectorXd ToEigen(const google::protobuf::RepeatedField<double>& v)
.. cpp:function:: google::protobuf::RepeatedField<double> ToProto(const Eigen::VectorXd& v)
.. cpp:function:: std::pair<Eigen::VectorXd, Eigen::VectorXd> ToEigen(const JointWaypoint& waypoint)

   Returns ``(position, velocity)``.

.. cpp:function:: JointWaypoint ToProto(const Eigen::VectorXd& joint_position, const Eigen::VectorXd& joint_velocity)

.. cpp:function:: template <typename Derived> Vector3 ToProto(const Eigen::MatrixBase<Derived>& v)

   For a fixed-size 3-vector expression, such as
   ``Isometry3d::translation()``.

.. cpp:function:: template <typename Derived> google::protobuf::RepeatedField<double> ToProto(const Eigen::MatrixBase<Derived>& v)

   For a dynamic-size column-vector expression, such as ``VectorXd::head()``.

An all-zero (unset) ``Quaternion`` converts to the identity rotation.

.. cpp:namespace:: flexiv::pdk::physics

``#include <flexiv/pdk/physics/eigen_conversion.hpp>``

.. cpp:function:: Eigen::Matrix3d ToEigen(const Inertia& I)
.. cpp:function:: Inertia ToProto(const Eigen::Matrix3d& I)

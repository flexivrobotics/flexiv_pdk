Build Your First Scene
======================

This page builds a minimal scene: it connects to the server, creates and loads
a workcell, adds a box, and reads it back. It assumes a server is running on
``localhost:50052`` and the SDK is installed (:doc:`install_for_python` or
:doc:`install_for_cpp`).

Step 1: Connect
---------------


Python:

.. code-block:: python

   from flexiv.pdk import Client

   with Client("localhost:50052") as client:
       ...  # every service is an attribute: client.workcell, client.config, ...

C++:

.. code-block:: cpp

   #include <flexiv/pdk/client.hpp>

   flexiv::pdk::Client client("localhost:50052");
   // every service is an accessor: client.workcell(), client.config(), ...

Creating the client does not contact the server; the first RPC does.

Step 2: Create and load a workcell
----------------------------------

All scene data lives in a **workcell**, and almost every scene call requires an
*active* workcell. Create one and load it:


Python:

.. code-block:: python

   from flexiv.pdk.workcell.workcell_service_pb2 import CreateRequest, NameRequest

   client.workcell.stub.Create(CreateRequest(name="quickstart", description="My first workcell"))
   res = client.workcell.stub.Load(NameRequest(name="quickstart"))
   if res.status.code != 0:
       raise RuntimeError(res.status.message)

C++:

.. code-block:: cpp

   #include <flexiv/pdk/workcell/workcell_service.grpc.pb.h>

   using namespace flexiv::pdk::workcell;

   {
     grpc::ClientContext ctx;
     CreateRequest req;
     req.set_name("quickstart");
     req.set_description("My first workcell");
     CreateResponse res;
     client.workcell().stub->Create(&ctx, req, &res);
   }
   {
     grpc::ClientContext ctx;  // one ClientContext per call
     NameRequest req;
     req.set_name("quickstart");
     WorkcellResponse res;
     grpc::Status s = client.workcell().stub->Load(&ctx, req, &res);
     if (!s.ok() || res.status().code() != flexiv::pdk::common::Status::OK) {
       // handle error
     }
   }

Step 3: Add an object
---------------------

Scene items are saved through ``ConfigService.Save``. Every item has a
``ConfigHeader`` with a unique ``name``, a ``parent`` frame and a
``pose_in_parent``. Here is a 10 cm box 0.5 m in front of the world origin:


Python:

.. code-block:: python

   from flexiv.pdk.config_header_pb2 import ConfigHeader
   from flexiv.pdk.config_service_pb2 import SaveConfigRequest
   from flexiv.pdk.scene.object_pb2 import Object
   from flexiv.pdk.spatial.geometry_pb2 import Quaternion, SE3Pose, Vector3
   from flexiv.pdk.spatial.shape_pb2 import Box, Collision, Shape, Visual

   identity = SE3Pose(position=Vector3(), rotation=Quaternion(w=1.0))
   box = Shape(box=Box(size=[0.1, 0.1, 0.1]))

   obj = Object(
       header=ConfigHeader(
           name="box_1",
           parent="world",
           pose_in_parent=SE3Pose(position=Vector3(x=0.5), rotation=Quaternion(w=1.0)),
       ),
       visual=[Visual(origin=identity, shape=box)],
       collision=[Collision(origin=identity, shape=box)],
   )
   res = client.config.stub.Save(SaveConfigRequest(object=obj))
   if res.status.code != 0:
       raise RuntimeError(res.status.message)

C++:

.. code-block:: cpp

   #include <flexiv/pdk/config_service.grpc.pb.h>
   #include <flexiv/pdk/spatial/eigen_conversion.hpp>

   flexiv::pdk::SaveConfigRequest req;
   auto* obj = req.mutable_object();
   auto* header = obj->mutable_header();
   header->set_name("box_1");
   header->set_parent("world");
   *header->mutable_pose_in_parent() = flexiv::pdk::spatial::ToProto(
       Eigen::Isometry3d(Eigen::Translation3d(0.5, 0.0, 0.0)));

   auto* visual = obj->add_visual();
   *visual->mutable_origin() = flexiv::pdk::spatial::ToProto(Eigen::Isometry3d::Identity());
   for (double s : {0.1, 0.1, 0.1}) visual->mutable_shape()->mutable_box()->add_size(s);
   auto* collision = obj->add_collision();
   *collision->mutable_origin() = visual->origin();
   *collision->mutable_shape() = visual->shape();

   grpc::ClientContext ctx;
   flexiv::pdk::SaveConfigResponse res;
   grpc::Status s = client.config().stub->Save(&ctx, req, &res);

Step 4: Read it back
--------------------

Python:

.. code-block:: python

   from flexiv.pdk.config_service_pb2 import ConfigType, ListConfigRequest, TypeNameConfigRequest

   names = client.config.stub.List(ListConfigRequest(type=ConfigType.CONFIG_TYPE_OBJECT)).names
   print("Objects:", list(names))

   res = client.config.stub.Get(TypeNameConfigRequest(type=ConfigType.CONFIG_TYPE_OBJECT, name="box_1"))
   print(res.object.header)

C++:

.. code-block:: cpp

   #include <iostream>

   {
     grpc::ClientContext ctx;
     flexiv::pdk::ListConfigRequest req;
     req.set_type(flexiv::pdk::CONFIG_TYPE_OBJECT);
     flexiv::pdk::ListConfigResponse res;
     client.config().stub->List(&ctx, req, &res);
     for (const auto& name : res.names()) std::cout << name << std::endl;
   }
   {
     grpc::ClientContext ctx;
     flexiv::pdk::TypeNameConfigRequest req;
     req.set_type(flexiv::pdk::CONFIG_TYPE_OBJECT);
     req.set_name("box_1");
     flexiv::pdk::GetConfigResponse res;
     client.config().stub->Get(&ctx, req, &res);
     std::cout << res.object().header().DebugString();
   }

Or from a terminal, using the CLI:

.. code-block:: bash

   pdk-scene workcell list
   pdk-scene object list
   pdk-scene object get box_1

Next steps
----------

* Read :doc:`/error_handling` before writing real code: most failures
  are reported in ``response.status``, not raised.
* Add robots in :doc:`/scene_setup`.
* Browse :doc:`/verify_with_example_programs` for complete, runnable programs.

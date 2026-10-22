Cameras and 3D Reconstruction
=============================

Cameras
-------

``CameraService`` (``client.camera`` in Python) talks to a physical camera that
is linked to a ``Camera`` config in the scene (:doc:`scene_setup`) by its
``camera_id``. Data is saved **on the server**; the RPCs return status and file
names, not pixels.

.. list-table::
   :header-rows: 1
   :widths: 36 64

   * - RPC
     - Description
   * - ``IsCameraOnline``
     - ``online`` is true if the camera responds.
   * - ``UpdateCameraIntrinsicFromDevice``
     - Read ``fx``, ``fy``, ``cx``, ``cy`` and ``distortion_coeffs`` from the
       device and store them.
   * - ``GetCameraRGBDImage``
     - Capture an RGB-D image; saved as ``save_file_name`` if not empty.
   * - ``GetCameraPointCloud``
     - Capture a point cloud in the camera frame, or in the world frame with
       ``in_world_frame=True``; saved as ``save_file_name`` if not empty.
   * - ``ListSavedCameraImages`` / ``ListSavedCameraPointClouds``
     - File names saved for a camera.
   * - ``DeleteSavedCameraImage`` / ``DeleteSavedCameraPointCloud``
     - Delete a saved file. Return a bare ``common.Status``.

All requests identify the camera by ``camera_name`` (the scene config name).

The example ``examples/python/camera_example.py`` needs a Flexiv robot with RDK
remote mode enabled and a camera with ID 9 enabled in the AI console. Edit the
serial number and camera ID for your setup.

.. literalinclude:: /../../examples/python/camera_example.py
   :language: python
   :start-after: # 5. Check whether the camera is online
   :end-before: # 9. List saved images and point clouds for the camera
   :dedent: 8

3D reconstruction
-----------------

``ReconstructionService`` (``client.reconstruction``) fuses depth data from one
or more cameras into a point cloud or mesh and can add the result to the scene
as an object.

Workflow:

1. Save a ``ReconstructionConfig`` (``name``, ``point_cloud_size``,
   ``voxel_size`` in m, ``voxel_bucket_count``) with
   ``AddReconstructionConfig``.
2. ``StartReconstruction(result_format, publish_frequency,
   reconstruction_config_name)``. ``result_format`` is, for example,
   ``"mesh"``. ``reconstruction_config_name`` is optional: leave it empty to
   use the server's default parameters, so step 1 is optional too.
3. ``AddCameraToReconstruction(camera_names=[...])``.
4. Call ``GetReconstructionResult(header, add_to_scene, replace_existing_object)``
   as often as you need. With ``add_to_scene=True`` the result becomes a scene
   object named by ``header``; ``replace_existing_object`` replaces the previous
   result instead of appending to it.
5. ``RemoveCameraFromReconstruction``, ``StopReconstruction``, and optionally
   ``RemoveReconstructionConfig``. It takes a whole ``ReconstructionConfig``,
   but only ``name`` is used.

``ListReconstructionObjects`` lists results (name and format).
``GetReconstructionConfig`` and ``ListReconstructionConfigs`` query saved
configurations.

.. note::

   Most ``ReconstructionService`` RPCs return a bare ``common.Status``. Check
   ``.code`` on the returned message directly.

The examples print ``grpc.RpcError`` instead of raising it. Production code
should check both layers; see :doc:`error_handling`.

.. literalinclude:: /../../examples/python/reconstruction_example.py
   :language: python
   :start-after: # 6. Add a reconstruction config
   :end-before: if __name__ == "__main__":
   :dedent: 8

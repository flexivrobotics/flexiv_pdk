Mesh Operations
===============

``MeshOperationService`` (``client.mesh_operation``) processes the mesh of a
scene object and saves the result as **new objects**. Use it to clean up
scanned meshes or to cut out the region to work on before generating a tool
path.

.. note:: ``MeshOperationService`` requires the ``mesh_operation`` license
   (:doc:`/activate_licenses`).

Both RPCs take the source ``object_name``. If the object has more than one
visual mesh, set ``mesh_filename`` to choose one.

Extracting an area
------------------

``ExtractArea(AreaExtractionRequest)`` cuts out the part of the mesh inside a
polygon and saves it as ``extracted_object_name``. The ``boundary`` points must
lie on the mesh surface (within 1 mm). They are in the coordinates of the mesh
file, scaled by ``Mesh.scale``; the object pose and the visual ``origin`` are
not applied. The source mesh must be ``.stl`` or ``.obj``.

.. literalinclude:: /../../examples/python/mesh_area_extraction_example.py
   :language: python
   :start-at: area_extraction_request = AreaExtractionRequest(
   :end-before: except grpc.RpcError
   :dedent: 8

Filtering a mesh
----------------

``FilterMesh(FilterMeshRequest)`` applies **one** filter and saves the result.
If the filter produces one mesh, it is named ``filtered_object_name_prefix``;
if it produces several, they share that prefix. ``filtered_object_names`` lists
them.

.. literalinclude:: /../../examples/python/mesh_filter_example.py
   :language: python
   :start-at: filter_mesh_request = FilterMeshRequest(
   :end-before: except grpc.RpcError
   :dedent: 8

Available filters
~~~~~~~~~~~~~~~~~

Set exactly one of these ``FilterMeshRequest`` fields. Mesh filters are in
``flexiv.pdk.mesh_operation.filter.parameters_pb2``; area filters in
``flexiv.pdk.mesh_operation.area_filter.parameters_pb2``.

.. list-table::
   :header-rows: 1
   :widths: 24 30 46

   * - Field
     - Parameters
     - Use
   * - ``smooth_mesh``
     - ``pass_band`` (0.01–0.1 typical; smaller is smoother), ``num_iterations``
       (10–100 typical)
     - Smooth a noisy, e.g. reconstructed, mesh.
   * - ``largest_region``
     - none
     - Keep the largest connected region; remove speckles.
   * - ``bounding_box``
     - ``bbox_center``, ``bbox_orientation``, ``bbox_size`` (world frame)
     - Keep the mesh inside a region of interest.
   * - ``fill_holes``
     - ``hole_size`` (m)
     - Patch holes smaller than this diameter.
   * - ``sharpen``
     - ``num_iterations``, ``strength``
     - Sharpen edge features.
   * - ``minimum_surface_area``
     - ``minimum_surface_area`` (m²)
     - Remove connected regions smaller than this.
   * - ``uniform_resampling``
     - ``num_points_per_unit_area`` (per m²)
     - Upsample, usually a coarse CAD mesh.
   * - ``bump_valley_removal``
     - ``tool_disk_radius`` (m), area factors, angle thresholds (rad)
     - Remove high-curvature regions a disk tool cannot follow.
   * - ``border_offset``
     - ``offset`` (m, inward), ``minimum_component_area_after_border_offset``
       (m²), ``flag_fallback_to_original_if_empty`` (keep the original if the
       result would be empty)
     - Shrink the region along its border.
   * - ``reachability_removal``
     - ``system_name``, ``tool_name``, ``reachability_threshold`` (0–0.95),
       ``minimum_component_area_after_reachability_removal`` (m²)
     - Keep only regions the robot can reach (IK-based).
   * - ``region_division``
     - ``rect_length``, ``rect_width`` (m), ``minimum_area_after_division``
     - Split the region into rectangles, producing several objects.

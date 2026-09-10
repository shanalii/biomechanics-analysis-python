"""Blender mesh access, isolated so the rest of the library is bpy-free.

This is the only module (besides visualizer.py) that touches bpy/bmesh.
"""

from dataclasses import dataclass

import bpy  # type: ignore  # pylint: disable=wrong-import-position
import bmesh  # type: ignore  # pylint: disable=wrong-import-position


@dataclass(frozen=True)
class MeshData:
    """Plain-Python snapshot of a Blender mesh's verts/edges.

    node_coords[i] and edge_indices are aligned by index with
    biomechanics.body_data.BODY_NODES / BODY_MEMBERS respectively - this
    ordering is assumed, not validated. See TODO2 in body_data.py for
    planned follow-up work to validate/derive this mapping instead of
    relying on Blender's vertex/edge creation order.
    """

    node_coords: list  # list[tuple[float, float, float]]
    edge_indices: list  # list[tuple[int, int]] - (i_vert_index, j_vert_index)


class BlenderMeshReader:
    """Reads the active Blender mesh into plain-Python MeshData."""

    def __init__(self, blender_object=None):
        self._blender_object = blender_object or bpy.context.object

    def read(self) -> MeshData:
        me = self._blender_object.data

        bm = bmesh.new()
        bm.from_mesh(me)
        try:
            node_coords = [(v.co.x, v.co.y, v.co.z) for v in bm.verts]
            edge_indices = [(e.verts[0].index, e.verts[1].index) for e in bm.edges]
        finally:
            bm.free()

        return MeshData(node_coords=node_coords, edge_indices=edge_indices)

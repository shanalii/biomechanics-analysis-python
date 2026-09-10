"""Draws visual markers in the Blender viewport.

This is the only module (besides mesh_reader.py) that touches bpy.
"""

from typing import Iterable

import bpy  # type: ignore  # pylint: disable=wrong-import-position


class ComVisualizer:
    """Draws small cones in Blender to mark member center-of-mass points."""

    def __init__(self, cone_vertices: int = 8, cone_radius: float = 0.03, cone_depth: float = 0.05):
        self._cone_vertices = cone_vertices
        self._cone_radius = cone_radius
        self._cone_depth = cone_depth

    def draw_com_marker(self, x: float, y: float, z: float) -> None:
        # Depends on the model position being at (0,0,0)
        bpy.ops.mesh.primitive_cone_add(
            vertices=self._cone_vertices,
            radius1=0,
            radius2=self._cone_radius,
            depth=self._cone_depth,
            enter_editmode=False,
            align="WORLD",
            location=(x, y, z),
        )

    def draw_com_markers(self, points: Iterable[tuple[float, float, float]]) -> None:
        for x, y, z in points:
            self.draw_com_marker(x, y, z)

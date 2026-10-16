"""Builds a Pynite FEModel3D from mesh geometry + anatomical body config."""

from Pynite import FEModel3D  # pylint: disable=wrong-import-position

from biomechanics.body_data import BodyMember, BodyNode
from biomechanics.body_graph import BodyGraph
from biomechanics.mesh_reader import MeshData

# Section properties pulled directly from SkyCiv's "Default Section" (Section ID 1),
# which is what the SkyCiv model actually solves with (all members use this section).
# Source values in mm^2 / mm^4, converted to m^2 / m^4.
STEEL_SECTION = dict(
    A=0.0016805189677511114,
    Iy=2.3534533341427174e-7,
    Iz=2.3534533341427174e-7,
    J=3.9714525013658364e-7,
)

# Material ref: https://github.com/JWock82/Pynite/blob/main/Pynite/Material.py
# Approximate values for steel beams:
# E = 200000 MPa (SkyCiv) (1Pa = 1N/m^2)
# G derived the way structural software typically does: G = E / (2*(1+nu)),
# rather than an independently-specified value.
# nu = 0.27 (SkyCiv)
# rho = 7850 kg/m^3 (SkyCiv)
STEEL_MATERIAL = dict(E=200000, G=200000 / (2 * (1 + 0.27)), nu=0.27, rho=7850)


class ModelBuilder:
    """Builds a Pynite FEModel3D representing a stick figure and its loads.

    Joint/limb identity and direction (i_node/j_node) both come from
    `body_graph` (a biomechanics.body_graph.BodyGraph), produced by
    BodyGraphResolver from mesh topology + geometry alone - not from
    Blender's vertex/edge creation order, and not stored in body_data.py.
    """

    def __init__(
        self,
        mesh_data: MeshData,
        body_graph: BodyGraph,
        nodes: list[BodyNode],
        members: list[BodyMember],
        body_mass_kg: float,
        g: float,
    ):
        self._mesh_data = mesh_data
        self._names_by_index = body_graph.names_by_index
        self._member_names_by_edge = body_graph.member_names_by_edge
        self._direction_by_edge = body_graph.direction_by_edge
        self._nodes_by_name = {node.name: node for node in nodes}
        self._members_by_name = {member.name: member for member in members}
        self._body_mass_kg = body_mass_kg
        self._g = g

    def build(self) -> FEModel3D:
        """Constructs and returns the Pynite FEModel3D: section, material, nodes,
        members, point loads, and load combo."""
        model = FEModel3D()
        model.add_section("S", **STEEL_SECTION)
        model.add_material("Steel", **STEEL_MATERIAL)

        self._add_nodes(model)
        self._add_members(model)

        # Consolidate point loads into a load combo, to be referenced in results
        model.add_load_combo("Combo", {"Point": 1.0})

        return model

    def _add_nodes(self, model: FEModel3D) -> None:
        # Add nodes to model with anatomical names
        for vertex_index, coords in enumerate(self._mesh_data.node_coords):
            name = self._names_by_index.get(vertex_index)
            if name is None:
                raise ValueError(f"Mesh vertex {vertex_index} could not be classified")
            body_node = self._nodes_by_name.get(name)
            if body_node is None:
                raise ValueError(
                    f"Mesh has joint '{name}' with no matching BodyNode in body_data.py"
                )

            x, y, z = coords
            model.add_node(name, x, y, z)

            # Add support for nodes that make contact
            # Pinned supports - only release rotation about the model's Y axis.
            # SkyCiv's restraint code (FFFFFR) releases rotation about SkyCiv's Z axis,
            # which corresponds to this model's Y axis (SkyCiv is Y-up, this model is
            # Z-up: SkyCiv Y <-> our Z, SkyCiv Z <-> our Y).
            if body_node.is_supported:
                model.def_support(
                    name,
                    support_DX=True,
                    support_DY=True,
                    support_DZ=True,
                    support_RX=True,
                    support_RY=False,
                    support_RZ=True,
                )

    def _add_members(self, model: FEModel3D) -> None:
        # Add members to model with anatomical names
        for i, j in self._mesh_data.edge_indices:
            edge = frozenset((i, j))
            member_name = self._member_names_by_edge.get(edge)
            if member_name is None:
                raise ValueError(f"Mesh edge {edge} could not be classified as a member")
            body_member = self._members_by_name.get(member_name)
            if body_member is None:
                raise ValueError(
                    f"Mesh has member '{member_name}' with no matching BodyMember "
                    "in body_data.py"
                )

            i_index, j_index = self._direction_by_edge[edge]
            i_node_name = self._names_by_index[i_index]
            j_node_name = self._names_by_index[j_index]

            model.add_member(body_member.name, i_node_name, j_node_name, "Steel", "S")

            # Add point load at CM based on CM percent; calculate length along the member
            # https://pynite.readthedocs.io/en/latest/member.html#local-coordinate-system
            # Each member starts at its i-node and ends at its j-node.
            # The local x-axis for the member is defined by a vector going from the
            # i-node to the j-node. i_node is proximal (limbs) or physically higher
            # (centerline) - see biomechanics.body_graph.

            # UNIT NOTE: we will calculate the weight (Newtons) by multiplying input mass by g
            # (9.81m/s^2). This is for the calculations to scientifically make sense, though we
            # ultimately need the weight on supported nodes in kg - this is dealt with in
            # post-processing.
            if body_member.mass_percent > 0:
                limb_weight = self._body_mass_kg * self._g * body_member.mass_percent / 100  # N
                member = model.members[body_member.name]
                cm_length = member.L() * body_member.cm_percent / 100  # Meters
                model.add_member_pt_load(
                    body_member.name, "FZ", -1 * limb_weight, cm_length, case="Point"
                    # Weight should be globally downwards in direction
                )

    @staticmethod
    def member_com_point(member, cm_percent: float) -> tuple[float, float, float]:
        """Global (x, y, z) of a member's center of mass, lerped from its end nodes.

        Pure geometry over a Pynite Member3D's end nodes - no Blender dependency.
        Used both implicitly (via cm_length above, for the point load) and explicitly
        by callers that want the 3D coordinate (e.g. visualization).
        """
        start_node = member.i_node
        end_node = member.j_node
        t = cm_percent / 100
        x = start_node.X + t * (end_node.X - start_node.X)
        y = start_node.Y + t * (end_node.Y - start_node.Y)
        z = start_node.Z + t * (end_node.Z - start_node.Z)
        return x, y, z

"""Builds a Pynite FEModel3D from mesh geometry + anatomical body config."""

from Pynite import FEModel3D  # pylint: disable=wrong-import-position

from biomechanics.body_data import BodyMember, BodyNode
from biomechanics.mesh_reader import MeshData

# Section based on steel material characteristics
# A: cross-sectional area (pi*r^2)
#   (SkyCiv: 1681 mm^2 = 0.001681 m^2)
# Iy: second moment of area (m. o. inertia) about the weak axis (pi*r^4/4)
#   (SkyCiv: 235345 mm^4 = 2e-7 m^4)
# Iz: second moment of area (m. o. inertia) about the strong axis (pi*r^4/4)
#   (SkyCiv: 235345 mm^4 = 2e-7 m^4)
# J: torsion constant (pi*r^4/2); calculated assuming circular cross-section
#   First calculate radius of circle with given A (r = 0.02313 m)
#   (https://www.omnicalculator.com/physics/torsional-constant: 4.496e-7 m^4)
# (Source: https://skyciv.com/free-moment-of-inertia-calculator/,
# http://www.hyperphysics.phy-astr.gsu.edu/hbase/icyl.html)
STEEL_SECTION = dict(A=0.001681, Iy=2.353e-7, Iz=2.353e-7, J=4.496e-7)

# Material ref: https://github.com/JWock82/Pynite/blob/main/Pynite/Material.py
# Approximate values for steel beams:
# E = 200000 MPa (SkyCiv) (1Pa = 1N/m^2)
# G = 79300 MPa (https://www.engineeringtoolbox.com/modulus-rigidity-d_946.html)
#  Optional in SkyCiv but required in PyNite
# nu = 0.27 (SkyCiv)
# rho = 7850 kg/m^3 (SkyCiv)
STEEL_MATERIAL = dict(E=200000, G=29000, nu=0.27, rho=7850)


class ModelBuilder:
    """Builds a Pynite FEModel3D representing a stick figure and its loads.

    Joint/limb identity comes from `names_by_index` (mesh vertex index ->
    anatomical name), typically produced by
    biomechanics.body_graph.BodyGraphResolver from mesh topology + geometry
    alone - not from Blender's vertex/edge creation order.
    """

    def __init__(
        self,
        mesh_data: MeshData,
        names_by_index: dict,
        nodes: list[BodyNode],
        members: list[BodyMember],
        body_mass_kg: float,
        g: float,
    ):
        self._mesh_data = mesh_data
        self._names_by_index = names_by_index
        self._nodes_by_name = {node.name: node for node in nodes}
        self._members_by_connection = {
            frozenset((member.i_node, member.j_node)): member for member in members
        }
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
            # Pinned supports - only release rotationally in local Z axis
            if body_node.is_supported:
                model.def_support(
                    name,
                    support_DX=True,
                    support_DY=True,
                    support_DZ=True,
                    support_RX=True,
                    support_RY=True,
                    support_RZ=False,
                )

    def _add_members(self, model: FEModel3D) -> None:
        # Add members to model with anatomical names
        for i, j in self._mesh_data.edge_indices:
            name_i = self._names_by_index.get(i)
            name_j = self._names_by_index.get(j)
            body_member = self._members_by_connection.get(frozenset((name_i, name_j)))
            if body_member is None:
                raise ValueError(
                    f"Mesh has an edge between '{name_i}' and '{name_j}' with no "
                    "matching BodyMember in body_data.py"
                )

            # Use BodyMember's own i_node/j_node direction (not the mesh edge's
            # arbitrary vertex order) - cm_percent is measured from i_node.
            model.add_member(
                body_member.name, body_member.i_node, body_member.j_node, "Steel", "S"
            )

            # Option to add releases:
            # https://github.com/JWock82/Pynite/blob/25897a43a4a25f41b3c5709817974169ffff0f4f/
            # Pynite/Member3D.py#L103
            # Equivalent to SkyCiv node fixicity (currently set to all fixed, which is
            # Pynite default)

            # Add point load at CM based on CM percent; calculate length along the member
            # https://pynite.readthedocs.io/en/latest/member.html#local-coordinate-system
            # Each member starts at its i-node and ends at its j-node.
            # The local x-axis for the member is defined by a vector going from the
            # i-node to the j-node.

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

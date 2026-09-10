"""Anatomical configuration for the stick-figure biomechanics model.

Model for: 2026.07.16_Basic Stick Figure Posed.blend

This is the single source of truth for THIS analysis: which joints are
supported, which joints each limb connects, and the mass-distribution data
used to compute point loads. Joint/limb identity is resolved against the
Blender mesh by name, via biomechanics.body_graph.BodyGraphResolver, which
infers names purely from mesh topology and geometry - independent of this
file and of Blender's vertex/edge creation order.
"""

from dataclasses import dataclass

# Input: total body mass (kg)
BODY_MASS_KG = 100
G = 9.81  # m/s^2


@dataclass(frozen=True)
class BodyNode:
    """A body joint, identified by name (see body_graph.BodyGraphResolver)."""

    name: str
    is_supported: bool


@dataclass(frozen=True)
class BodyMember:
    """A body segment (limb) connecting two named joints.

    i_node/j_node: the joint names this member connects. Matches Pynite's
        i-node/j-node convention - the member's local x-axis runs from
        i_node to j_node, and cm_percent is measured from i_node.
        https://pynite.readthedocs.io/en/latest/member.html#local-coordinate-system
    mass_percent: percent of total body mass carried by this segment.
    cm_percent: percent of segment length (from i_node) at which the
        segment's center of mass sits.
        https://en.wikipedia.org/wiki/Anatomical_terms_of_location#Proximal_and_distal
    """

    name: str
    i_node: str
    j_node: str
    mass_percent: float
    cm_percent: float


# Input nodes representing each body joint/connection
BODY_NODES = [
    BodyNode("l_shoulder", is_supported=False),
    BodyNode("l_elbow", is_supported=False),
    BodyNode("l_wrist", is_supported=True),
    BodyNode("l_finger", is_supported=False),
    BodyNode("r_shoulder", is_supported=False),
    BodyNode("r_elbow", is_supported=True),
    BodyNode("r_wrist", is_supported=False),
    BodyNode("r_finger", is_supported=False),
    BodyNode("neck_base", is_supported=False),
    BodyNode("head_base", is_supported=False),
    BodyNode("head_top", is_supported=False),
    BodyNode("spine_base", is_supported=False),
    BodyNode("r_hip", is_supported=False),
    BodyNode("l_hip", is_supported=False),
    BodyNode("l_knee", is_supported=True),
    BodyNode("l_heel", is_supported=False),
    BodyNode("l_toe", is_supported=False),
    BodyNode("r_knee", is_supported=True),
    BodyNode("r_heel", is_supported=False),
    BodyNode("r_toe", is_supported=False),
]

# Members connecting bodily nodes
# Flipped cm_percent values (100 - cm_percent) for members whose i_node/j_node
# run in the reversed direction (see "Flip" comments)
BODY_MEMBERS = [
    BodyMember("l_upperarm", i_node="l_shoulder", j_node="l_elbow", mass_percent=2.71, cm_percent=57.72),
    BodyMember("l_forearm", i_node="l_elbow", j_node="l_wrist", mass_percent=1.62, cm_percent=45.74),
    BodyMember("l_back", i_node="neck_base", j_node="l_shoulder", mass_percent=0, cm_percent=0),
    BodyMember("r_upperarm", i_node="r_elbow", j_node="r_shoulder", mass_percent=2.71, cm_percent=42.28),  # Flip
    BodyMember("r_forearm", i_node="r_wrist", j_node="r_elbow", mass_percent=1.62, cm_percent=54.26),  # Flip
    BodyMember("r_hand", i_node="r_wrist", j_node="r_finger", mass_percent=0.61, cm_percent=79.00),
    BodyMember("r_back", i_node="r_shoulder", j_node="neck_base", mass_percent=0, cm_percent=0),
    BodyMember("neck", i_node="neck_base", j_node="head_base", mass_percent=0, cm_percent=0),
    BodyMember("head", i_node="head_base", j_node="head_top", mass_percent=6.94, cm_percent=59.76),
    BodyMember("spine", i_node="neck_base", j_node="spine_base", mass_percent=43.46, cm_percent=55.14),  # Flip
    BodyMember("r_pelvis", i_node="r_hip", j_node="spine_base", mass_percent=0, cm_percent=0),
    BodyMember("l_pelvis", i_node="spine_base", j_node="l_hip", mass_percent=0, cm_percent=0),
    BodyMember("l_thigh", i_node="l_hip", j_node="l_knee", mass_percent=14.16, cm_percent=40.95),
    BodyMember("l_calf", i_node="l_knee", j_node="l_heel", mass_percent=4.33, cm_percent=44.59),
    BodyMember("l_foot", i_node="l_heel", j_node="l_toe", mass_percent=1.37, cm_percent=44.15),
    BodyMember("r_thigh", i_node="r_knee", j_node="r_hip", mass_percent=14.16, cm_percent=59.05),  # Flip
    BodyMember("r_calf", i_node="r_heel", j_node="r_knee", mass_percent=4.33, cm_percent=55.41),  # Flip
    BodyMember("r_foot", i_node="r_toe", j_node="r_heel", mass_percent=1.37, cm_percent=55.85),  # Flip
    BodyMember("l_hand", i_node="l_wrist", j_node="l_finger", mass_percent=0.61, cm_percent=79.00),
]

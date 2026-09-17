"""Anatomical configuration for the stick-figure biomechanics model.

Model for: 2026.07.16_Basic Stick Figure Posed.blend

This is the single source of truth for the specific stick figure being
analyzed: which mesh vertices are joints/supports, which edges are limb
segments, and the mass-distribution data used to compute point loads.
"""

from dataclasses import dataclass

# Input: total body mass (kg)
BODY_MASS_KG = 100
G = 9.81  # m/s^2


@dataclass(frozen=True)
class BodyNode:
    """A body joint/connection, mapped 1:1 by index to a Blender mesh vertex."""

    name: str
    is_supported: bool


@dataclass(frozen=True)
class BodyMember:
    """A body segment (limb), mapped 1:1 by index to a Blender mesh edge.

    mass_percent: percent of total body mass carried by this segment.
    cm_percent: percent of segment length (from the "proximal end") at
        which the segment's center of mass sits.
        https://en.wikipedia.org/wiki/Anatomical_terms_of_location#Proximal_and_distal
    """

    name: str
    mass_percent: float
    cm_percent: float


# TODO2: global ordering of nodes/members to set loads; for now, hard-code based on order created
# Coordinate-based (eg. by height or left/right) has many edge cases based on figure position
# Construct graph data structure, identify limbs based on leaves/nodes with 1 member
# Head is limb (leaf node in graph) as well - we can identify arms vs legs
# based on coordinates down the spine from head
# Symmetry across spine: doesn't really matter R/L, but we can assume R/L
# arms/legs are on either side

# Input nodes representing each body joint/connection
# Order is specific to this model - manually listed from Blender coordinates
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
# Flipped values (100 - cm_percent) for members with reversed x-axis
# Ordering of member nodes determined by order of creation
# However, cm_percent was calculated from the "proximal end"
BODY_MEMBERS = [
    BodyMember("l_upperarm", mass_percent=3.25443787, cm_percent=43.6),
    BodyMember("l_forearm", mass_percent=1.87058599, cm_percent=43),
    BodyMember("l_back", mass_percent=0, cm_percent=0),
    BodyMember("r_upperarm", mass_percent=3.25443787, cm_percent=56.4),  # Flip
    BodyMember("r_forearm", mass_percent=1.87058599, cm_percent=57),  # Flip
    BodyMember("r_hand", mass_percent=0.6489788128, cm_percent=46.8),
    BodyMember("r_back", mass_percent=0, cm_percent=0),
    BodyMember("neck", mass_percent=0, cm_percent=0),
    BodyMember("head", mass_percent=8.25539225, cm_percent=55),
    BodyMember("spine", mass_percent=46.83145638, cm_percent=54.04),  # Flip
    BodyMember("r_pelvis", mass_percent=0, cm_percent=0),
    BodyMember("l_pelvis", mass_percent=0, cm_percent=0),
    BodyMember("l_thigh", mass_percent=10.49818668, cm_percent=43.3),
    BodyMember("l_calf", mass_percent=4.752815423, cm_percent=43.4),
    BodyMember("l_foot", mass_percent=1.43157091, cm_percent=50),
    BodyMember("r_thigh", mass_percent=10.49818668, cm_percent=56.7),  # Flip
    BodyMember("r_calf", mass_percent=4.752815423, cm_percent=56.6),  # Flip
    BodyMember("r_foot", mass_percent=1.43157091, cm_percent=50),  # Flip
    BodyMember("l_hand", mass_percent=0.6489788128, cm_percent=46.8),
]

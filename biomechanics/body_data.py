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
    BodyMember("l_upperarm", mass_percent=2.71, cm_percent=57.72),
    BodyMember("l_forearm", mass_percent=1.62, cm_percent=45.74),
    BodyMember("l_back", mass_percent=0, cm_percent=0),
    BodyMember("r_upperarm", mass_percent=2.71, cm_percent=42.28),  # Flip
    BodyMember("r_forearm", mass_percent=1.62, cm_percent=54.26),  # Flip
    BodyMember("r_hand", mass_percent=0.61, cm_percent=79.00),
    BodyMember("r_back", mass_percent=0, cm_percent=0),
    BodyMember("neck", mass_percent=0, cm_percent=0),
    BodyMember("head", mass_percent=6.94, cm_percent=59.76),
    BodyMember("spine", mass_percent=43.46, cm_percent=55.14),  # Flip
    BodyMember("r_pelvis", mass_percent=0, cm_percent=0),
    BodyMember("l_pelvis", mass_percent=0, cm_percent=0),
    BodyMember("l_thigh", mass_percent=14.16, cm_percent=40.95),
    BodyMember("l_calf", mass_percent=4.33, cm_percent=44.59),
    BodyMember("l_foot", mass_percent=1.37, cm_percent=44.15),
    BodyMember("r_thigh", mass_percent=14.16, cm_percent=59.05),  # Flip
    BodyMember("r_calf", mass_percent=4.33, cm_percent=55.41),  # Flip
    BodyMember("r_foot", mass_percent=1.37, cm_percent=55.85),  # Flip
    BodyMember("l_hand", mass_percent=0.61, cm_percent=79.00),
]

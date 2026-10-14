"""Anatomical configuration for the stick-figure biomechanics model.

Model for: 2026.07.16_Basic Stick Figure Posed.blend

This is the single source of truth for THIS analysis: which joints are
supported, and the mass-distribution data used to compute point loads.
Everything about *identity* - which joints exist, which members connect
them, and member direction (i_node/j_node) - is resolved against the
Blender mesh via biomechanics.body_graph.BodyGraphResolver, which infers
all of it purely from mesh topology and geometry, independent of this file
and of Blender's vertex/edge creation order. This file only needs to
provide physics data (mass, support, cm_percent) keyed by the names that
module produces.

cm_percent is always "percent of the way from i_node" under that
convention - see body_graph.py for exactly what i_node means for each kind
of member.
"""

from dataclasses import dataclass

# Input: total body mass (kg)
BODY_MASS_KG = 112.7
G = 9.81  # m/s^2


@dataclass(frozen=True)
class BodyNode:
    """A body joint, identified by name (see body_graph.BodyGraphResolver)."""

    name: str
    is_supported: bool


@dataclass(frozen=True)
class BodyMember:
    """A body segment, identified by name (see body_graph.BodyGraphResolver).

    mass_percent: percent of total body mass carried by this segment.
    cm_percent: percent of segment length, measured from i_node (see
        biomechanics.body_graph for the i_node convention), at which the
        segment's center of mass sits.
        https://en.wikipedia.org/wiki/Anatomical_terms_of_location#Proximal_and_distal
    """

    name: str
    mass_percent: float
    cm_percent: float


# Input nodes representing each body joint/connection, alphabetically by name
BODY_NODES = [
    BodyNode("head_base", is_supported=False),
    BodyNode("head_top", is_supported=False),
    BodyNode("l_elbow", is_supported=False),
    BodyNode("l_finger", is_supported=False),
    BodyNode("l_heel", is_supported=False),
    BodyNode("l_hip", is_supported=False),
    BodyNode("l_knee", is_supported=True),
    BodyNode("l_shoulder", is_supported=False),
    BodyNode("l_toe", is_supported=False),
    BodyNode("l_wrist", is_supported=True),
    BodyNode("neck_base", is_supported=False),
    BodyNode("r_elbow", is_supported=True),
    BodyNode("r_finger", is_supported=False),
    BodyNode("r_heel", is_supported=False),
    BodyNode("r_hip", is_supported=False),
    BodyNode("r_knee", is_supported=True),
    BodyNode("r_shoulder", is_supported=False),
    BodyNode("r_toe", is_supported=False),
    BodyNode("r_wrist", is_supported=False),
    BodyNode("spine_base", is_supported=False),
    BodyNode("tail", is_supported=False),
]

# Body segments, alphabetically by name (identity/connectivity not stored -
# see BodyGraphResolver). cm_percent values below are placeholders pending a
# pass to express them all as "percent from i_node" under the new
# direction convention - do not trust these numbers yet.
BODY_MEMBERS = [
    BodyMember("head", mass_percent=6.94, cm_percent=59.76),
    BodyMember("l_back", mass_percent=0, cm_percent=0),
    BodyMember("l_calf", mass_percent=4.33, cm_percent=44.59),
    BodyMember("l_foot", mass_percent=1.37, cm_percent=44.15),
    BodyMember("l_forearm", mass_percent=1.62, cm_percent=45.74),
    BodyMember("l_hand", mass_percent=0.61, cm_percent=79.00),
    BodyMember("l_pelvis", mass_percent=0, cm_percent=0),
    BodyMember("l_thigh", mass_percent=14.16, cm_percent=40.95),
    BodyMember("l_upperarm", mass_percent=2.71, cm_percent=57.72),
    BodyMember("neck", mass_percent=0, cm_percent=0),
    BodyMember("r_back", mass_percent=0, cm_percent=0),
    BodyMember("r_calf", mass_percent=4.33, cm_percent=55.41),
    BodyMember("r_foot", mass_percent=1.37, cm_percent=55.85),
    BodyMember("r_forearm", mass_percent=1.62, cm_percent=54.26),
    BodyMember("r_hand", mass_percent=0.61, cm_percent=79.00),
    BodyMember("r_pelvis", mass_percent=0, cm_percent=0),
    BodyMember("r_thigh", mass_percent=14.16, cm_percent=59.05),
    BodyMember("r_upperarm", mass_percent=2.71, cm_percent=42.28),
    BodyMember("spine", mass_percent=43.46, cm_percent=55.14),
]

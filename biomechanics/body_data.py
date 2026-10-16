"""Anatomical configuration for the stick-figure biomechanics model.

TODO: instead of populating per-model parameters here, import from a txt or csv file.
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
# see BodyGraphResolver).
# Proximal -> distal for cm_percent:
# Top -> bottom for centerline members, near trunk -> further from trunk for others
# Should be consistent with given data without modifications - flag if not
# TODO: same numbers for R&L
BODY_MEMBERS = [
    BodyMember("head", mass_percent=8.25539225, cm_percent=40.24),
    BodyMember("l_back", mass_percent=0, cm_percent=0),
    BodyMember("l_calf", mass_percent=4.752815423, cm_percent=43.4),
    BodyMember("l_foot", mass_percent=1.43157091, cm_percent=50),
    BodyMember("l_forearm", mass_percent=1.87058599, cm_percent=43),
    BodyMember("l_hand", mass_percent=0.6489788128, cm_percent=46.8),
    BodyMember("l_pelvis", mass_percent=0, cm_percent=0),
    BodyMember("l_thigh", mass_percent=10.49818668, cm_percent=43.3),
    BodyMember("l_upperarm", mass_percent=3.25443787, cm_percent=43.6),
    BodyMember("neck", mass_percent=0, cm_percent=0),
    BodyMember("r_back", mass_percent=0, cm_percent=0),
    BodyMember("r_calf", mass_percent=4.752815423, cm_percent=43.4),
    BodyMember("r_foot", mass_percent=1.43157091, cm_percent=50),
    BodyMember("r_forearm", mass_percent=1.87058599, cm_percent=43),
    BodyMember("r_hand", mass_percent=0.6489788128, cm_percent=46.8),
    BodyMember("r_pelvis", mass_percent=0, cm_percent=0),
    BodyMember("r_thigh", mass_percent=10.49818668, cm_percent=43.3),
    BodyMember("r_upperarm", mass_percent=3.25443787, cm_percent=43.6),
    # Should CM for the spine be closer to neck or pelvis?
    BodyMember("spine", mass_percent=33.1742699, cm_percent=54.04),
    BodyMember("tailbone", mass_percent=13.65718649, cm_percent=5),
]

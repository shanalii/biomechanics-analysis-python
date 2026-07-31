"""Script to run linear analysis for Pynite stick figure model built from Blender mesh data."""
import logging
import os
import sys

# Make Blender use venv
sys.path.insert(0, "/Users/sl/blender-env-3-13/lib/python3.13/site-packages")
from Pynite import FEModel3D  # pylint: disable=wrong-import-position

# Ignore lint errors for imports from Blender's internal module
import bpy  # type: ignore  # pylint: disable=wrong-import-position
import bmesh  # type: ignore  # pylint: disable=wrong-import-position

# How to run:
# in terminal, ~
# source blender-env-3-13/bin/activate
# blender (opens app, select blender file)

### LOGGING SETUP ###

# Log to output.txt in the current directory
# Need to go up 1 level since current directory is the Blender file we're
# running code in
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_path = os.path.join(script_dir, "output.txt")
LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
DATE_FORMAT = "%H:%M:%S"

# Get root logger and clear existing handlers from previous runs
logger = logging.getLogger()
logger.handlers.clear()
logger.setLevel(logging.DEBUG)

# Log to file output.txt
file_handler = logging.FileHandler(log_path, mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

# Also log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(
    logging.Formatter(
        LOG_FORMAT,
        datefmt=DATE_FORMAT))

logger.addHandler(file_handler)
logger.addHandler(console_handler)


### MECHANICS SETUP ###
# Model for: 2026.07.16_Basic Stick Figure Posed.blend

# Input: total body mass (kg)
BODY_MASS_KG = 100
G = 9.81  # m/s^2

# TODO2: global ordering of nodes/members to set loads; for now, hard-code based on order created
# Coordinate-based (eg. by height or left/right) has many edge cases based on figure position
# Construct graph data structure, identify limbs based on leaves/nodes with 1 member
# Head is limb (leaf node in graph) as well - we can identify arms vs legs
# based on coordinates down the spine from head
# Symmetry across spine: doesn't really matter R/L, but we can assume R/L
# arms/legs are on either side

# Get the active mesh in Blender window
me = bpy.context.object.data

# Create a BMesh representation
bm = bmesh.new()  # create an empty BMesh
bm.from_mesh(me)  # fill it in from a Mesh

# Input nodes represending each body joint/connection
# Order is specific to this model - manually listed from Blender coordinates
# [name, is_supported]
input_nodes = [
    ["l_shoulder", False],
    ["l_elbow", False],
    ["l_wrist", True],
    ["l_finger", False],
    ["r_shoulder", False],
    ["r_elbow", True],
    ["r_wrist", False],
    ["r_finger", False],
    ["neck_base", False],
    ["head_base", False],
    ["head_top", False],
    ["spine_base", False],
    ["r_hip", False],
    ["l_hip", False],
    ["l_knee", True],
    ["l_heel", False],
    ["l_toe", False],
    ["r_knee", True],
    ["r_heel", False],
    ["r_toe", False],
]

# Members connecting bodily nodes
# [name, mass_percent, cm_percent]
# Flipped values (100 - cm_percent) for members with reversed x-axis
# Ordering of member nodes determined by order of creation
# However, cm_percent was calculated from the "proximal end"
# https://en.wikipedia.org/wiki/Anatomical_terms_of_location#Proximal_and_distal
input_members = [
    ["l_upperarm", 2.71, 57.72],
    ["l_forearm", 1.62, 45.74],
    ["l_back", 0, 0],
    ["r_upperarm", 2.71, 42.28],  # Flip
    ["r_forearm", 1.62, 54.26],  # Flip
    ["r_hand", 0.61, 79.00],
    ["r_back", 0, 0],
    ["neck", 0, 0],
    ["head", 6.94, 59.76],
    ["spine", 43.46, 55.14],  # Flip
    ["r_pelvis", 0, 0],
    ["l_pelvis", 0, 0],
    ["l_thigh", 14.16, 40.95],
    ["l_calf", 4.33, 44.59],
    ["l_foot", 1.37, 44.15],
    ["r_thigh", 14.16, 59.05],  # Flip
    ["r_calf", 4.33, 55.41],  # Flip
    ["r_foot", 1.37, 55.85],  # Flip
    ["l_hand", 0.61, 79.00],
]


### CONSTRUCT PYNITE 3D MODEL ###

# Create an FE Model (Pynite representation)
model = FEModel3D()

# ref: https://pynite.readthedocs.io/en/latest/FEModel3D.html#quick-start
# Need to add: nodes, materials, sections, members, support, node loads,
# load combos

# Section based on steel material characteristics
# A: cross-sectional area (pi*r^2)
#   (SkyCiv: 1681 mm^2 = 0.001681 m^2)
# Iy: second moment of area (m. o. inertia) about the weak axis (pi*r^4/4)
#   (SkyCiv: 235345 mm^4 = 2e-7 m^4)
# Iz: second moment of area (m. o. inertia) about the strong axis (pi*r^4/4)
#   (SkyCiv: 235345 mm^4 = 2e-7 m^4)
# J: torsion constant (pi*r^4/2); calculated assuming circlar cross-section
#   First calculate radius of circle with given A (r = 0.02313 m)
#   (https://www.omnicalculator.com/physics/torsional-constant: 4.496e-7 m^4)
# (Source: https://skyciv.com/free-moment-of-inertia-calculator/,
# http://www.hyperphysics.phy-astr.gsu.edu/hbase/icyl.html)
model.add_section("S", A=0.001681, Iy=2.353e-7, Iz=2.353e-7, J=4.496e-7)

# Material ref: https://github.com/JWock82/Pynite/blob/main/Pynite/Material.py
# Approximate values for steel beams:
# E = 200000 MPa (SkyCiv) (1Pa = 1N/m^2)
# G = 79300 MPa (https://www.engineeringtoolbox.com/modulus-rigidity-d_946.html)
#  Optional in SkyCiv but required in PyNite
# nu = 0.27 (SkyCiv)
# rho = 7850 kg/m^3 (SkyCiv)
model.add_material(
    "Steel",
    E=200000,  # Young's modulus
    G=29000,  # Shear modulus of elasticity (ksi)
    nu=0.27,  # Poisson's ratio
    rho=7850,  # Density
)


# Add nodes to model with anatomical names
for v in bm.verts:

    # Get respective input node data
    input_node = input_nodes[v.index]
    node_name = input_node[0]
    is_supported = input_node[1]

    model.add_node(input_node[0], v.co.x, v.co.y, v.co.z)

    # Add support for nodes that make contact
    # Pined supports - only release rotationally in local Z axis
    if is_supported:
        model.def_support(
            node_name,
            support_DX=True,
            support_DY=True,
            support_DZ=True,
            support_RX=True,
            support_RY=True,
            support_RZ=False,
        )


# Add members to model with anatomical names
for e in bm.edges:

    # Get respective input member and data
    input_member = input_members[e.index]
    member_name = input_member[0]
    m_distribution = input_member[1]
    cm_percent = input_member[2]

    # Obtain the unique indices of the 2 vertices connected to each edge
    i = e.verts[0].index
    j = e.verts[1].index
    model.add_member(
        member_name,
        input_nodes[i][0],
        input_nodes[j][0],
        "Steel",
        "S")

    # Option to add releases:
    # https://github.com/JWock82/Pynite/blob/25897a43a4a25f41b3c5709817974169ffff0f4f/Pynite/Member3D.py#L103
    # Equivalent to SkyCiv node fixicity (currently set to all fixed, which is Pynite default)

    # Add point load at CM based on CM percent; calculate length along the member
    # https://pynite.readthedocs.io/en/latest/member.html#local-coordinate-system
    # Each member starts at its i-node and ends at its j-node.
    # The local x-axis for the member is defined by a vector going from the i-node to the j-node.

    # UNIT NOTE: we will calculate the weight (Newtons) by multiplying input mass by g (9.81m/s^2).
    # This is for the calculations to scientifically make sense, though we ultimately need the
    # weight on supported nodes in kg - this is dealt with in post-processing.

    if m_distribution > 0:
        limb_weight = BODY_MASS_KG * G * m_distribution / 100  # Newtons
        member = model.members[member_name]
        member_length = member.L()
        cm_length = member_length * cm_percent / 100  # Meters
        model.add_member_pt_load(
            member_name, "FZ", -1 * limb_weight, cm_length, case="Point"
            # Weight should be globally downwards in direction
        )

        # Visualize the COM point in Blender
        # First, find the coordinate of the COM point along the member
        start_node = member.i_node
        end_node = member.j_node
        c_x = start_node.X + cm_percent / 100 * (end_node.X - start_node.X)
        c_y = start_node.Y + cm_percent / 100 * (end_node.Y - start_node.Y)
        c_z = start_node.Z + cm_percent / 100 * (end_node.Z - start_node.Z)

        # Draw cone in Blender at the coordinate
        # Depends on the model position being at (0,0,0)
        bpy.ops.mesh.primitive_cone_add(
            vertices = 8,
            radius1 = 0,
            radius2 = 0.03,
            depth = 0.05,
            enter_editmode = False,
            align = 'WORLD',
            location = (c_x, c_y, c_z)
        )

# Consolidate point loads into a load combo, to be referenced in results
model.add_load_combo("Combo", {"Point": 1.0})

# Free mesh from memory
bm.free()
logger.info("3D model constructed.")

# Log number of nodes and coordinates
logger.info("\nNodes: %d", len(model.nodes))
for name, node in model.nodes.items():
    logger.info("%s: (%.2f, %.2f, %.2f)", name, node.X, node.Y, node.Z)

# Log number of members and coordinates
logger.info("\nMembers: %d", len(model.members))
for name, member in model.members.items():
    i = member.i_node.name
    j = member.j_node.name
    logger.info("%s: %s -> %s", name, i, j)

# Log point loads
logger.info("\nMember point loads:")
for name, member in model.members.items():
    for load in member.PtLoads:
        direction, magnitude, x, case = load
        logger.info("%s: %s = %s", name, direction, magnitude)

logger.info("\nSupports:")
for name, node in model.nodes.items():
    if any(
        [
            node.support_DX,
            node.support_DY,
            node.support_DZ,
            node.support_RX,
            node.support_RY,
            node.support_RZ,
        ]
    ):
        logger.info(name)


### RUN LINEAR ANALYSIS VIA PYNITE ###

logger.info("\nPerforming linear analysis")
model.analyze_linear(log=True, check_stability=True)

# Results
# Nodal displacements - how much each node has moved due to load
logger.info("Nodal displacements (meters):")
for name, node in model.nodes.items():
    dx = node.DX["Combo"]
    dy = node.DY["Combo"]
    dz = node.DZ["Combo"]
    if any(abs(v) > 1e-3 for v in (dx, dy, dz)):
        logger.info("%s: DX=%.2f  DY=%.2f  DZ=%.2f", name, dx, dy, dz)

# Reactions at supported nodes - forces that supports are exerting to
# stabilize structure
logger.info("\nReaction forces (Newtons):")
weights_on_supports_kg = []
for name, node in model.nodes.items():
    rx = node.RxnFX["Combo"]
    ry = node.RxnFY["Combo"]
    rz = node.RxnFZ["Combo"]
    if any(abs(v) > 1e-3 for v in (rx, ry, rz)):
        logger.info("%s: RxnFX=%.2f  RxnFY=%.2f  RxnFZ=%.2f", name, rx, ry, rz)

        # Calculate downwards weight (kg) on supported nodes
        # Flip sign because reaction force is in +Z direction
        weights_on_supports_kg.append([name, -int(rz / G)])

# Log weight exerted on each supported node
logger.info("Weight exerted on support nodes (kg):")
for node_name, w in weights_on_supports_kg:
    logger.info("%s: %.2f", node_name, w)

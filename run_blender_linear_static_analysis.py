# How to run:
# in terminal, ~
# source blender-env-3-13/bin/activate
# blender (opens app, select blender file)

# Use venv
import sys
sys.path.insert(0, "/Users/sl/blender-env-3-13/lib/python3.13/site-packages")

from Pynite import FEModel3D
import bpy
import bmesh
import logging
import os

# Log to output.txt in the current directory
# Need to go up 1 level since current directory is the Blender file we're running code in
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_path = os.path.join(script_dir, "output.txt")
log_format = "%(asctime)s %(levelname)s: %(message)s"
date_format = "%H:%M:%S"

# Get root logger and clear existing handlers from previous runs
logger = logging.getLogger()
logger.handlers.clear()
logger.setLevel(logging.DEBUG)

# Log to file output.txt
file_handler = logging.FileHandler(log_path, mode='w')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

# Also log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

logger.addHandler(file_handler)
logger.addHandler(console_handler)


### MECHANICS SETUP ###

# TODO: double check units (kips???)

# Input: total weight (kg)
body_weight = 100

# TODO2: global ordering of nodes/members to set loads; for now, hard-code based on order created
    # Coordinate-based (eg. by height or left/right) has many edge cases based on figure position
    # Construct graph data structure, identify limbs based on leaves/nodes with 1 member
    # Spine has 2 members on each end
    # Symmetry across spine: doesn't really matter R/L, but we can assume R/L arms/legs are on either side

# Get the active mesh in Blender window
me = bpy.context.object.data

# Create a BMesh representation
bm = bmesh.new()   # create an empty BMesh
bm.from_mesh(me)   # fill it in from a Mesh

# Order is specific to this model - manually listed from Blender coordinates
# [name, is_supported]
input_nodes = [
    ['l_shoulder', False],
    ['l_elbow', False],
    ['l_wrist', True],
    ['l_finger', False],
    ['r_shoulder', False],
    ['r_elbow', True],
    ['r_wrist', False],
    ['r_finger', False],
    ['neck_base', False],
    ['head_base', False],
    ['head_top', False],
    ['spine_base', False],
    ['r_hip', False],
    ['l_hip', False],
    ['l_knee', True],
    ['l_heel', False],
    ['l_toe', False],
    ['r_knee', True],
    ['r_heel', False],
    ['r_toe', False],
]

# [name, mass_percent, cm_percent]
input_members = [
    ['l_upperarm', 2.71, 57.72],
    ['l_forearm', 1.62, 45.74],
    ['l_back', 0, 0],
    ['r_upperarm', 2.71, 57.72],
    ['r_forearm', 1.62, 45.74],
    ['r_hand', 0.61, 79.00],
    ['r_back', 0, 0],
    ['neck', 0, 0],
    ['head', 6.94, 59.76],
    ['spine', 43.46, 44.86],
    ['r_pelvis', 0, 0],
    ['l_pelvis', 0, 0],
    ['l_thigh', 14.16, 40.95],
    ['l_calf', 4.33, 44.59],
    ['l_foot', 1.37, 44.15],
    ['r_thigh', 14.16, 40.95],
    ['r_calf', 4.33, 44.59],
    ['r_foot', 1.37, 44.15],
    ['l_hand', 0.61, 79.00],
]


### CONSTRUCT PYNITE 3D MODEL ###

# Create an FE Model (Pynite representation)
model = FEModel3D()

# ref: https://pynite.readthedocs.io/en/latest/FEModel3D.html#quick-start
# Need to add: nodes, materials, sections, members, support, node loads, load combos

# Section based on steel material characteristics - TODO make sure this doesn't add extra weight to the model
# A: cross-sectional area (pi*r^2)
# Iy: second moment of area (inertia) about the weak axis (pi*r^4/4)
# Iz: second moment of area (inertia) about the strong axis (pi*r^4/4)
# J: torsion constant (pi*r^4/2)
# (Source: https://skyciv.com/free-moment-of-inertia-calculator/, http://www.hyperphysics.phy-astr.gsu.edu/hbase/icyl.html)
model.add_section('S', A=0.00004, Iy=100000, Iz=100000, J=100000)

# Material ref: https://github.com/JWock82/Pynite/blob/main/Pynite/Material.py
# Approximate values for steel beams, from SkyCiv
model.add_material('Steel', 
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

    # Add support if needed - fix the node in place from translation and rotation in all axes
    if is_supported:
        model.def_support(node_name, 
            support_DX = True, 
            support_DY = True, 
            support_DZ = True, 
            support_RX = True, 
            support_RY = True, 
            support_RZ = True
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
    model.add_member(member_name, input_nodes[i][0], input_nodes[j][0], 'Steel', 'S')

    # Add point load at CM based on CM percent; calculate length along the member
    if m_distribution > 0:
        limb_weight = body_weight * m_distribution / 100

        # TODO: double check for direction of the CM position
        cm_length = model.members[member_name].L() * cm_percent / 100
        model.add_member_pt_load(member_name, 'FZ', -1 * limb_weight, cm_length, case='Point')


# Consolidate point loads into a load combo, to be referenced in analysis results
model.add_load_combo('Combo', {'Point': 1.0})

# Free mesh from memory
bm.free()
logger.info('3D model constructed.')

# Print number of nodes and coordinates
logger.info(f'\nNodes: {len(model.nodes)}')
for name, node in model.nodes.items():
    logger.info(f'{name}: ({node.X:.2f}, {node.Y:.2f}, {node.Z:.2f})')

# Print number of members and coordinates
logger.info(f'\nMembers: {len(model.members)}')
for name, member in model.members.items():
    i = member.i_node.name
    j = member.j_node.name
    logger.info(f'{name}: {i} -> {j}')

logger.info('\nMember point loads:')
for name, member in model.members.items():
    for load in member.PtLoads:
        direction, magnitude, x, case = load
        logger.info(f'{name}: {direction} = {magnitude}')

logger.info('\nSupports:')
for name, node in model.nodes.items():
    if any([node.support_DX, node.support_DY, node.support_DZ,
            node.support_RX, node.support_RY, node.support_RZ]):
        logger.info(name)


### RUN LINEAR ANALYSIS VIA PYNITE ###

logger.info('\nPerforming linear analysis')
model.analyze_linear(log=True, check_stability=True)

# Results
# Nodal displacements - how much each node has moved due to load
logger.info('Nodal displacements (meters):')
for name, node in model.nodes.items():
    dx = node.DX['Combo']
    dy = node.DY['Combo']
    dz = node.DZ['Combo']
    logger.info(f'{name}: DX={dx:.2f}  DY={dy:.2f}  DZ={dz:.2f}')

# Reactions at supported nodes - forces that supports are exerting to stabilize structure
logger.info('\nReaction forces (Newtons):')
for name, node in model.nodes.items():
    rx = node.RxnFX['Combo']
    ry = node.RxnFY['Combo']
    rz = node.RxnFZ['Combo']
    if any(abs(v) > 1e-10 for v in (rx, ry, rz)):
        logger.info(f'{name}: RxnFX={rx:.2f}  RxnFY={ry:.2f}  RxnFZ={rz:.2f}')

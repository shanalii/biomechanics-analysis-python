# How to run:
# in terminal, ~
# source blender-env-3-13/bin/activate
# blender (opens app, select blender file)

# use venv
import sys
sys.path.insert(0, "/Users/sl/blender-env-3-13/lib/python3.13/site-packages")

from Pynite import FEModel3D
import bpy
import bmesh

# TODO: add const for mass % distribution, longitudinal CM position %
# TODO: double check units (kips???)

### SETUP ###

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

# Order is specific to this model
# [name, is_supported]
input_nodes = [
    ['l_shoulder', False],
    ['l_elbow',    False],
    ['l_wrist',    True],
    ['l_finger',   False],
    ['r_shoulder', False],
    ['r_elbow',    True],
    ['r_wrist',    False],
    ['r_finger',   False],
    ['neck_base',  False],
    ['head_base',  False],
    ['head_top',   False],
    ['spine_base', False],
    ['r_hip',      False],
    ['l_hip',      False],
    ['l_knee',     True],
    ['l_heel',     False],
    ['l_toe',      False],
    ['r_knee',     True],
    ['r_heel',     False],
    ['r_toe',      False],
]

# [name, cm_percent]
input_members = [
    ['l_upperarm', 57.72],
    ['l_forearm',  45.74],
    ['l_back',     0],
    ['r_upperarm', 57.72],
    ['r_forearm',  45.74],
    ['r_hand',     79.00],
    ['r_back',     0],
    ['neck',       0],
    ['head',       59.76],
    ['spine',      44.86],
    ['r_pelvis',   0],
    ['l_pelvis',   0],
    ['l_thigh',    40.95],
    ['l_calf',     44.59],
    ['l_foot',     44.15],
    ['r_thigh',    40.95],
    ['r_calf',     44.59],
    ['r_foot',     44.15],
    ['l_hand',     79.00],
]


### CONSTRUCT PYNITE 3D MODEL ###

# Create an FE Model
model = FEModel3D()

# ref: https://pynite.readthedocs.io/en/latest/FEModel3D.html#quick-start
# Need to add: nodes, materials, sections, members, support, node loads, load combos

# Section based on steel material characteristics - this shouldn't add extra weight to the model
# A: cross-sectional area (pi*r^2)
# Iy: second moment of area (inertia) about the weak axis (pi*r^4/4)
# Iz: second moment of area (inertia) about the strong axis (pi*r^4/4)
# J: torsion constant (pi*r^4/2)
# (Source: https://skyciv.com/free-moment-of-inertia-calculator/, http://www.hyperphysics.phy-astr.gsu.edu/hbase/icyl.html)
model.add_section('S', A=0.00004, Iy=100000, Iz=100000, J=100000)

# Material ref: https://github.com/JWock82/Pynite/blob/main/Pynite/Material.py
# Approximate values for steel beams, from SkyCiv
# Additional info (including G)
# Name, Young's modulus, shear modulus of elasticity (ksi), Poisson's ratio, density
model.add_material('Steel', E=200000, G=29000, nu=0.27, rho=7850)

# Add nodes to model with anatomical names
for v in bm.verts:
    model.add_node(input_nodes[v.index][0], v.co.x, v.co.y, v.co.z)

# Add members to model with anatomical names
for e in bm.edges:
    # Obtain the unique indices of the 2 vertices connected to each edge
    i = e.verts[0].index
    j = e.verts[1].index
    model.add_member(input_members[e.index][0], input_nodes[i][0], input_nodes[j][0], 'Steel', 'S')

# Free mesh from memory
bm.free()
print('3D model constructed.')

# Print number of nodes and coordinates
print(f'Nodes: {len(model.nodes)}')
for name, node in model.nodes.items():
    print(f'{name}: ({node.X:.2f}, {node.Y:.2f}, {node.Z:.2f})')

# Print number of members and coordinates
print(f'Members: {len(model.members)}')
for name, member in model.members.items():
    i = member.i_node.name
    j = member.j_node.name
    print(f'{name}: {i}->{j}')

# Supports (for nodes) from translation/rotation from every axis
# Set supports based on node dict
for data in input_nodes:
    if data[1]:
        model.def_support(data[0], support_DX=True, support_DY=True, support_DZ=True, support_RX=True, support_RY=True, support_RZ=True)

# TODO: add loads for each member based on weight and longitudinal CM
# Point loads at the center of mass point, amount = weight of segment
# Geometry/Accessors - model.members['M'].L(): returns member length - model.members['M'].i_node, .j_node: node objects
# model.add_member_pt_load('M1', 'FZ', -1030, 0.15, case='Point') # 4th arg is proximal value, in length units
model.add_member_pt_load('head', 'FZ', -1030, 0.15, case='Point')
model.add_load_combo('Combo', {'Point': 1.0})


### RUN LINEAR ANALYSIS VIA PYNITE ###

print('Performing linear analysis')
model.analyze_linear(log=True, check_stability=False)

# Results
# Nodal displacements - how much each node has moved due to load
print('Nodal displacements (meters):')
for name, node in model.nodes.items():
    dx = node.DX['Combo']
    dy = node.DY['Combo']
    dz = node.DZ['Combo']
    print(f'{name}: DX={dx:.2f}  DY={dy:.2f}  DZ={dz:.2f}')

# Reactions at supported nodes - forces that supports are exerting to stabilize structure
print('Reaction forces (Newtons):')
for name, node in model.nodes.items():
    rx = node.RxnFX['Combo']
    ry = node.RxnFY['Combo']
    rz = node.RxnFZ['Combo']
    if any(abs(v) > 1e-10 for v in (rx, ry, rz)):
        print(f'{name}: RxnFX={rx:.2f}  RxnFY={ry:.2f}  RxnFZ={rz:.2f}')

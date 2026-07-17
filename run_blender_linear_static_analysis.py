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

# Assign:
    # Support boolean of each node
        # 2 knees, right elbow, left wrist (different for each model)
    # Load of each member
# TODO: member dict of {name}: {index, CM position (length)}
    # Access nodes connecting: model.members[index].i_node or j_node

# Order is specific to this model
# {name}: [index, is_supported]
model_nodes = {
    'l_shoulder':[0, False],
    'l_elbow':[1, False], 
    'l_wrist':[2, True],
    'l_finger':[3, False],
    'r_shoulder':[4, False],
    'r_elbow':[5, True], 
    'r_wrist':[6, False],
    'r_finger':[7, False],
    'neck_base':[8, False],
    'head_base':[9, False], 
    'head_top':[10, False],
    'spine_base':[11, False],
    'r_hip':[12, False],
    'l_hip':[13, False],
    'l_knee':[14, True], 
    'l_heel':[15, False],
    'l_toe':[16, False],
    'r_knee':[17, True], 
    'r_heel':[18, False],
    'r_toe':[19, False],
}

# {name}: [index, cm_percent]
model_members = {
    'l_upperarm':[0, 57.72],
    'l_forearm':[1, 45.74], 
    'l_back':[2, 0],
    'r_upperarm':[3, 57.72],
    'r_forearm':[4, 45.74],
    'r_hand':[5, 79.00], 
    'r_back':[6, 0],
    'neck':[7, 0],
    'head':[8, 59.76],
    'spine':[9, 44.86], 
    'r_pelvis':[10, 0],
    'l_pelvis':[11, 0],
    'l_thigh':[12, 40.95],
    'l_calf':[13, 44.59],
    'l_foot':[14, 44.15], 
    'r_thigh':[15, 40.95],
    'r_calf':[16, 44.59],
    'r_foot':[17, 44.15], 
    'l_hand':[18, 79.00],
}


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

# Add nodes to model, name based on part of body
for v in bm.verts:
    model.add_node(f'N{v.index}', v.co.x, v.co.y, v.co.z)

# Add members to model, prefixed by M
for e in bm.edges:
    # Obtain the unique indices of the 2 vertices connected to each edge
    i = e.verts[0].index
    j = e.verts[1].index
    model.add_member(f'M{e.index}', f'N{i}', f'N{j}', 'Steel', 'S')

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
# TODO: set supports based on node dict
model.def_support('N2', support_DX=True, support_DY=True, support_DZ=True, support_RX=True, support_RY=True, support_RZ=True) # left wrist
model.def_support('N5', support_DX=True, support_DY=True, support_DZ=True, support_RX=True, support_RY=True, support_RZ=True) # right elbow


# TODO: add loads for each member based on weight and longitudinal CM
# Point loads at the center of mass point, amount = weight of segment
# Geometry/Accessors - model.members['M'].L(): returns member length - model.members['M'].i_node, .j_node: node objects
model.add_member_pt_load('M1', 'FZ', -1030, 0.15, case='Point') # 4th arg is proximal value, in length units
model.add_member_pt_load('M0', 'FZ', -1030, 0.15, case='Point')
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

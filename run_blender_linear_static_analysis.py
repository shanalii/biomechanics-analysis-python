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

### SETUP ###

# Load input csv file with figure 
# TODO: we need to assert some sort of order of the nodes/members to set the individual loads on them
# Input csv format will be: index/name of limb/member, mass (or % distribution)
# Additional input: total mass

# Get the active mesh in Blender window
me = bpy.context.object.data

# Create a BMesh representation
bm = bmesh.new()   # create an empty BMesh
bm.from_mesh(me)   # fill it in from a Mesh


### CONSTRUCT PYNITE 3D MODEL ###

# Create an FE Model
model = FEModel3D()

# ref: https://pynite.readthedocs.io/en/latest/FEModel3D.html#quick-start
# Need to add: nodes, materials, sections, members, support, node loads, load combos

# Single section for everything, test values for now
# TODO: do we need real values? - probably do for A, the cross-sectional area
# A: cross-sectional area (pi*r^2)
# Iy: second moment of area (inertia) about the weak axis (pi*r^4/4)
# Iz: second moment of area (inertia) about the strong axis (pi*r^4/4)
# J: torsion constant (pi*r^4/2)
# (Source: https://skyciv.com/free-moment-of-inertia-calculator/, http://www.hyperphysics.phy-astr.gsu.edu/hbase/icyl.html)
model.add_section('S', A=0.5, Iy=1, Iz=1, J=1)

# Material ref: https://github.com/JWock82/Pynite/blob/main/Pynite/Material.py
# Approximate values for steel beams, from SkyCiv
# Additional info (including G)
# Name, Young's modulus, shear modulus of elasticity (ksi), Poisson's ratio, density
model.add_material('Steel', E=200000, G=29000, nu=0.27, rho=7850)

# Add nodes to model, prefixed by N
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
# TODO: determine supports, set all to true for now
model.def_support('N1', support_DX=True, support_DY=True, support_DZ=True, support_RX=True, support_RY=True, support_RZ=True)

# Add loads - only gravity for now
# https://pynite.readthedocs.io/en/latest/load_combo.html
model.add_member_self_weight('FZ', -9.81, case='Gravity')
model.add_load_combo('Combo', {'Gravity': 1.0})


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

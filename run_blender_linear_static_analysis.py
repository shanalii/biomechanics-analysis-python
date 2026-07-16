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

# Load input csv file with figure coordinate data

# Get the active mesh; TODO can we select out of multiple elements/only the visible ones in viewport?
me = bpy.context.object.data

# Get a BMesh representation
bm = bmesh.new()   # create an empty BMesh
bm.from_mesh(me)   # fill it in from a Mesh

# Create an FE Model
model = FEModel3D()

# ref: https://pynite.readthedocs.io/en/latest/FEModel3D.html#quick-start
# Need to add: nodes, materials, sections, members, support, node loads, load combos

# Single section for everything, test values for now
# TODO: do we need real values?
model.add_section('S', A=1, Iy=1, Iz=1, J=1)

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

print(f'Nodes: {len(model.nodes)}')
print(f'Members: {len(model.members)}')

# # Supports (for nodes) from translation/rotation from every axis
# model.def_support('N1', support_DX=True, support_DY=True, support_DZ=True, support_RX=True, support_RY=True, support_RZ=True)

# # TODO: add point loads
# model.add_node_load('N2', direction='FZ', P=-5.0, case='D')
# model.add_load_combo('1.0D', {'D': 1.0})

# print('Performing linear analysis')
# model.analyze_linear(log=True, check_stability=False)  # TODO: try with log=False; what does this change?

# # Results
# uz = model.nodes['N2'].DZ['1.0D']
# rxn = model.nodes['N1'].RxnFZ['1.0D']
# print(uz)
# print(rxn)

#import pprint
#node = list(model.nodes.values())[0]
#pprint.pprint(vars(node))
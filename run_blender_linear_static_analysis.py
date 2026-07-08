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

# Get the active mesh; TODO can we select out of multiple elements/only the visible ones in viewport?
me = bpy.context.object.data

# Get a BMesh representation
bm = bmesh.new()   # create an empty BMesh
bm.from_mesh(me)   # fill it in from a Mesh

# Create an FE Model
frame = FEModel3D()

# ref: https://pynite.readthedocs.io/en/latest/FEModel3D.html#quick-start
# Need to add: nodes, materials, sections, members, support, node loads, load combos

for i, v in enumerate(bm.verts):
    frame.add_node(f'N{i}', v.co[0], v.co[1], v.co[2])

# Material ref: https://github.com/JWock82/Pynite/blob/main/Pynite/Material.py
# Approximate values for steel beams, from SkyCiv
# Name, Young's modulus, G, Poisson's ratio, density
frame.add_material('A36', E=200000, G=2, nu=0.27, rho=7850)
#frame.add_section('Wsect', A=5, Iy=6, Iz=7, J=8)

# Add 3D model members for every edge in the mesh
for i, e in enumerate(bm.edges):
    i_node = f'N{e.verts[0].index}'
    j_node = f'N{e.verts[1].index}'
    frame.add_member(f'M{i}', i_node=i_node, j_node=j_node, material_name='A36', section_name='Wsect')

# Supports from translation/rotation from every axis
frame.def_support('N1', support_DX=True, support_DY=True, support_DZ=True, support_RX=True, support_RY=True, support_RZ=True)

# TODO: add point loads
frame.add_node_load('N2', direction='FZ', P=-5.0, case='D')
frame.add_load_combo('1.0D', {'D': 1.0})

print('Performing linear analysis')
frame.analyze_linear(log=True, check_stability=False)  # TODO: try with log=False; what does this change?

# Results
uz = frame.nodes['N2'].DZ['1.0D']
rxn = frame.nodes['N1'].RxnFZ['1.0D']
print(uz)
print(rxn)

#import pprint
#node = list(frame.nodes.values())[0]
#pprint.pprint(vars(node))
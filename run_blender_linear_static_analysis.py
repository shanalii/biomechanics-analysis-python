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

# Get the active mesh
me = bpy.context.object.data

# Get a BMesh representation
bm = bmesh.new()   # create an empty BMesh
bm.from_mesh(me)   # fill it in from a Mesh

# Create a FE Model
frame = FEModel3D()

# ref: https://pynite.readthedocs.io/en/latest/FEModel3D.html#quick-start
# Need to add: nodes, materials, sections, members, support, node loads, load combos

for i, v in enumerate(bm.verts):
    frame.add_node(f'N{i}', v.co[0], v.co[1], v.co[2])

frame.add_material('A36', E=1, G=2, nu=0.3, rho=0.0004)
frame.add_section('Wsect', A=5, Iy=6, Iz=7, J=8)

for i, e in enumerate(bm.edges):
    i_node = f'N{e.verts[0].index}'
    j_node = f'N{e.verts[1].index}'
    frame.add_member(f'M{i}', i_node, j_node, 'Steel', 'W8x31')

model.def_support('N1', support_DX=True, support_DY=True, support_DZ=True, support_RY=True, support_RZ=True)
model.add_node_load('N2', direction='FZ', P=-5.0, case='D')
model.add_load_combo('1.0D', {'D': 1.0})

print('Performing linear analysis')
model.analyze_linear(log=True, check_stability=False)

# Results
uz = model.nodes['N2'].DZ['1.0D']
rxn = model.nodes['N1'].RxnFZ['1.0D']


# frame.analyze_linear(log=True, check_stability=False)


# Geometry
# model.add_node('N1', 0.0, 0.0, 0.0)
# model.add_node('N2', 3.0, 0.0, 0.0)

# model.add_material('A36', E=29_000_000.0, G=11_200_000.0, nu=0.3, rho=0.283)
# model.add_section('Wsect', A=10.0, Iy=100.0, Iz=200.0, J=5.0)

# m1 = model.add_member('M1', i_node='N1', j_node='N2', material_name='A36', section_name='Wsect')

# # Supports and loads
# model.def_support('N1', support_DX=True, support_DY=True, support_DZ=True, support_RY=True, support_RZ=True)
# model.add_node_load('N2', direction='FZ', P=-5.0, case='D')

# # Load combinations and analysis
# model.add_load_combo('1.0D', {'D': 1.0})
# model.analyze_linear(log=False)

# # Results
# uz = model.nodes['N2'].DZ['1.0D']
# rxn = model.nodes['N1'].RxnFZ['1.0D']


#import pprint
#node = list(frame.nodes.values())[0]
#pprint.pprint(vars(node))
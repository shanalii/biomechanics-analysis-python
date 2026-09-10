"""Script to run linear analysis for Pynite stick figure model built from Blender mesh data."""
import os
import sys

# This script lives in scripts/, one level below the repo root - add the repo
# root to sys.path so the biomechanics package is importable.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

# Make Blender use venv
sys.path.insert(0, "/Users/sl/blender-env-3-13/lib/python3.13/site-packages")

# Ignore lint errors for imports from Blender's internal module
import bpy  # type: ignore  # pylint: disable=wrong-import-position

from biomechanics.analysis import AnalysisRunner  # pylint: disable=wrong-import-position
from biomechanics.body_data import (  # pylint: disable=wrong-import-position
    BODY_MASS_KG,
    BODY_MEMBERS,
    BODY_NODES,
    G,
)
from biomechanics.logging_setup import configure_logging  # pylint: disable=wrong-import-position
from biomechanics.mesh_reader import MeshReader  # pylint: disable=wrong-import-position
from biomechanics.model_builder import ModelBuilder  # pylint: disable=wrong-import-position
from biomechanics.results import log_model_summary  # pylint: disable=wrong-import-position
from biomechanics.visualizer import ComVisualizer  # pylint: disable=wrong-import-position

# How to run:
# in terminal, ~
# source blender-env-3-13/bin/activate
# blender (opens app, select blender file, open scripts/run_blender_linear_static_analysis.py)

### LOGGING SETUP ###

# Log to output/output.txt in the repo root
output_dir = os.path.join(REPO_ROOT, "output")
os.makedirs(output_dir, exist_ok=True)
log_path = os.path.join(output_dir, "output.txt")
logger = configure_logging(log_path)


### BUILD PYNITE 3D MODEL FROM BLENDER MESH ###

mesh_data = MeshReader(bpy.context.object).read()

builder = ModelBuilder(mesh_data, BODY_NODES, BODY_MEMBERS, BODY_MASS_KG, G)
model = builder.build()
logger.info("3D model constructed.")
log_model_summary(model, logger)


### VISUALIZE MEMBER CENTER-OF-MASS POINTS IN BLENDER ###

com_points = [
    ModelBuilder.member_com_point(model.members[member.name], member.cm_percent)
    for member in BODY_MEMBERS
    if member.mass_percent > 0
]
ComVisualizer().draw_com_markers(com_points)


### RUN LINEAR ANALYSIS VIA PYNITE ###

results = AnalysisRunner(model, G, logger=logger).run()
results.log_summary(logger)

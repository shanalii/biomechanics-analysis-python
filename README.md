# A Biomechanics Analysis Tool for Rigid Bodies

A Python script that performs [linear static analysis](https://ansyshelp.ansys.com/public/account/secured?returnurl=/Views/Secured/corp/v252/en/lsdyna_imp_an/lsdi_examples_linear_static.html) on rigid human-like bodies, in collaboration with [Forensic Architecture](https://forensic-architecture.org/). 

More info coming soon! :)

## Usage

1. In a terminal in the home directory ~ (exists in Shana's local machine), activate the Blender venv:
   ```
   source blender-env-3-13/bin/activate
   ```
2. Open Blender and load a stick-figure `.blend` file from `blender_files/`.
3. In Blender's **Scripting** tab, open (or copy/paste) `scripts/run_blender_linear_static_analysis.py`.
4. Click **Run Script** (play button at the top of the scripting window).

The script builds a [Pynite](https://github.com/JWock82/Pynite) finite-element model from the mesh, draws a cone at each limb's center-of-mass point in the Blender viewport, then runs linear static analysis.

### Outputs

Each run writes a timestamped txt file to `output/`. Only the 10 most recent output files are kept, and the oldest is deleted for the 11th run.

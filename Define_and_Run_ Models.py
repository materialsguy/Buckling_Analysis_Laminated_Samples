from abaqus import *
from caeModules import *
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
from odbAccess import*
from abaqusConstants import *

import os

###############################################################################
# If you use this code please cite:
# "Fatigue life assessment of metal foils in multifunctional composites via combined experiments and simulations"
# which will be published in "Composites B: Engineering" in 2023

# Written by Claus O. W. Trost
# see https://www.researchgate.net/profile/Claus-Trost
################################################################################

# Abaqus has a nearestNodeModule that needs to be imported in order to run all functions of analyse_model properly.
node_module_path = '/opt/abaqus/DassaultSystemes/SimulationServices/V6R2018x/linux_a64/code/python2.7/lib/abaqus_plugins/findNearestNode/'


PATH = "/home/c.trost/Documents/Abaqus_Python/Geometrien/Github_Sample_Design/V2/Codes/"
os.chdir(PATH)
from run_simulation import *


simulations_dir = check_and_create_paths(os.getcwd())
os.chdir(simulations_dir)
simulations_dir = simulations_dir + "/"

LENGTH = 2000
NOTCH_WIDTH = 1000
WIDTH = 3000
RADII = [None] # in this case gets calculated
CONSTANT_LINES = [1000]
FOIL_THICKNESSES = [30]
SUBSTRATE_THICKNESSES = [45.0, 55.0]

# Current Substrate Material (M1-106) extracted from Fuchs et al.
# (see https://doi.org/10.1016/j.microrel.2012.04.019 for details)
# Put your own Substrate details here!

SUBSTRATE_MATERIALS = [[13120, 13120, 9020, 0.19, 0.33, 0.33, 3380, 3300, 3850]]
SUBSTRATE_MATERIALS_NAME = "Pre-Preg"

JOB_NUMBERS = ["Test"]
IMPERFECTIONS = [1]
NUMBER_OF_FOILS = [26]
NOTCH_INSERTS = [1000]


for RADIUS in RADII:
    for CONSTANT_LINE in CONSTANT_LINES:
        for NOTCH_INSERT in NOTCH_INSERTS:
            for FOIL_THICKNESS in FOIL_THICKNESSES:
                for i, FOIL_NUMBER in enumerate(NUMBER_OF_FOILS):
                    for SUBSTRATE_MATERIAL in SUBSTRATE_MATERIALS:
                        OUTPUT_EIGENVALUE="result_buckling_{}{}.dat".format(SUBSTRATE_MATERIALS_NAME, JOB_NUMBERS[i], node_module_path)
                        eigenvalue_analysis(simulations_dir, LENGTH, WIDTH, NOTCH_WIDTH, NOTCH_INSERT, RADIUS, CONSTANT_LINE, FOIL_THICKNESS, SUBSTRATE_THICKNESSES, SUBSTRATE_MATERIAL, JOB_NUMBERS[i], OUTPUT_EIGENVALUE, FOIL_NUMBER,node_module_path, run=True)
                        for IMPERFECTION in IMPERFECTIONS: # Same eigenvalue_analysis calculations can be used for numerous imperfections.
                            buckling_analysis(simulations_dir, IMPERFECTION, LENGTH, WIDTH, NOTCH_WIDTH, NOTCH_INSERT, RADIUS, CONSTANT_LINE, FOIL_THICKNESS, SUBSTRATE_THICKNESSES, JOB_NUMBERS[i], OUTPUT_EIGENVALUE, FOIL_NUMBER, node_module_path, calculate_radius=True)

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

import numpy as np
import re
import os
import math


from geometry_functions import *
from material_model import *
from step_definition import *
from meshing import *
from job_definition import *
from tools import *
from evaluate_sample import *


def check_and_create_paths(current_dir):
    # Create the 'simulation' folder
    simulation_folder = os.path.join(current_dir, 'simulation')
    if not os.path.exists(simulation_folder):
        os.makedirs(simulation_folder)

    # Create the 'results' folder inside the 'simulation' folder
    results_folder = os.path.join(simulation_folder, 'results')
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    return simulation_folder


def eigenvalue_analysis(path, length, width, notch_width, notch_insert, radius, constant_line, foil_thickness, substrate_thickness, substrate_material, job_number, output_eigenvalue, number_of_foils, node_module_path, run=True):
    length =float(length)
    constant_line = float(constant_line)
    foil_thickness = float(foil_thickness)
    notch_width = float(notch_width)
    thickness = number_of_foils * foil_thickness + (number_of_foils/2) * substrate_thickness[0] + (number_of_foils/2-1) * substrate_thickness[1]
    print("thickness:", thickness)


    width, angle, top_line, radius = create_geometry(length, notch_width, notch_insert, thickness, radius, constant_line, width=width, calculate_radius=True)
    print("Width:", width)
    complete_length = length + top_line

    create_datum_planes(complete_length, width,notch_width, radius, thickness, foil_thickness, substrate_thickness, constant_line)

    create_cyclic_material_model('Model-1')
    generate_substrate_material(E1=substrate_material[0], E2=substrate_material[1], E3=substrate_material[2], v12=substrate_material[3], v23=substrate_material[4], v13=substrate_material[5], G12=substrate_material[6], G13=substrate_material[7], G23=substrate_material[8])
    foil_cells, substrate_cells= create_sections(complete_length, width, notch_width, thickness, constant_line, substrate_thickness, foil_thickness)
    all_cells = foil_cells+substrate_cells

    generate_eigenvalue_step()

    create_bc_and_load(complete_length, width, radius, notch_width, constant_line, thickness, foil_thickness, substrate_thickness, 'Model-1')

    create_mesh(complete_length, width, notch_width, notch_insert, thickness, radius, constant_line, foil_thickness, substrate_thickness, all_cells, angle, top_line)
    if run:
        run_job(path, job_number)
        mdb.saveAs(pathName="Buckling_{}.cae".format(job_number))
        import_nearest_node_module(node_module_path)
        eigenvalue = find_eigenvalue(path, job_number)

        file_name = "Buckling_{}".format(job_number)
        node_0, node_1, node_2, node_3 = find_nearest_node(path, file_name, complete_length, notch_width, constant_line)
        result = [complete_length, width, notch_width, radius, constant_line, foil_thickness, substrate_thickness[0], eigenvalue, node_0, node_1, node_2, node_3]
        np.savetxt(output_eigenvalue, result, delimiter=",")
        name = 'Buckling_{}'.format(job_number)
        remove_files(name)
        print('Eigenvalue Buckling Analysis completed!')


def buckling_analysis(path, imperfection, length, width, notch_width, notch_insert, radius, constant_line, foil_thickness, substrate_thickness, job_number, output_eigenvalue, number_of_foils, node_module_path, calculate_radius=False, run_model=True ):
    length = float(length)
    constant_line = float(constant_line)
    foil_thickness = float(foil_thickness)
    notch_width = float(notch_width)
    thickness = number_of_foils * foil_thickness + (number_of_foils/2) * substrate_thickness[0] + (number_of_foils/2-1) * substrate_thickness[1]

    if calculate_radius:
        radius = calculation_radius(length, width, notch_width, constant_line, notch_insert)

    print("thickness", thickness)

    file_name = 'Post_Buckling_force_{}_IMP_{}'.format(job_number, imperfection)
    if run_model:
        openMdb(pathName="{}Buckling_{}.cae".format(path,job_number))

        create_second_model(length, width, radius, constant_line, notch_width, thickness, foil_thickness, substrate_thickness, path, job_number, break_by_displacement=False)
        change_input_file_riks(path, file_name,  job_number, imperfection)
        _ = run_second_model(path, file_name)

        remove_files(file_name)
    else:
        _ = session.openOdb(name="{}.odb".format(file_name))
    frames = get_frames(path, file_name)
    print("Number of frames:", frames)

    import_nearest_node_module(node_module_path)
    evaluate_riks(path, length, width, notch_width, radius, constant_line,thickness, foil_thickness, substrate_thickness, number_of_foils, imperfection, file_name, frames, job_number)
    print('Buckling Analysis completed!')

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


def import_nearest_node_module(node_module_path):
    sys.path.insert(0, node_module_path)
    from nearestNodeModule import findNearestNode


def evaluate_riks(path, length, width, notch_width, radius, constant_line, thickness, foil_thickness, substrate_thickness, number_of_foils, imperfection, file_name, frames, job_number):

    pre_file_name='Buckling_{}'.format(job_number)

    node_number = find_nearest_node_from_pre_buckling(path, pre_file_name,[[1,0,0], [0,0,0], [0, length, 0], [0, constant_line, 0], [-notch_width, 0, 0]])

    extract_force(path, file_name, node_number[0])

    create_path(node_number[1], node_number[2], node_number[3])
    create_output(path, frames, length, width, radius, constant_line,foil_thickness, substrate_thickness, number_of_foils, imperfection, file_name)

    evaluate_path_quer(path, file_name, frames, node_number[1], node_number[4])

    coordinates = find_all_foil_coordinates(thickness, foil_thickness, substrate_thickness)
    nodes = find_nearest_node_from_pre_buckling_foils(path, file_name, coordinates, notch_width)
    for i, node in enumerate(nodes):
        evaluate_path_quer(path, file_name, frames, node[0], node[1], position_name=i)


def find_nearest_node_from_pre_buckling(path, file_name, coordinates):
    '''
    finds nearest Nodes to specific coordinates
    '''
    _ = session.openOdb('{}{}.odb'.format(path, file_name))
    session.viewports[session.currentViewportName].odbDisplay.setFrame(step='Step-1', frame=0)
    from nearestNodeModule import findNearestNode
    nodes = []
    for coordinate in coordinates:
        node = findNearestNode(xcoord=coordinate[0], ycoord=coordinate[1], zcoord=coordinate[2], name='{}{}.odb'.format(path, file_name), instanceName='')
        nodes.append(node[0])
    return nodes


def extract_force(path, file, node_number):
    o1 = session.openOdb('{}{}.odb'.format(path, file))
    session.viewports['Viewport: 1'].setValues(displayedObject=o1)
    session.linkedViewportCommands.setValues(_highlightLinkedViewports=False)
    odb = session.odbs['{}{}.odb'.format(path, file)]
    xy = xyPlot.XYDataFromHistory(odb=odb, outputVariableName='Reaction force: RF2 at Node {} in NSET POINT'.format(node_number), steps=('Step-1', ), suppressQuery=True, __linkedVpName__='Viewport: 1')
    data = np.array(xy)
    file_name = '{}/results/result_{}_force.dat'.format(path, file)
    np.savetxt(file_name, np.array(xy))


def create_path(node_0, node_1, node_2):
    '''
    Creates the paths for the data ANALYSIS
    '''
    pth = session.Path(name='Path-1', type=NODE_LIST, expression=(('PART-1-1', (node_0, node_2, )), ))
    pth2 = session.Path(name='Path-2', type=NODE_LIST, expression=(('PART-1-1', (node_1, node_0, )), ))


def create_output(path, frames, length, width, radius, constant_line,foil_thickness, substrate_thickness, number_of_foils, imperfection, job_name):
    '''
    Creates Output from Ricks ANALYSIS

    Calculates the exported paths. One in the notched area (pth) and another one between the top and the middle (pth2).
    It then loops all U1, U2 and U3 and exports the first and last point of the path.

    Parameters:
    -----
    Path and Geometry parameters of the sample.
    Job Number
    '''
    odb_name = '{}{}.odb'.format(path,job_name)
    frames = int(frames)
    odb = openOdb(path=odb_name)
    session.viewports['Viewport: 1'].setValues(displayedObject=odb)
    pth = session.paths['Path-1']
    pth2 = session.paths['Path-2']
    components = ['U1','U2','U3']
    output_compressed = []
    output_top_middle = []
    for component in components:
        for frame in range(frames):
            session.viewports['Viewport: 1'].odbDisplay.setPrimaryVariable(
                variableLabel='U', outputPosition=NODAL, refinement=(COMPONENT, component))
            session.viewports['Viewport: 1'].odbDisplay.setFrame(step=0, frame=frame)
            num_intervals = 2
            xy = session.XYDataFromPath(name='Data_{}_frame_{}'.format(component, frame), path=pth, includeIntersections=True,
                projectOntoMesh=False, pathStyle=UNIFORM_SPACING, numIntervals=num_intervals,
                projectionTolerance=0, shape=UNDEFORMED, labelType=Y_COORDINATE,
                removeDuplicateXYPairs=True, includeAllElements=False)
            data = np.array(xy)
            #np.savetxt('{}{}_compressed_frame_{}.dat'.format(path,component, frame), data)
            output_compressed.append([data[0][1], data[-1][1]])

            xy = session.XYDataFromPath(name='Data_{}_frame_{}'.format(component, frame), path=pth2, includeIntersections=True,
                projectOntoMesh=False, pathStyle=UNIFORM_SPACING, numIntervals=100,
                projectionTolerance=0, shape=UNDEFORMED, labelType=Y_COORDINATE,
                removeDuplicateXYPairs=True, includeAllElements=False)
            data = np.array(xy)
            #np.savetxt('{}{}_TOPtoMIDDLE_frame_{}.dat'.format(path,component, frame), data)
            output_top_middle.append([data[0][1],data[-1][1]])
        file_name = '{}/results/{}_j_{}_compression_result.dat'.format(path,component, job_name)
        np.savetxt(file_name, output_compressed)
        file = open(file_name,'a')
        file.write('{} {} {} {} {} {} {} {}'.format(length, width, radius, constant_line,foil_thickness, substrate_thickness[0], number_of_foils, imperfection))
        file.close()
        file_name = '{}/results/{}_j_{}_TOPtoMIDDLE_result.dat'.format(path,component, job_name)
        np.savetxt(file_name, output_top_middle)
        file = open(file_name,'a')
        file.write('{} {} {} {} {} {} {} {}'.format(length, width, radius, constant_line, foil_thickness, substrate_thickness[0], number_of_foils, imperfection))
        file.close()
        output_compressed = []
        output_top_middle = []


def evaluate_path_quer(path, job_name, frames, node_0, node_1, position_name="surface"):
    o1 = session.openOdb('{}{}.odb'.format(path, job_name))
    session.viewports['Viewport: 1'].setValues(displayedObject=o1)
    session.linkedViewportCommands.setValues(_highlightLinkedViewports=False)
    _ = session.odbs['{}{}.odb'.format(path, job_name)]
    pth3 = session.Path(name='Quer_{}'.format(position_name), type=NODE_LIST, expression=(('PART-1-1', (node_0, )), ('PART-1-1', (node_1, ))))
    frames = int(frames)
    vp = session.viewports['Viewport: 1']
    components = ['S', 'LE', 'PE', "Mises"]
    num_intervals = 2
    for component in components:
        for frame in range(frames):
            if component == "Mises":
                vp.odbDisplay.setPrimaryVariable(variableLabel='S', outputPosition=INTEGRATION_POINT, refinement=(INVARIANT, 'Mises'), )
            else:
                vp.odbDisplay.setPrimaryVariable(variableLabel=component, outputPosition=INTEGRATION_POINT, refinement=(COMPONENT, '{}22'.format(component)), )
            vp.odbDisplay.setFrame(step=0, frame=frame)
            xy = session.XYDataFromPath(name='Data_{}_frame_{}'.format(component, frame), path=pth3, includeIntersections=True,
                projectOntoMesh=False, pathStyle=PATH_POINTS, numIntervals=num_intervals,
                projectionTolerance=0, shape=DEFORMED, labelType=TRUE_DISTANCE,
                removeDuplicateXYPairs=True, includeAllElements=False)
            data = np.array(xy)

            file_name='{}/results/{}_j_{}_{}_frame_{}.dat'.format(path, component, job_name, position_name, frame)
            np.savetxt(file_name, np.array(xy))


def find_all_foil_coordinates(thickness, foil_thickness, substrate_thickness):
    z_coordinate = []
    z = 0
    z_coordinate.append(z)
    z += foil_thickness/2
    j = 1
    while z < thickness:
        z_coordinate.append(round(z,8))
        if j % 2 ==0:
            z += (substrate_thickness[1] + foil_thickness)
        else:
            z += (substrate_thickness[0] + foil_thickness)
        j += 1
    z_coordinate.append(thickness)
    return z_coordinate


def find_nearest_node_from_pre_buckling_foils(path, file_name, coordinates, notch_width):
    '''
    finds nearest Nodes to specific coordinates for every foil_instance
    '''
    _ = session.openOdb('{}{}.odb'.format(path, file_name))
    session.viewports[session.currentViewportName].odbDisplay.setFrame(step='Step-1', frame=0)
    from nearestNodeModule import findNearestNode
    nodes = []
    for coordinate in coordinates:
        node_1 = findNearestNode(xcoord=0, ycoord=0, zcoord=coordinate, name='{}{}.odb'.format(path, file_name), instanceName='')
        node_2 = findNearestNode(xcoord=-notch_width, ycoord=0, zcoord=coordinate, name='{}{}.odb'.format(path, file_name), instanceName='')
        node_pair = [node_1[0], node_2[0]]
        nodes.append(node_pair)
    return nodes

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

from boundary_conditions import *


def find_eigenvalue(path, job_number):
    odb_name = '{}Buckling_{}.odb'.format(path, job_number)
    odb = openOdb(path=odb_name)
    eigenvalue = odb.steps['Step-1'].frames[1].description
    eigenvalue = re.findall('[0-9]+.[0-9]+',eigenvalue)
    return float(eigenvalue[0])


def find_nearest_node(path, file_name, length, notch_width, constant_line):
    '''
    finds nearest Nodes to specific coordinates
    '''
    session.viewports[session.currentViewportName].odbDisplay.setFrame(step='Step-1', frame=0)
    from  nearestNodeModule import findNearestNode
    node_0 = findNearestNode(xcoord=0, ycoord=0, zcoord=0, name='{}{}.odb'.format(path, file_name), instanceName='')
    node_1 = findNearestNode(xcoord=0, ycoord=length, zcoord=0, name='{}{}.odb'.format(path, file_name), instanceName='')
    node_2 = findNearestNode(xcoord=0, ycoord=constant_line, zcoord=0, name='{}{}.odb'.format(path, file_name), instanceName='')
    node_3 = findNearestNode(xcoord=-notch_width, ycoord=0, zcoord=0, name='{}{}.odb'.format(path, file_name), instanceName='')
    return node_0[0],node_1[0], node_2[0], node_3[0]


def create_second_model(length, width, radius, constant_line, notch_width, thickness, foil_thickness, substrate_thickness, path, job_number, first_model='Model-1', break_by_displacement=True, static_step = True):
    mdb.Model(name='Model-2', objectToCopy=mdb.models[first_model])
    m = mdb.models['Model-2']
    a = m.rootAssembly
    i = a.instances['Part-1-1']
    del m.steps['Step-1']
    if static_step:
        m.StaticStep(name='Step-1', previous='Initial', maxNumInc=1000000000, initialInc=0.015, minInc=1e-27, maxInc=0.06, nlgeom=ON)
    else:
        m.StaticRiksStep(initialArcInc=0.001, maxNumInc=1000, name='Step-1', nlgeom=ON, previous='Initial')

    if break_by_displacement:
        vertices = i.vertices.findAt(((0, 0, 0),))
        a.Set(vertices = vertices, name="Vertices")
        m.steps['Step-1'].setValues(dof=3, maximumDisplacement=thickness/7, nodeOn=ON, region=a.sets['Vertices'])

    eigenvalue = find_eigenvalue(path, job_number)
    print("Eigenvalue:", eigenvalue)
    create_bc_and_load(length, width, radius, notch_width, constant_line, thickness, foil_thickness, substrate_thickness, model_name='Model-2', force=-eigenvalue, displacement_control=True)
    create_history_output()


def create_history_output(model='Model-2'):
    m = mdb.models[model]
    a = m.rootAssembly
    m.HistoryOutputRequest(createStepName='Step-1', name='H-Output-2', rebar=EXCLUDE, region=
    a.sets['point'], sectionPoints=DEFAULT, variables=('RF1', 'RF2', 'RF3', 'RM1', 'RM2', 'RM3'))
    m.HistoryOutputRequest(createStepName='Step-1', name='H-Output-3', rebar=EXCLUDE, region=
    a.sets['bottom'], sectionPoints=DEFAULT, variables=('E22', 'PE22'))


def change_input_file_riks(path, job_name, job_number, imperfection):
    mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF,
        explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF,
        memory=90, memoryUnits=PERCENTAGE, model='Model-2', modelPrint=OFF,
        multiprocessingMode=DEFAULT, name=job_name, nodalOutputPrecision=SINGLE,
        numCpus=1, numGPUs=0, queue=None, resultsFormat=ODB, scratch='', type=
        ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)
    mdb.jobs[job_name].setValues(numCpus=10, numDomains=10, numGPUs=0)
    mdb.jobs[job_name].writeInput()
    print("Check")
    del mdb.jobs[job_name]

    if imperfection == 0:
        pass
    else:
        with open("{}{}.inp".format(path, job_name), "r") as f:
            lines = f.readlines()
            first = True
            for i, line in enumerate(lines):
                if first:
                    if line == "** STEP: Step-1\n":
                        lines.insert(i-1,  '*IMPERFECTION, FILE=Buckling_{},STEP=1\n'.format(job_number))
                        lines.insert(i, '1, {}\n'.format(imperfection))
                        lines.insert(i+1, '** ----------------------------------------------------------------\n')
                        first = False
                else:
                    if line == "*Output, field, variable=PRESELECT\n":
                        # upside down to make it easier
                        lines.insert(i+2, "COORD, U\n")
                        lines.insert(i+2, "*node output\n")
                        lines.insert(i+2, "*Output, field\n")
                        break
            print("Keywords changed")
            f.close()
        f = open("{}{}.inp".format(path, job_name), "w")
        for line in lines:
            f.write(line)

    mdb.JobFromInputFile(inputFileName="{}{}.inp".format(path, job_name), name=job_name, type=ANALYSIS, numCpus=6, numDomains=6)


def remove_files(name, endings=['log', 'sim', 'msg', 'prt', 'com', 'dat', 'mdl', 'stt']):
    for ending in endings:
        file_name = '{}.{}'.format(name, ending)
        if os.path.exists(file_name):
            os.remove(file_name)

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


def run_job(path, job_number):
    job_name = "Buckling_{}".format(job_number)
    mdb.models['Model-1'].rootAssembly.regenerate()
    mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF,
        explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF,
        memory=90, memoryUnits=PERCENTAGE, model='Model-1', modelPrint=OFF,
        multiprocessingMode=DEFAULT, name=job_name, nodalOutputPrecision=SINGLE,
        numCpus=1, numGPUs=0, queue=None, resultsFormat=ODB, scratch='', type=
        ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)
    mdb.jobs[job_name].writeInput()
    del mdb.jobs[job_name]
    change_input_file(path, job_name)
    mdb.JobFromInputFile(inputFileName="{}{}.inp".format(path, job_name), name=job_name, type=ANALYSIS)
    mdb.jobs[job_name].submit(consistencyChecking=OFF)
    mdb.jobs[job_name].waitForCompletion()


def change_input_file(path, name):
    with open("{}{}.inp".format(path,name), "r") as f:
        lines = f.readlines()
        lines.insert(len(lines)-1, "*NODE FILE\n")
        lines.insert(len(lines)-1, "U\n")
        f.close()
    file = open("{}{}.inp".format(path, name), "w")
    for line in lines:
        file.write(line)


def run_second_model(path, job_name, break_by_displacement=True):
    mdb.jobs[job_name].submit(consistencyChecking=OFF)
    if break_by_displacement:
        mdb.jobs[job_name].waitForCompletion()
        frames = get_frames(path, job_name)
    else:
        frames = check_run(path, file_name)
    return frames


def get_frames(path, job_name):
    file_name = '{}{}.sta'.format(path, job_name)
    fid = open(file_name, 'r', 0)
    for line in fid:
        fields = line.split()
        if len(fields) > 2:
            if fields[0] == '1':
                frames = float(fields[1])
    fid.close()
    return frames


def check_run(path, job_name):
    '''
    Additional Function that can be used to automatically stop a Riks step, which can be used instead of Static step after the calculation of the Eigenvalues.
    If no breaking criteria in a Riks Step is specified this code can be used to end step at the start of unstable buckling.
    More details and discussion can be found here: https://www.researchgate.net/post/How-can-I-stop-a-Riks-step-at-the-maximum-LPF-in-Abaqus
    '''
    #Initialise
    run = True
    LPFv = 10
    n = 0
    # check model
    file_name = '{}{}.sta'.format(path, file_name)
    while run:
        n += 1 # number of checks
        time.sleep(60) # wait for job to generate new output
        print('-CHECK {}-'.format(n))
        if os.path.exists(file_name):
            fid = open(file_name, 'r', 0)
            for line in fid:
                fields = line.split()
                if len(fields) > 0:
                    if fields[0] == '1': # check when actual data starts
                        LPFv = float(fields[7])
                else:
                    break
                    fid.close()
                    print('-CHECK {} done-'.format(n))
                if LPFv < 0: # If factor is negative kill job
                    frames = float(fields[1])
                    mdb.jobs[job_name].kill()
                    print('Job terminated by scrpit due to negative LPFv')
                    run = False
        else:
            print('-CHECK {} completed, no .sta file found, yet-'.format(n))
            if n == 10:
                print("Run terminated")
                break
    return frames

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


def generate_eigenvalue_step(numEigen=1):
    '''
    Generates Eigenvalue Step
    '''
    m=mdb.models['Model-1']
    m.BuckleStep(maxIterations=30000000, name='Step-1', numEigen=numEigen,
        previous='Initial', vectors=10)

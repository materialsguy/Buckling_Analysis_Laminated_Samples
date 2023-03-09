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


def create_bc_and_load(length, width, radius, notch_width, constant_line, thickness, foil_thickness, substrate_thickness, model_name='Model-1', force=-1, displacement_control=False):
    m = mdb.models[model_name]
    p = m.parts['Part-1']
    a = m.rootAssembly
    i = a.instances['Part-1-1']
    #create reference Point and force on point
    if model_name=="Model-1":
        point=p.ReferencePoint(point=(1.0, 0.0, 0.0))
        a.Set(name='point', referencePoints=(i.referencePoints[point.id], ))
        create_sets_top_bottom(0, notch_width, thickness, foil_thickness, substrate_thickness, "bottom", 'Model-1')
        create_sets_side(length, constant_line, thickness, substrate_thickness, foil_thickness, "side", "Model-1")
        create_sets_clamps(length, notch_width, thickness, "clamps", "Model-1")
    a.regenerate()

    if displacement_control:
        m.DisplacementBC(amplitude=UNSET, createStepName='Step-1',
            distributionType=UNIFORM, fieldName='', fixed=OFF, localCsys=None, name=
            'BC-4', region=a.sets['point'], u2=-length/100*2)
    else:
        m.ConcentratedForce(cf2=force, createStepName='Step-1',
                distributionType=UNIFORM, field='', localCsys=None, name='Load-1', region=
                a.sets['point'])
    m.Equation(name='Constraint-1', terms=((1.0, 'clamps', 2), (-1.0, 'point', 2)))

    m.DisplacementBC(amplitude=UNSET, createStepName='Initial',
        distributionType=UNIFORM, fieldName='', localCsys=None, name='BC-1',
        region=a.sets['bottom'], u1=UNSET, u2=SET,
        u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET)

    m.DisplacementBC(amplitude=UNSET, createStepName='Initial',
        distributionType=UNIFORM, fieldName='', localCsys=None, name='BC-2',
        region=a.sets['side'], u1=SET, u2=UNSET,
        u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET)

    m.DisplacementBC(amplitude=UNSET, createStepName='Initial',
        distributionType=UNIFORM, fieldName='', localCsys=None, name='BC-3',
        region=a.sets['clamps'], u1=UNSET, u2=UNSET,
        u3=SET, ur1=UNSET, ur2=UNSET, ur3=UNSET)


def create_sets_top_bottom(y_coordinate, width, thickness, foil_thickness, substrate_thickness, set_name, model_name):
    m=mdb.models[model_name]
    p=m.parts['Part-1']
    a=m.rootAssembly
    i=a.instances['Part-1-1']
    faces = i.faces.findAt(((-width/2, y_coordinate, foil_thickness/2),))
    next_foil=False
    foil_number = 1
    substrate_number_0 = 1
    substrate_number_1 = 0
    # start with big substrate
    z = foil_thickness + substrate_thickness[0]/2
    # next small substrate
    j = 2
    while z < thickness:
        faces += i.faces.findAt(((-width/2, y_coordinate, z),))
        if next_foil:
            if j % 2 == 0:
                substrate_number_1 += 1
                z = foil_thickness * (foil_number) + substrate_thickness[1] * (substrate_number_1 - 0.5) + substrate_thickness[0] * (substrate_number_0)
            else:
                substrate_number_0 +=1
                z = foil_thickness*(foil_number) + substrate_thickness[1] * (substrate_number_1) + substrate_thickness[0] * (substrate_number_0 - 0.5)
            j += 1
            next_foil = False
        else:
            foil_number += 1
            z = foil_thickness*(foil_number-0.5) + substrate_thickness[1] * substrate_number_1 + substrate_thickness[0] * substrate_number_0
            next_foil = True
    a.Set(faces=faces, name=set_name)


def create_sets_side(length, constant_line, thickness, substrate_thickness, foil_thickness, set_name, model_name):
    '''
    Creates sections and assigns materials/orientation.
    '''
    m=mdb.models[model_name]
    p=m.parts['Part-1']
    a=m.rootAssembly
    i=a.instances['Part-1-1']
    #Initialise segmentation_thickness
    next_foil = False
    # Initialise Cooridnates of Cells
    foil_number = 1
    substrate_number_0 = 0
    substrate_number_1 = 0
    x = 0
    y = constant_line/2
    #y_2 = (length - 11000 - constant_line)/2 + constant_line old version
    y_2 = constant_line + 100 # as in mark current model, +100 does the trick to get the right part of the sample
    y_3 = (length)/2
    z = foil_thickness / 2

    faces = i.faces.findAt(((x, y, z),))
    faces += i.faces.findAt(((x, y_2, z),))
    j = 1
    while z < thickness-foil_thickness:
        if next_foil:
            if j % 2 ==0:
                substrate_number_1 += 1
                z = substrate_number_0 * substrate_thickness[0] + (substrate_number_1 - 0.5) * substrate_thickness[1] + foil_number * foil_thickness
            else:
                substrate_number_0 += 1
                z = (substrate_number_0-0.5) * substrate_thickness[0] + (substrate_number_1) * substrate_thickness[1] + foil_number * foil_thickness
            j += 1
            next_foil = False
        else:
            foil_number += 1
            z = substrate_number_0 * substrate_thickness[0] + substrate_number_1 * substrate_thickness[1]+ (foil_number-0.5) * foil_thickness
            next_foil = True
        faces += i.faces.findAt(((x, y, z),))
        faces += i.faces.findAt(((x, y_2, z),))
        faces += i.faces.findAt(((x, y_3, z),))
    a.Set(faces=faces, name=set_name)


def create_sets_clamps(length, notch_width,  thickness, set_name, model_name):
    m = mdb.models[model_name]
    a = m.rootAssembly
    i = a.instances['Part-1-1']
    x = -notch_width/2
    y = length/2
    faces = i.faces.findAt(((x, y, 0),))
    faces += i.faces.findAt(((x, y, thickness),))
    a.Set(faces=faces, name=set_name)

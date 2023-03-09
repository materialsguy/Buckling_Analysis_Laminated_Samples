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
import math


def create_geometry(length, notch_width, notch_insert, thickness, radius, constant_line, width = None,  calculate_radius=False, complete_length = 15000):
    top_line = complete_length - length

    if calculate_radius:
        if width is None:
            radius = length - constant_line
            delta_x = math.sqrt(radius**2 - (length - constant_line)**2)
            width = notch_width - delta_x + radius
        else:
            radius = calculation_radius(length, width, notch_width, constant_line, notch_insert)
            print("Radius", radius)

    if length - constant_line - radius > 0:
        raise ValueError("LENGTH - CONSTANT_LINE - RADIUS needs to be > 0 to work")

    m = mdb.models['Model-1']
    m.ConstrainedSketch(name='__profile__', sheetSize=length*2)
    s = m.sketches['__profile__']
    # right line
    s.Line(point1=(0.0, 0.0), point2=(0.0, length + top_line)) #ok
    # bottom_line
    s.Line(point1=(0.0, 0.0), point2=(-notch_width, 0.0)) #ok
    # small left constant line
    s.Line(point1=(-notch_width, 0.0), point2=(-notch_width, constant_line)) #ok
    # rounding
    s.ArcByCenterEnds(center=(-(notch_width + radius), constant_line), direction=COUNTERCLOCKWISE,
        point1=(-notch_width, constant_line), point2=(-width + notch_insert, length))
    # top_line
    s.Line(point1=(0.0, length + top_line), point2=(-width, length + top_line)) #ok
    s.Line(point1=(-width, length), point2=(-width, length + top_line)) #ok
    # notch_insert
    s.Line(point1=(-width, length), point2=(-width + notch_insert, length),)
    m.Part(dimensionality=THREE_D, name='Part-1', type=DEFORMABLE_BODY)
    m.parts['Part-1'].BaseSolidExtrude(depth=thickness, sketch=s)

    angle= math.asin((length - constant_line)/radius)/2
    del s
    return width, angle, top_line, radius


def create_datum_planes(length, width,notch_width, radius, thickness, foil_thickness, substrate_thickness, constant_line, start_clamps=4000):
    '''
    Creates layer structure
    '''
    m = mdb.models['Model-1']
    p = m.parts['Part-1']
    a = m.rootAssembly
    segmentation_thickness = foil_thickness
    next_foil = True
    j = 1
    while segmentation_thickness < thickness:
        if next_foil:
            datum_plane(segmentation_thickness, XYPLANE, length, width, thickness)
            if j % 2 == 0:
                segmentation_thickness += substrate_thickness[1]
            else:
                segmentation_thickness += substrate_thickness[0]
            j += 1
            next_foil = False
        else:
            datum_plane(segmentation_thickness, XYPLANE, length, width, thickness)
            segmentation_thickness += foil_thickness
            next_foil = True
    datum_plane_down(constant_line, XZPLANE, length, radius, notch_width, thickness, foil_thickness, substrate_thickness)
    datum_plane_down(start_clamps, XZPLANE, length, radius, notch_width, thickness, foil_thickness, substrate_thickness) # for clamping
    # create instance in Abaqus
    a.DatumCsysByDefault(CARTESIAN)
    a.Instance(dependent=ON, name='Part-1-1',part=p)


def calculation_radius(length, width, notch_width, constant_line, notch_insert):
    delta_x = width - notch_width - notch_insert
    delta_y = length - constant_line
    radius = (delta_x**2 + delta_y**2)/(2*delta_x)
    return radius


def datum_plane(offset, principalPlane, length, width, thickness):
    '''
    Creates a single datum Plane and automatically partitions the whole model acordingly
    '''
    m = mdb.models['Model-1']
    p = m.parts['Part-1']
    plane = p.DatumPlaneByPrincipalPlane(offset=offset, principalPlane=principalPlane)
    all_cells = mark_all_cells(width, length, thickness)
    p.PartitionCellByDatumPlane(cells=all_cells, datumPlane=p.datums[plane.id])


def datum_plane_down(offset, principalPlane, length, radius, notch_width, thickness, foil_thickness, substrate_thickness):
    '''
    Creates the constant line datum plane cut
    '''
    m = mdb.models['Model-1']
    p = m.parts['Part-1']
    cells = p.cells
    # Create Plane
    plane = p.DatumPlaneByPrincipalPlane(offset=offset, principalPlane=principalPlane)
    #Define Coodinates
    x, y, z = -(notch_width)/2, (length-radius)/2, foil_thickness/2
    # Define if next thing is a foil
    next_foil = True
    j = 1
    while z < thickness:
        all_cells=cells.findAt(((x, y, z),))
        if next_foil:
            if j % 2 ==0:
                z += substrate_thickness[1]
            else:
                z += substrate_thickness[0]
            j += 1
            # Change to substrate
            next_foil = False
        else:
            z += foil_thickness
            next_foil = True
        p.PartitionCellByDatumPlane(cells=all_cells, datumPlane=p.datums[plane.id])


def mark_cells(x, y, z, x_2, y_2, z_2):
    'Marks cells in specific area'
    m = mdb.models['Model-1']
    p = m.parts['Part-1']
    cells = p.cells
    return cells.findAt(((x, y, z),), ((x_2, y_2, z_2),))


def mark_all_cells(width, length, thickness):
    'Marks all cells of model'
    return mark_cells(0, 0, 0, -width, length, thickness)


def create_sections(length, width, notch_width, thickness, constant_line, substrate_thickness, foil_thickness):
    '''
    Creates sections and assigns materials/orientation.
    '''
    m = mdb.models['Model-1']
    p = m.parts['Part-1']
    # Sections creation
    m.HomogeneousSolidSection(material='Copper', name='Copper_Section', thickness=None)
    m.HomogeneousSolidSection(material='Pre-Preg', name='Pre-Preg_Section', thickness=None)
    foil_cells, substrate_cells = mark_current_model(width, notch_width, length, foil_thickness, constant_line, substrate_thickness, thickness)
    p.Set(cells=foil_cells, name="Foils")
    p.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE,
        region=p.sets["Foils"], sectionName='Copper_Section', thicknessAssignment=FROM_SECTION)

    p.Set(cells=substrate_cells, name="Substrate")
    p.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE, region=
        p.sets["Substrate"], sectionName='Pre-Preg_Section', thicknessAssignment=FROM_SECTION)
    p.MaterialOrientation(
        additionalRotationType=ROTATION_NONE, axis=AXIS_1, fieldName='', localCsys=
        None, orientationType=GLOBAL, region=Region(cells=substrate_cells), stackDirection=STACK_3)
    return foil_cells, substrate_cells


def mark_current_model(width, notch_width, complete_length , foil_thickness, constant_line, substrate_thickness, thickness ):
    m = mdb.models['Model-1']
    p = m.parts['Part-1']
    cells = p.cells

    next_foil = True
    foil_number = 1
    substrate_number = 1
    # Initialise Cooridnates of Cells
    # to be in the middle of the cell --> foil_thickness/2
    z = foil_thickness/2
    # middle lower part
    x_1, y_1 = -notch_width/2, constant_line/2
    # middle higher part
    #x_2, y_2 = -notch_width/2, constant_line + 11000 #old version
    #x_3, y_3 = -notch_width/2, constant_line + (complete_length  - constant_line -11000)/2 #old version
    x_2, y_2 = -notch_width/2, constant_line + 100 # +100 does the trick to be in the right area (if anyone finds a  more elegant solution let me know ;) )
    x_3, y_3 = -notch_width/2, complete_length  - 100 # -100 does the trick to be in the right area
    j = 1
    while z <= thickness:
        # get constant line part of the section
        if next_foil:
            if foil_number == 1:
                foil_cells = cells.findAt(((x_1, y_1, z),))
                foil_cells += cells.findAt(((x_2, y_2, z),))
                foil_cells += cells.findAt(((x_3, y_3, z),))
            else:
                foil_cells += cells.findAt(((x_1, y_1, z),))
                foil_cells += cells.findAt(((x_2, y_2, z),))
                foil_cells += cells.findAt(((x_3, y_3, z),))
            # proceed with coordiates
            if j % 2 == 0:
                z += substrate_thickness[1]
            else:
                z += substrate_thickness[0]

            j += 1
            foil_number += 1
            # next layer is not a foil
            next_foil = False

        else:
            if substrate_number == 1:
                substrate_cells = cells.findAt(((x_1, y_1, z),))
                substrate_cells += cells.findAt(((x_2, y_2, z),))
                substrate_cells += cells.findAt(((x_3, y_3, z),))
            else:
                substrate_cells += cells.findAt(((x_1, y_1, z),))
                substrate_cells += cells.findAt(((x_2, y_2, z),))
                substrate_cells += cells.findAt(((x_3, y_3, z),))
            # create sets according to marked cells and set material orientation
            # proceed with coordiates
            z += foil_thickness
            substrate_number += 1
            # next layer is a foil
            next_foil = True
    return foil_cells, substrate_cells

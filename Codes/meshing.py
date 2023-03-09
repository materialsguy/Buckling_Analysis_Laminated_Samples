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


def create_mesh(length, width, notch_width, notch_insert, thickness, radius, constant_line, foil_thickness, substrate_thickness, all_cells, angle, top_line):
    p=mdb.models['Model-1'].parts['Part-1']
    # OK
    number_seeds_foil=5
    number_seeds_substrate=5
    print(length, width, notch_width, notch_insert, thickness, radius, constant_line, foil_thickness, substrate_thickness)
    # calculate_numberof seeds
    seed_number_side = 25
    ratio = constant_line/length
    long_part_seeds = int(seed_number_side*(1-ratio))
    constant_line_seeds = int(seed_number_side*(ratio))+4
    if constant_line_seeds < 10:
        constant_line_seeds = 10
    if long_part_seeds > 30:
        long_part_seeds = 30
    top_line_seeds = calculate_seeds(length, top_line, seed_number_side, 3)

    width_line_seeds = 40-4
    notch_width_line_seeds = calculate_seeds(width, notch_width, width_line_seeds, 10)
    notch_insert_seeds = calculate_seeds(width, notch_insert, width_line_seeds, 5)+3


    ################
    # radius
    radius_seeds = calculate_seeds(width, 2* np.pi*radius/2, width_line_seeds, 10)-3

    print(long_part_seeds, constant_line_seeds, radius_seeds, ratio)
    edges =  seed_geometry_edges(-(notch_width+radius-radius*math.cos(angle))*2, radius*math.sin(angle) + constant_line, thickness, foil_thickness, substrate_thickness)

    p.seedEdgeByNumber(constraint=FINER, edges=edges, number=radius_seeds)
    # left line over radius
    edges =  seed_geometry_edges(-width, (constant_line + radius +(length-constant_line-11000-radius)/2)*2, thickness, foil_thickness, substrate_thickness, horizontal=False)
    p.seedEdgeByNumber(constraint=FINER, edges=edges, number=top_line_seeds)
    # notch_insert
    edges =  seed_geometry_edges((-width+notch_insert/2)*2, (length-top_line), thickness, foil_thickness, substrate_thickness)
    p.seedEdgeByNumber(constraint=FINER, edges=edges, number=notch_insert_seeds)

    # long side
    edges =  seed_geometry_edges(0, (constant_line + (length-constant_line-11000)/2)*2, thickness, foil_thickness, substrate_thickness, horizontal=False)
    p.seedEdgeByNumber(constraint=FINER, edges=edges, number=long_part_seeds)

    edges =  seed_geometry_edges(0, length, thickness, foil_thickness, substrate_thickness, horizontal=False)
    edges +=  seed_geometry_edges(-width, length, thickness, foil_thickness, substrate_thickness, horizontal=False)
    #p.seedEdgeByBias(biasMethod=SINGLE, constraint=FINER, end1Edges=edges, number=20, ratio=5.0)
    p.seedEdgeByNumber(constraint=FINER, edges=edges, number=20)

    # constant_line
    edges =  seed_geometry_edges(0, constant_line, thickness, foil_thickness, substrate_thickness, horizontal=False)
    p.seedEdgeByNumber(constraint=FINER, edges=edges, number=constant_line_seeds)
    edges =  seed_geometry_edges(-notch_width, constant_line, thickness, foil_thickness, substrate_thickness, horizontal=False)
    p.seedEdgeByNumber(constraint=FINER, edges=edges, number=constant_line_seeds)

    # Foil
    edges = seeds_thickness_edges(length, width, notch_width, radius, constant_line, thickness, foil_thickness, substrate_thickness)
    p.seedEdgeByNumber(constraint=FINER, edges=edges, number=number_seeds_foil)
    # Substrate
    edges = seeds_thickness_edges(length, width, notch_width, radius, constant_line, thickness, foil_thickness, substrate_thickness, foil=False)
    p.seedEdgeByNumber(constraint=FINER, edges=edges, number=number_seeds_substrate)

    # unterste line
    edges = seed_geometry_edges(-notch_width, 0, thickness, foil_thickness, substrate_thickness)
    p.seedEdgeByNumber(constraint=FINER, edges=edges, number=notch_width_line_seeds)

    # horizontal constant line
    edges = seed_geometry_edges(-notch_width, constant_line, thickness, foil_thickness, substrate_thickness)
    p.seedEdgeByNumber(constraint=FINER, edges=edges, number=notch_width_line_seeds)

    # oberste line
    edges =  seed_geometry_edges(-width, length, thickness, foil_thickness, substrate_thickness)
    p.seedEdgeByNumber(constraint=FINER, edges=edges, number=5)

    # clamps down
    edges =  seed_geometry_edges(-width, 4000, thickness, foil_thickness, substrate_thickness)
    p.seedEdgeByNumber(constraint=FINER, edges=edges, number=width_line_seeds)

    #set_mesh_control
    p.setMeshControls(algorithm=MEDIAL_AXIS, regions=all_cells)
    p.generateMesh()


def calculate_seeds(length_1, length_2, seeds_long, min_seeds):
    ratio = length_2/length_1
    seeds = int(ratio*seeds_long)
    if seeds < min_seeds:
        return min_seeds
    return seeds


def seed_geometry_edges(x, y, thickness, foil_thickness, substrate_thickness, horizontal=True, radius= False):
        p = mdb.models['Model-1'].parts['Part-1']
        if horizontal:
            x, y, z = x/2, y, 0
        else:
            x, y, z = x, y/2, 0
        edges = p.edges.findAt(((x, y, z),))
        z = foil_thickness
        next_foil = False
        j = 1
        while z <= thickness:
            edges += p.edges.findAt(((x, y, z),))
            if next_foil:
                z += foil_thickness
                next_foil = False
            else:
                if j % 2 == 0:
                    z += substrate_thickness[1]
                else:
                    z += substrate_thickness[0]
                j += 1
                next_foil = True
        return edges


def seeds_thickness_edges(length, width, notch_width, radius, constant_line, thickness, foil_thickness, substrate_thickness, foil=True):
    if foil:
        z = foil_thickness/2
        j = 1
    else:
        z = foil_thickness + substrate_thickness[0]/2
        j = 2
    edges = get_thickness_edges(length, width, notch_width, radius, constant_line, thickness, foil_thickness, z)
    if j % 2 == 0:
        z += substrate_thickness[1] +  foil_thickness
    else:
        z += substrate_thickness[0] +  foil_thickness
    j += 1
    while z < thickness:
        edges += get_thickness_edges(length, width, notch_width, radius, constant_line, thickness, foil_thickness, z)
        if j % 2 == 0:
            z += substrate_thickness[1] +  foil_thickness
        else:
            z += substrate_thickness[0] +  foil_thickness
        j += 1
    return edges


def get_thickness_edges(length, width, notch_width, radius, constant_line, thickness, foil_thickness, z):
    p = mdb.models['Model-1'].parts['Part-1']
    edges = p.edges.findAt(((0, 0, z),))
    edges += p.edges.findAt(((0, constant_line, z),))
    edges += p.edges.findAt(((0, length, z),))
    edges += p.edges.findAt(((-width, length, z),))
    edges += p.edges.findAt(((-notch_width, 0, z),))
    edges += p.edges.findAt(((-notch_width, constant_line, z),))
    return edges

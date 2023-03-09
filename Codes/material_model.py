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
import numpy as np


def generate_substrate_material(E1, E2, E3, v12, v23, v13, G12, G13, G23):
    m = mdb.models['Model-1']
    mat = m.Material(name='Pre-Preg')
    D1111, D2222, D3333, D1122, D1133, D2233, D1212, D1313, D2323 = calculate_orthotropic_parameters(E1, E2, E3, v12, v23, v13, G12, G13, G23)
    mat.Elastic(table=((D1111, D1122, D2222, D1133, D2233, D3333, D1212, D1313, D2323), ), type=ORTHOTROPIC)


def calculate_orthotropic_parameters(E1, E2, E3, v12, v23, v13, G12, G13, G23):
    #to enble propper dividation the values need to be float
    E1 = float(E1)
    E2 = float(E2)
    E3 = float(E3)
    G12 = float(G12)
    G13 = float(G13)
    G23 = float(G23)

    v21 = E2/E1*v12
    v32 = E3/E2*v23
    v31 = E3/E1*v13
    print('E1={} E2={} E3={}'.format(E1, E2, E3))
    print('v12={} v23={} v13={}'.format(v12, v23, v13))
    print('v21={} v32={} v31={}'.format(v21, v32, v31))

    tau = 1/(1-v12*v21-v23*v32-v31*v13-2*v21*v32*v13)
    print('tau={}'.format(tau))

    D1111 = E1*(1-v23*v32)*tau
    D2222 = E2*(1-v13*v31)*tau
    D3333 = E3*(1-v12*v21)*tau

    D1122 = E1*(v21+v31*v23)*tau
    D1133 = E1*(v31+v21*v32)*tau
    D2233 = E2*(v32+v12*v31)*tau

    D1212 = G12
    D1313 = G13
    D2323 = G23
    print('D1111={} D2222={} D3333={} D1122={} D1133={} D2233={} D1212={} D1313={} D2323={}'.format(D1111, D2222, D3333,
    D1122, D1133, D2233, D1212, D1313, D2323))
    check_orthotropic_stability(D1111, D2222, D3333, D1122, D1133, D2233, D1212, D1313, D2323)
    return D1111, D2222, D3333, D1122, D1133, D2233, D1212, D1313, D2323


def check_orthotropic_stability(D1111, D2222, D3333, D1122, D1133, D2233, D1212, D1313, D2323):
    check = []
    check.append(D1111 > 0)
    check.append(D2222 > 0)
    check.append(D3333 > 0)
    check.append(D1212 > 0)
    check.append(D1313 > 0)
    check.append(D2323 > 0)
    check.append(abs(D1122) < np.sqrt(D1111*D2222))
    check.append(abs(D1133) < np.sqrt(D1111*D3333))
    check.append(abs(D2233) < np.sqrt(D2222*D3333))
    check.append(D1111*D2222*D3333+2*D1122*D1133*D2233-D2222*D1133**2-D1111*D2233**2-D3333*D1122**2 > 0)
    for element in check:
        if element == False:
            raise ValueError("orthotropic Stability not given check input calculateorthotropic_parameters")
    print('Orthotropic Stability Check succeeded')


def create_cyclic_material_model(model_name):
    '''Your Material model goes here, Currently implemented model by Fellner et al. (10.1109/EuroSimE.2014.6813788)'''
    m = mdb.models[model_name]
    m.Material(name = 'Copper')
    m.materials['Copper'].Elastic(table=((91800.0, 0.34),))
    m.materials['Copper'].Plastic(dataType=PARAMETERS, hardening=COMBINED,
        table=((105.0, 250000.0, 1900.0),))
    m.materials['Copper'].plastic.CyclicHardening(table=((104.999, 0),
        (105.0, 0.00984), (27.0, 0.52033), (10.0, 2.80569),
        (2.0, 5.5174),))

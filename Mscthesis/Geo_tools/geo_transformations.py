
import numpy as np


def transf4compdist(coord, mean_lat=0.71088):
    """Default location is spain latitude (in rad).
    Canarias: 0.49445665
    """

    coord = np.pi/180.*coord
    coord[:, 0] = coord[:, 0]*np.cos(mean_lat)
    return coord


def transf4compdist_inv(coord, mean_lat=0.71088):
    """Default location is spain latitude (in rad).
    Canarias: 0.49445665
    """

    coord = 180/np.pi*coord
    coord[:, 0] = coord[:, 0]/np.cos(mean_lat)
    return coord


def transf4compdist_spain(coord, loc_zone='peninsula', inverse=False):
    """"""

    if loc_zone == 'peninsula':
        mean_lat = 0.71088
    elif loc_zone == 'canarias':
        mean_lat = 0.49446
    elif loc_zone == 'ceutamelilla':
        mean_lat = 0.62134
    if not inverse:
        coord = transf4compdist(coord, mean_lat)
    else:
        coord = transf4compdist_inv(coord, mean_lat)

    return coord


def transf4compdist_spain_global(data, loc_vars, loc_zone_var, inverse=False):
    """"""

    loc_zones = ['peninsula', 'canarias', 'ceutamelilla']

    for loc_z in loc_zones:
        #aux = data[loc_vars][data[loc_zone_var].as_matrix() == loc_z]
        logi = (data[loc_zone_var] == loc_z).as_matrix()
        aux = data.loc[logi.reshape(-1), loc_vars]
        aux = transf4compdist_spain(aux.as_matrix(), loc_z, inverse)
        #data[loc_vars][logi] = aux
        data.loc[logi.reshape(-1), loc_vars] = aux
#
    return data


def transf4compdist_global_homo(data, loc_vars, inverse=False):
    """"""

    #aux = data[loc_vars][data[loc_zone_var].as_matrix() == loc_z]
    if not inverse:
        data.loc[:, loc_vars] = np.pi/180.*data.loc[:, loc_vars]
        lats = data.loc[:, loc_vars[1]]
        #data.loc[:, loc_vars[0]] = data.loc[:, loc_vars[0]]*np.cos(lats)
    else:
        lats = data.loc[:, loc_vars[1]]
        data.loc[:, loc_vars] = 180./np.pi*data.loc[:, loc_vars]
    #    data.loc[:, loc_vars[0]] = data.loc[:, loc_vars[0]]/np.cos(lats)

    return data

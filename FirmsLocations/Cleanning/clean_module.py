
"""
Clean module
============
This module contains all the functions required to format properly the data
from SABI dataset to be optimally used by this package.
The data is formated to the structure of folders that the package recognizes.

Folder structure ===========
============================
Parent_folder
    |-- Main
        |-- Servicios
    |-- Financial
        |-- year
            |-- Servicios
        |-- ...
    |-- Aggregated
        |-- Agg_by_cp
============================

"""

import numpy as np
from itertools import product
import datetime
import pandas as pd

from os.path import exists, join, isfile, isdir
import os
import time

from FirmsLocations.IO.aux_functions import parse_xlsx_sheet, write_dataframe
from FirmsLocations.Preprocess.preprocess_cols import categorize_cols
from FirmsLocations.Preprocess.comp_complementary_data import \
    average_position_by_aggvar, counting_type_by_aggvar
from FirmsLocations.Preprocess.preprocess_general import concat_empresas
from FirmsLocations.IO.parse_data import parse_empresas
from FirmsLocations.IO.preparation_module import prepare_concatinfo


############################## GLOBAL VARIABLES ###############################
###############################################################################
types_legend = ['Activo', 'Activo Circulante', 'Pasivo Fijo', 'Pasivo liquido',
                'Trabajadores', 'Valor agregado', 'Valor ventas']
types = ['Act', 'ActC', 'Pasfijo', 'Pasliq', 'Trab', 'Va', 'Vtas']
years = [2006, 2007, 2008, 2009, 2010, 2011, 2012]
years_key = ['06', '07', '08', '09', '10', '11', '12']

## Column info transformation
main_cols = ['Nom', 'nif', 'cnae', 'cp', 'localidad', 'ES-X', 'ES-Y',
             'apertura', 'cierre']
mapping_manu = {'localitat': 'localidad', 'ESX': 'ES-X', 'ESY': 'ES-Y'}
types_m = ['Act', 'ActC', 'Pasfijo', 'Pasliq', 'Treb', 'Va', 'Vdes']
check_xlsx = lambda f: f[-5:] == '.xlsx'


############################## GLOBAL VARIABLES ###############################
###############################################################################
def folder_structure(outpath):
    "Function which checks and creates the required folder structure."
    ## Ensure creation of needed folders
    if not exists(outpath):
        os.mkdir(outpath)
    if not exists(join(outpath, 'Main')):
        os.mkdir(join(outpath, 'Main'))
    if not exists(join(join(outpath, 'Main'), 'Servicios')):
        os.mkdir(join(join(outpath, 'Main'), 'Servicios'))
    if not exists(join(outpath, 'Financial')):
        os.mkdir(join(outpath, 'Financial'))
    folders = os.listdir(join(outpath, 'Financial'))
    folders_years = [str(int(e)) for e in years]
    for f in folders_years:
        if f not in folders:
            os.mkdir(join(join(outpath, 'Financial'), f))
        os.mkdir(join(join(join(outpath, 'Financial'), f), 'Servicios'))
    return folders_years


def get_financial_cols():
    "Get the names of the financial columns."
    ## Creation of the Financial cols
    aux = []
    for i in range(len(years_key)):
        aux.append([''.join(e) for e in product([years_key[i]], types)])
    Financial_cols = aux
    return Financial_cols


def parse_write_manufactures(inpath, outpath, extension, financial_cols,
                             folders_years):
    ""
    ## Parse manufactures
    # Start traking
    t0 = time.time()
    print "Start parsing manufacturas."
    # parse manufacturas
    manufacturas = parse_xlsx_sheet(join(inpath, 'Manufactures.xlsx'))
    # Rename columns
    cols = manufacturas.columns
    newcolnames = clean_colnames_manu(cols)
    manufacturas.columns = newcolnames
    # Compute extra variables
    extra = compute_extra_cols(manufacturas)
    manufacturas = pd.concat([manufacturas, extra], axis=1)
    # Correct coordinates
    coords = ['ES-X', 'ES-Y']
    manufacturas[coords] = reformat_coordinates_manu(manufacturas, coords)
    # Categorize cols
    manufacturas = categorize_cols(manufacturas)
    # Separate and save
    name = 'Manufactures.xlsx'
    write_dataframe(manufacturas[main_cols], name,
                    join(outpath, 'Main'), extension)
    # Tracking task
    print "Manufacturas main lasted %f seconds." % (time.time()-t0)
    for i in range(len(financial_cols)):
        t0 = time.time()
        y = folders_years[i]
        write_dataframe(manufacturas[financial_cols[i]], name,
                        join(join(outpath, 'Financial'), y), extension)
        print "Manufacturas year %s lasted %f seconds." % (y, time.time()-t0)
    del manufacturas


def parse_write_servicios(inpath, outpath, extension, financial_cols,
                          folders_years):
    ""
    ## 1. Parse servicios
    t0 = time.time()
    onlyfiles = [f for f in os.listdir(join(inpath, 'Servicios'))
                 if isfile(join(join(inpath, 'Servicios'), f))
                 and check_xlsx(f)]
    for f in onlyfiles:
        # parse servicios
        servicios = parse_xlsx_sheet(join(join(inpath, 'Servicios'), f))
        # Rename columns
        cols = servicios.columns
        newcolnames = clean_colnames_servi(cols)
        servicios.columns = newcolnames
        # Compute extra variables
        apertura = obtain_open_aperture_date(servicios)
        servicios['apertura'] = apertura
        servicios = compute_close_date_servicios(servicios)
        ## Categorize cols
        servicios = categorize_cols(servicios)
        # Separate and save
        write_dataframe(servicios[main_cols], f,
                        join(join(outpath, 'Main'), 'Servicios'), extension)
        print "Compute %s." % f
        print "Servicios main lasted %f seconds." % (time.time()-t0)
        # Write servicios
        path_fin = join(outpath, 'Financial')
        for i in range(len(financial_cols)):
            t0 = time.time()
            y = folders_years[i]
            write_dataframe(servicios[financial_cols[i]], f,
                            join(join(path_fin, y), 'Servicios'), extension)
            print "Servicios year %s lasted %f seconds." % (y, time.time()-t0)


############################# AUXILIAR FUNCTIONS ##############################
###############################################################################
def aggregate_by_mainvar(parentfolder, agg_var, loc_vars, type_var=None,
                         ifwrite=True, transformation=lambda x: x):
    """Function to aggregate variables by the selected variable considering a
    properly structured data.
    """

    ## Parse with class the structure and return the data
    parser = Firms_Parser(cleaned=True, logfile=join(parentfolder, 'log.log'))
    empresas = parser.parse(parentfolder, year=2006)
    # Transformation
    empresas = transformation(empresas)
    ## Aggregation
    positions = average_position_by_cp(empresas, agg_var, loc_vars)
    if type_var is not None:
        types = counting_type_by_cp(empresas, agg_var, type_var)
        df = pd.concat([positions, types], axis=1)
        cols = {'types': list(types.columns)}
        cols['positions'] = list(positions.columns)
    else:
        df = positions
        cols = {'positions': list(positions.columns)}

    ## Write dataframe
    if ifwrite:
        aggfolder = 'Agg_by_'+agg_var
        if not exists(join(parentfolder, 'Aggregated')):
            os.mkdir(join(parentfolder, 'Aggregated'))
        if not exists(join(join(parentfolder, 'Aggregated'), aggfolder)):
            os.mkdir(join(join(parentfolder, 'Aggregated'), aggfolder))

        write_dataframe(df, 'table_agg',
                        join(join(parentfolder, 'Aggregated'), aggfolder),
                        'csv')
    return df, cols


def aux_transformation(df, lvl):
    "Auxiliar transformation for formatting aggregate data."
    # categorize
    df = categorize_cols(df)
    # Change the cnae code
    from Mscthesis.Retrieve.cnae_utils import transform_cnae_col
    df['cnae'] = transform_cnae_col(df['cnae'], lvl)
    return df


def clean(inpath, outpath, extension='csv'):
    """Do the cleaning data from the raw initial data. It formats the data to a
    folder structure in which it is separated the main information of a company
    with the Financial information in order to save memory and read unnecessary
    information for some tasks.
    """
    ## 0. Ensure creation of needed folders
    if not exists(outpath):
        os.mkdir(outpath)
    if not exists(join(outpath, 'Main')):
        os.mkdir(join(outpath, 'Main'))
    if not exists(join(join(outpath, 'Main'), 'Servicios')):
        os.mkdir(join(join(outpath, 'Main'), 'Servicios'))
    if not exists(join(outpath, 'Financial')):
        os.mkdir(join(outpath, 'Financial'))
    folders = os.listdir(join(outpath, 'Financial'))
    folders_years = [str(int(e)) for e in years]
    for f in folders_years:
        if f not in folders:
            os.mkdir(join(join(outpath, 'Financial'), f))
        os.mkdir(join(join(join(outpath, 'Financial'), f), 'Servicios'))
    ## Creation of the Financial cols
    aux = []
    for i in range(len(years_key)):
        aux.append([''.join(e) for e in product([years_key[i]], types)])
    Financial_cols = aux

    ## 1. Parse manufactures
    # Start traking
    t0 = time.time()
    print "Start parsing manufacturas."
    # parse manufacturas
    manufacturas = parse_xlsx_sheet(join(inpath, 'Manufactures.xlsx'))
    # Rename columns
    cols = manufacturas.columns
    newcolnames = clean_colnames_manu(cols)
    manufacturas.columns = newcolnames
    # Compute extra variables
    extra = compute_extra_cols(manufacturas)
    manufacturas = pd.concat([manufacturas, extra], axis=1)
    # Correct coordinates
    coords = ['ES-X', 'ES-Y']
    manufacturas[coords] = reformat_coordinates_manu(manufacturas, coords)
    # Categorize cols
    manufacturas = categorize_cols(manufacturas)
    # Separate and save
    name = 'Manufactures.xlsx'
    write_dataframe(manufacturas[main_cols], name,
                    join(outpath, 'Main'), extension)
    # Tracking task
    print "Manufacturas main lasted %f seconds." % (time.time()-t0)
    for i in range(len(Financial_cols)):
        t0 = time.time()
        y = folders_years[i]
        write_dataframe(manufacturas[Financial_cols[i]], name,
                        join(join(outpath, 'Financial'), y), extension)
        print "Manufacturas year %s lasted %f seconds." % (y, time.time()-t0)
    del manufacturas

    ## 1. Parse servicios
    t0 = time.time()
    onlyfiles = [f for f in os.listdir(join(inpath, 'Servicios'))
                 if isfile(join(join(inpath, 'Servicios'), f))
                 and check_xlsx(f)]
    for f in onlyfiles:
        # parse servicios
        servicios = parse_xlsx_sheet(join(join(inpath, 'Servicios'), f))
        # Rename columns
        cols = servicios.columns
        newcolnames = clean_colnames_servi(cols)
        servicios.columns = newcolnames
        # Compute extra variables
        apertura = obtain_open_aperture_date(servicios)
        servicios['apertura'] = apertura
        servicios = compute_close_date_servicios(servicios)
        ## Categorize cols
        servicios = categorize_cols(servicios)
        # Separate and save
        write_dataframe(servicios[main_cols], f,
                        join(join(outpath, 'Main'), 'Servicios'), extension)
        print "Compute %s." % f
        print "Servicios main lasted %f seconds." % (time.time()-t0)
        # Write servicios
        path_fin = join(outpath, 'Financial')
        for i in range(len(Financial_cols)):
            t0 = time.time()
            y = folders_years[i]
            write_dataframe(servicios[Financial_cols[i]], f,
                            join(join(path_fin, y), 'Servicios'), extension)
            print "Servicios year %s lasted %f seconds." % (y, time.time()-t0)


def clean_colnames_manu(cols):
    "Clean names of the manufactures."
    # Format properly
    cols = [e.strip() for e in cols]
    # Replace the Financial variables
    cols_f = ['y'+''.join(e) for e in product(years_key, types_m)]
    cols_f_g = [''.join(e) for e in product(years_key, types)]
    replace_f = dict(zip(cols_f, cols_f_g))
    cols = replace_colnames(cols, replace_f)
    # Replace the main
    cols = replace_colnames(cols, mapping_manu)
    return cols


def clean_colnames_servi(cols):
    "Clean names of the servicios."
    # Format properly
    cols = [e.strip() for e in cols]
    return cols


def reformat_coordinates_manu(df, coord_var):
    """Divide the coordinates for 10^6 in order to get the correct
    dimensionality."""
    aux = df[coord_var].as_matrix()/float(10**6)
    return aux


def compute_extra_cols(df):
    ## Compute aperture date
    bool_null = np.array(df['constituc'].isnull())
    aux1 = obtain_open_aperture_date(df.loc[bool_null, :])
    f = lambda x: datetime.date(int(x), 1, 1)
    aux2 = np.zeros(np.logical_not(bool_null).sum()).astype(datetime.date)
    idxs = np.nonzero(np.logical_not(bool_null))[0]
    for i in xrange(idxs.shape[0]):
        aux2[i] = f(int(df.loc[idxs[i], 'constituc']))
    aux = pd.DataFrame(columns=['apertura'], index=df.index)
    aux.loc[bool_null, 'apertura'] = aux1
    aux.loc[np.logical_not(bool_null), 'apertura'] = aux2
    ## Compute close date
    bool_act = np.array(df.loc[:, 'estat'] == 'Activa')
    bool_2012 = np.array(df.loc[:, 'tancament']) == 2012
    cierre = np.zeros(bool_2012.shape)
    cierre = np.array(df.loc[:, 'tancament'])
    cierre[np.logical_and(bool_act, bool_2012)] = 2013
    cierre_aux = np.zeros(cierre.shape[0]).astype(datetime.date)
    for i in xrange(cierre.shape[0]):
        cierre_aux[i] = f(cierre[i])
    cierre = pd.DataFrame(cierre_aux, columns=['cierre'], index=aux.index)
    ## Concat
    extras = pd.concat([aux, cierre], axis=1)
    return extras


def compute_close_date_servicios(servicios):
    "Compute the close date."
    f = lambda x: datetime.date(x.year, x.month, x.day)
    cierre = np.zeros(servicios.shape[0]).astype(datetime.date)
    bool_c = np.array(servicios['cierre'].isnull())
    bool_nc = np.logical_not(bool_c)
    cierre2 = servicios.loc[bool_nc, 'cierre'].astype(datetime.date).apply(f)
    cierre[bool_c] = obtain_close_date(servicios.loc[bool_c, :])
    cierre[bool_nc] = np.array(cierre2)

    servicios['cierre'] = cierre
    return servicios


def replace_colnames(cols, replaces):
    "Replace the names keeping the order in the list of colnames."
    for c in cols:
        if c in replaces.keys():
            cols[cols.index(c)] = replaces[c]
    return cols


def obtain_open_aperture_date(df):
    "Obtain the date of aperture of the each company."

    m_y = len(years)
    ## Obtain bool arrays
    bool_m = np.zeros((df.shape[0], m_y)).astype(bool)
    for i in range(m_y):
        bool_m[:, i] = check_year_open(df, years[i])

    ## Obtain date
    dates = np.zeros(bool_m.shape[0])
    for i in range(m_y):
        logi = bool_m[:, i]
        dates[np.logical_and(dates == 0, logi)] = i+1
    ## Format dates
    dates = dates + years[0]-1
    dates = dates.astype(int)
    aux = np.zeros(dates.shape).astype(datetime.date)
    for i in range(aux.shape[0]):
        aux[i] = datetime.date(int(dates[i]), 1, 1)
    dates = aux
    return dates


def obtain_close_date(df):
    "Obtain close date"
    m_y = len(years)
    ## Obtain bool arrays
    bool_m = np.zeros((df.shape[0], m_y)).astype(bool)
    for i in range(m_y):
        bool_m[:, m_y-1-i] = check_year_open(df, years[i])

    ## Obtain date
    dates = np.ones(bool_m.shape[0])*m_y
    for i in range(m_y):
        logi = bool_m[:, i]
        dates[np.logical_and(dates == m_y, logi)] = m_y-i-1
    dates = m_y - dates

    ## Format dates
    dates = dates + years[0]-1
    dates = dates.astype(int)
    aux = np.zeros(dates.shape).astype(datetime.date)
    for i in range(aux.shape[0]):
        aux[i] = datetime.datetime(int(dates[i]), 12, 31)
    dates = aux
    return dates


def check_year_open(df, year):
    """Function to check if there is any variables not none to check if there
    was opened the selected year.
    """
    i = years.index(year)
    year_key = [years_key[i]]
    comb = product(year_key, types)
    comb = [''.join(e) for e in comb]

    logis = np.logical_not(df[comb].isnull().as_matrix())
    m = logis.shape[1]

    logi = np.zeros(logis.shape[0]).astype(bool)
    for i in range(m):
        logi = np.logical_or(logi, logis[:, i])
    return logi

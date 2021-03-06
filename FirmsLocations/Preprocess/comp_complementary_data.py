
"""
This module contains functions which helps in the computation of extra and
complementary data needed and computed from the known data.

TODO:
----
- Other functions not only count.

"""

# Counting process of each type


import numpy as np
import pandas as pd


###############################################################################
############################ Main functions counts ############################
###############################################################################
def compute_aggregate_counts(df, agg_var, type_vars, reindices):
    ## Compute the tables
    agg_values = list(np.unique(df[agg_var]))
    tables = {}
    axis = {}
    for col in type_vars:
        n_vals = df[col].unique().shape[0]
        aux = np.zeros((len(agg_values), n_vals, reindices.shape[1]))
        for i in range(reindices.shape[1]):
            # The type values
            aux_df = df.loc[:, [agg_var]+type_vars]
            aux2 = aux_df[type_vars].reindex(reindices[:, i]).as_matrix()
            aux_df[type_vars] = aux2
            table, cols = counting_type_by_aggvar(aux_df, agg_var, type_vars)
            aux[:, :, i] = table.as_matrix()

        tables[col] = aux
        axis[col] = {'rows': agg_values, 'columns': cols}

    return tables, axis


###############################################################################
############################ Auxiliar counts by var ###########################
###############################################################################
def aggregate_by_var(df, agg_var, loc_vars, type_vars=None):
    """Function to aggregate variables by the selected variable considering a
    properly structured data.
    """
    ## Aggregation
    positions = average_position_by_aggvar(df, agg_var, loc_vars)
    if type_vars is not None:
        types = aggregate_by_typevar(df, agg_var, type_vars)
        df_agg, cols = pd.concat([positions, types], axis=1)
        cols = {'types': cols}
        cols['positions'] = list(positions.columns)
    else:
        df_agg = positions
        cols = {'positions': list(positions.columns)}

    return df_agg, cols


def aggregate_by_typevar(df, agg_var, type_vars):
    "Function to aggregate only by type_var."
    type_vars = [type_vars] if type(type_vars) != list else type_vars
    df_agg = counting_type_by_aggvar(df, agg_var, type_vars)
    cols = list(df.columns)
    return df_agg, cols


def average_position_by_aggvar(df, aggvar, loc_vars):
    "Compute the pivot table to assign to cp a geographic coordinates."
    table = df.pivot_table(values=loc_vars, rows=aggvar, aggfunc=np.mean)
    return table


def average_position_by_aggarr(locs, agg_arr):
    "Compute the pivot table to assign to cp a geographic coordinates."
    loc_vars, aggvar = ['x', 'y'], 'agg'
    df = [pd.DataFrame(locs, columns=loc_vars),
          pd.DataFrame(agg_arr, columns=[aggvar])]
    df = pd.concat(df, axis=1)
    table = df.pivot_table(values=loc_vars, rows=aggvar, aggfunc=np.mean)
    return table


def counting_type_by_aggvar(df, aggvar, type_vars):
    "Compute the counting of types by "
    table = df[[aggvar] + type_vars].pivot_table(rows=aggvar, cols=type_vars,
                                                 aggfunc='count')
    table = table.fillna(value=0)
    cols = table.columns.get_level_values(1).unique()
    m = len(cols)
    table = table.loc[:, table.columns[:m]]
    table.columns = cols
    return table, cols


def std_type_by_aggvar(df, aggvar, loc_vars):
    "Compute the counting of types by "
    table = df.pivot_table(rows=aggvar, values=loc_vars,
                           aggfunc=np.std)
    table = table.fillna(value=0)
    table.columns = ['STD-X', 'STD-Y']
    return table


def mean_type_by_aggvar(df, aggvar, loc_vars):
    "Compute the counting of types by "
    table = df.pivot_table(rows=aggvar, values=loc_vars,
                           aggfunc=np.mean)
    table.columns = ['MEAN-X', 'MEAN-Y']
    table = table.fillna(value=0)
    return table


###############################################################################
############################# Auxiliar grid counts ############################
###############################################################################
def computation_aggregate_collapse_i(type_arr, n_vals):
    "Counting the types of each one."
    values = np.unique(type_arr[:, 0])
    counts_i = np.zeros(n_vals[0])
    for j in range(values.shape[0]):
        counts_i[values[j]] = (type_arr == values[j]).sum()
    return counts_i


###############################################################################
########################### Cond_agg and info_ret #############################
###############################################################################
def create_info_ret(df, typevars, params=None):
    "Creation of the information for retrieve neighs."
    ## Needed vars
    n = df.shape[0]
    typevars['info_ret'] = ['info_i', 'info_agg']
    ## Assignation
    if type(params) == list:
        df['info_i'] = params[0]
        df['info_agg'] = params[1]
    else:
        df['info_i'] = 2.5*np.ones(n)
        df['info_agg'] = (3*np.ones(n)).astype(int)
    return df, typevars


def create_cond_agg(df, typevars, params=None):
    "Creation of the conditional aggregation for retrieve aggregate data."
    ## Needed vars
    n = df.shape[0]
    typevars['cond_agg'] = 'cond_agg'
    ## Assignation
    if type(params) == np.ndarray:
        df['cond_agg'] = params
    else:
        df['cond_agg'] = np.ones(n).astype(bool)
    return df, typevars

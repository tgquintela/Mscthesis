
import numpy as np
from pySpatialTools.Geo_tools import general_projection
from pythonUtils.Logger import Logger

#### 1. Prepare empresas
from Mscthesis.IO import Firms_Parser
from Mscthesis.Preprocess import Firms_Preprocessor

parentpath = '/home/tono/mscthesis/code/Data/pruebas_clean'
logfile = '/home/tono/mscthesis/code/Data/Outputs/Logs/log_clean.log'


## Parse
logger = Logger(logfile)
parser = Firms_Parser(logger)
empresas, typevars = parser.parse(parentpath, year=2006)

## Preprocess
preprocess = Firms_Preprocessor(typevars, logger)
empresas = preprocess.preprocess(empresas)


### Prepare municipios
from Mscthesis.IO import Municipios_Parser
from pySpatialTools.Interpolation import general_density_assignation
from pySpatialTools.Retrieve import KRetriever

from pySpatialTools.Interpolation.density_assignation_process import \
    DensityAssign_Process
from pySpatialTools.Interpolation.density_utils import population_assignation_f

#from Mscthesis.Preprocess.comp_complementary_data import population_assignation_f, compute_population_data

# municipios file
mpiosfile = '/home/tono/mscthesis/code/Data/municipios_data/municipios-espana_2014_complete.csv'

mparser = Municipios_Parser(None)
data, typ = mparser.parse(mpiosfile)


params = {'f_weights': 'exponential', 'params_w': {'max_r': 10.}, 'f_dens': population_assignation_f, 'params_d': {}}
params_proj = {'method': 'ellipsoidal', 'inverse': False, 'radians': False}


data.loc[:, typ['loc_vars']] = general_projection(data, typ['loc_vars'], **params_proj)
locs = empresas[typevars['loc_vars']]


retriever = KRetriever
info_ret = np.ones(locs.shape[0]).astype(int)*3

## ProcessClass
pop_assign = DensityAssign_Process(logger, retriever)
m = pop_assign.compute_density(locs, data, typ, info_ret, params)

###########################################


## TODO: Join function
## TODO: Discrete vars, continious vars?
empresas['population_idx'] = m
typevars['pop_var'] = 'population_idx'
########################################


#### 2. Compute model descriptors
from pySpatialTools.IO import create_reindices
from Mscthesis.Preprocess import create_info_ret, create_cond_agg
from pySpatialTools.Preprocess import Aggregator
from pySpatialTools.Retrieve import CircRetriever, Neighbourhood, KRetriever

#compute_population_data(locs, pop, popvars, retriever, info_ret, params)


## Define aggregator
agg = Aggregator(typevars=typevars)

## Define permuts
permuts = 2
reindices = create_reindices(empresas.shape[0], permuts)

## Define info retriever and conditional aggregator
empresas, typevars = create_info_ret(empresas, typevars)
empresas, typevars = create_cond_agg(empresas, typevars, np.random.randint(0, 2, empresas.shape[0]).astype(bool))


### Aplying model
from pySpatialTools.Descriptor_Models import Pjensen, ModelProcess, Countdescriptor

## Define descriptormodel
descriptormodel = Countdescriptor(empresas, typevars)

## Define retriever (Neigh has to know typevars)  (TODO: define bool_var)
retriever = CircRetriever(empresas[typevars['loc_vars']].as_matrix())
aggretriever = KRetriever

Neigh = Neighbourhood(retriever, typevars, empresas, reindices, aggretriever, funct=descriptormodel.compute_aggcharacterizers)
del locs


## Define process
modelprocess = ModelProcess(logger, Neigh, descriptormodel, typevars=typevars,
                            lim_rows=5000, proc_name='Test')

count_matrix = modelprocess.compute_matrix(empresas, reindices)

descriptormodel = Pjensen(empresas, typevars)
modelprocess = ModelProcess(logger, Neigh, descriptormodel, typevars=typevars,
                            lim_rows=5000, proc_name='Test')

pjensen_matrix = modelprocess.compute_matrix(empresas, reindices)
corrs = modelprocess.compute_net(empresas,reindices)
net = modelprocess.filter_with_random_nets(corrs, 0.03)


### 3. Recommmendation
from pySpatialTools.Recommender import PjensenRecommender
from pySpatialTools.Recommender import SupervisedRmodel
from sklearn.cross_validation import KFold
from pySpatialTools.Interpolation.density_assignation import \
    general_density_assignation, from_distance_to_weights, compute_measure_i

################### Pjensen ###################
# definition of parameters
feat_arr = np.array(empresas[typevars['feat_vars']])

# Instantiation of the class
recommender = PjensenRecommender()
# Making the predictionmatrix
Q = recommender.compute_quality(net, count_matrix, feat_arr, 0)
Qs, idxs = recommender.compute_kbest_type(net, count_matrix, feat_arr, 5)

################## Supervised #################
# definition of parameters
feat_arr = np.array(empresas[typevars['feat_vars']])

# Instantiation of the class
recommender = SupervisedRmodel(modelcl, pars_model, cv, pars_cv)
model, measure = recommender.fit_model(pjensen_matrix, feat_arr)
Q = recommender.compute_quality(pjensen_matrix)

################## Supervised #################
# definition of parameters
feat_arr = np.array(empresas[typevars['feat_vars']])
weights_f = lambda 

general_density_assignation(locs, retriever, info_ret, values, f_weights,
                                params_w, f_dens, params_d)

# Instantiation of the class
recommender = NeighRecommender(retriever, weights_f)





import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
from shapely import geometry
import libpysal

# read the data
pop = gpd.read_file('your file directory of population grid cell')
green = gpd.read_file('your file directory of green space')
boundry= gpd.read_file('your file directory of city administrative boundry')

# get the road network of city
place_name = "Philadelphia, United States" # you could change the name of the city 
G = ox.graph_from_place(place_name, network_type='all', buffer_dist = 1600) # also choose different network type, like walking, driving
G_proj = ox.project_graph(G,to_crs='epsg:32618') # choose a suitable CRS for your city
G_nodes_proj, G_edges_proj = ox.graph_to_gdfs(G_proj, nodes=True, edges=True)
edges = G_edges_proj.unary_union


# preprocessing green space data
def green_data_prepocessing(green,boundry,distance_threshold):
    """
    green space data preprocessing:
    green is the green space geodataframe;
    boundry is the city's administrative boundry;
    buffer is added around the green space to do the intersection with road network, usually 20m
    """
     
    # transfer the CRS
    boundry = boundry.to_crs(epsg = 32618) 
    green =  green.to_crs(epsg = 32618)
    
    # clip green space within the buffered city boundry
    # first to add a buffer around the boundry to ensure people 
    # live around the edge of the boundry could access the green space outside the city but still within distance threshold
    boundry_buffer = boundry.buffer(distance_threshold)
    green_clip = green.clip(boundry_buffer,keep_geom_type=False)
    
    # merge the overlap green space into one polygon
    s_ = gpd.GeoDataFrame(geometry=[green_clip.unary_union]).explode(
        index_parts=False).reset_index(drop=True).set_crs(epsg = 32618)
    s_ = gpd.sjoin(s_, green_clip, how='left').drop(columns=['index_right'])
    green_dis = s_.dissolve(s_.index, aggfunc='first')
    # reset the index 
    green_dis =green_dis.reset_index(drop=True)
    #create the buffer of green space, ususally 20m, equals the width of roads
    green_dis['buffer_20m'] = green_dis['geometry'].buffer(20)
    
    # define the green areas that overlap with each other within 20m as the same component
    W = libpysal.weights.fuzzy_contiguity(green_dis['buffer_20m'])
    green_dis['green_components']= W.component_labels
    green_space = green_dis.dissolve('green_components')
    
    #create the centroid of the green space
    green_space['centroids'] = green_space['geometry'].centroid
    #calculate the area of the green space
    green_space['area'] = green_space['geometry'].area
    
    # select area >400m2
    green_space = green_space[green_space['area'] > 400]
    green_space = green_space.reset_index(drop=True)

    return green_space



# choose the different models of fake gate
def fake_gate(green_space, destination = 'centroids'):
   """
   green space is the green space dataset after preprocessing
   destination represents the fake gate of green space,
   'centroids' means using centroids of green space as access point.
   'Entrance' means using the intersections points between the road network and boundry of green space
   """
    entrance = []  
    # use centroid of green space 
    if destination == 'centroids':
        green_access = green_space[['centroids','area']]
        green_access.rename(columns = {'centroids': 'geometry'}, inplace = True)
        green_access['park_id'] = list(range(len(green_space)))
        
    
    # use the intersection points: the road network and buffered green space polygon
    else destination == 'Entrance':
        # add the buffer of 20m for each components
        green_space['buffer'] = green_space['geometry'].buffer(20)
        for i in range(len(green_space)):
            green_area = green_space.loc[i,'geometry'].area
            intersection = green_space['buffer'][i].boundary.intersection(edges)
            try:
                for point in intersection:
                    dic = {'geometry': point, 'area': green_area, 'park_id': i}
                    entrance.append(dic)
            except: continue
    green_access = gpd.GeoDataFrame(entrance)
    
    # if the distance of two fake entrances is less than 50m, then keep the first entrance
    green_access['buffer'] = green_access['geometry'].buffer(25)
    w_e = libpysal.weights.fuzzy_contiguity(green_access['buffer'])
    green_access['entrance_components']= w_e.component_labels
    
    # Delete duplicate rows based on specific columns 
    green_access =  green_access.drop_duplicates(subset=["entrance_components"], keep='first')
    green_access = green_access.reset_index(drop=True)
    
    return green_access


# preprocessing population data
def population_data_prepocessing(pop,boundry,distance_threshold):
    
    """
    population data prepocessing:
    pop is the population geodataframe;
    boundry is the city's administrative boundry; 
    distance_threshold is the walking or driving distance; 
    
    """
    
    # transfer the CRS
    boundry = boundry.to_crs(epsg = 32618) 
    pop =  pop.to_crs(epsg = 32618)
    
    # clip population within the city boundry
    pop_clip = pop.clip(boundry,keep_geom_type=False)

    # remove grid cell if its population is less than 10 in case of extreme value
    pop_remove = pop_clip[(pop_clip['PoP2015_Number'] < 10) == False]
    pop_remove['area'] = pop_remove['geometry'].area
    
    # remove boundry population if the area of grid cell is less than half of the regular area
    pop_remove_bound = pop_remove[pop_remove['area'] > pop_remove['area'].max()*0.5]
    
    #create the centroid of the population grid cell
    pop_remove_bound['centroids'] = pop_remove_bound['geometry'].centroid
    #create the buffer of each grid cell, which equals the distance threshold
    pop_remove_bound['buffer'] = pop_remove_bound['geometry'].buffer(distance_threshold)
    # reset the index 
    pop_remove_bound  = pop_remove_bound.reset_index(drop=True)
    
    return pop_remove_bound


def get_the_index_within_dist(pop_clip,green_access):
    
    """
    pop_clip is the population grid cell data after preprocessing step;
    green_access is the fake gate;
    this step is to create a dataframe includes pairs of population grid cell and green space
    whose euclidian distance is smaller than distance threshold
    
    """
  
    k= []
    for i in range(len(pop_clip)):
        for j in range(len(green_access)):
            if green_access['geometry'][j].within(pop_clip['buffer'][i]):
            #distance. = pop_clip['centroids'][i].distance(access_point['geometry'][j])
                index = {'pop_index': i, 'green_index': j,
                         'green_area': green_access['area'][j],
                         'park_id': green_access['park_id'][j],
                         'pop_num': pop_clip.loc[i, 'PoP2015_Number']}
                k.append(index)
    df_index = pd.DataFrame(k)
    return df_index



def origin_node(df_index,pop_clip):
    """
    df_index is the dataframe includes pairs of population grid cell and green space whose euclidian distance is smaller than distance threshold
    pop_clip is the population grid cell data after preprocessing step;
   
    """
    
    # get the unique value of pop index
    pop_unique = df_index['pop_index'].unique()
    
    orig_id = []
    # get the nearest node id of each centroid of population grid cell
    for i in range(len(pop_unique)):
        pop_index = pop_unique[i]
        orig_node = ox.distance.nearest_nodes(G_proj,pop_clip.loc[pop_index,'centroids'].x,
                                                pop_clip.loc[pop_index,'centroids'].y)
        dic = {'pop_index':pop_unique[i],'orig_node':orig_node}
        orig_id.append(dic)
    orig_id_df = pd.DataFrame(orig_id)
    return orig_id_df


def target_node(df_index, green_access):
    # get the unique value of green index
    green_unique = df_index['green_index'].unique()
    target_id = []
    # get the nearest node id of each green space
    
    for i in range(len(green_unique)):
        green_index = green_unique[i]
        target_node = ox.distance.nearest_nodes(G_proj,green_access.loc[green_index,'geometry'].x,
                                                green_access.loc[green_index,'geometry'].y)
        dic = {'green_index':green_unique[i],'target_node': target_node}
        target_id.append(dic)
    target_id_df = pd.DataFrame(target_id)
    return target_id_df


def OD_Matrix(merge):
    """
    get the real distance between each pair of population grid cell and green space 
    """
    distance = []
    for i in range(len(merge)):
        try: 
            orig_node = merge.loc[i, 'orig_node']
            target_node = merge.loc[i, 'target_node']
            dist = nx.shortest_path_length(G_proj, source=orig_node, 
                                           target=target_node, weight='length')
            distance.append(dist)
        except:
            distance.append(np.nan)
    merge['distance'] = distance
    return merge


# this function is for the entrance model
# if the entrances are belong to the same park, I will choose the nearest entrance. 
def neareat_entrance(OD_mile): # OD_mile is the OD Matrix after selection, e.g real_distance < 1km
    unique = OD_mile['pop_index'].unique()
    OD_nearest_E = []
    for i in a:
        df = OD_mile.loc[OD_mile['pop_index'] == i]
        df1 = df.groupby('park_id').min('distance')
        for j in df1.index:
            dic = {'pop_index': i,'park_id': j,'distance':df1.loc[j,'distance'],
              'green_area': df1.loc[j,'green_area'], 'pop_num':df1.loc[j,'pop_num']}
            OD_nearest_E.append(dic)
    OD_nearest_E = pd.DataFrame(OD_nearest_E)
    return OD_nearest_E


# modified two-step floating catchment area model

def M2tsfca (OD_nearest_E):
    
    # use gussian distribution: let v= 923325, then the weight for 800m is 0.5
    # add a column of weight: apply the decay function on distance
    OD_nearest_E['weight'] = np.exp(-(OD_nearest_E['distance'])**2/923325).astype(float) 
    OD_nearest_E['weighted_pop'] = OD_nearest_E['weight'] * OD_nearest_E['pop_num']

    # get the sum of weighted population each green space has to serve.
    s_w_p = pd.DataFrame(OD_nearest_E.groupby('park_id').sum('weighted_pop')['weighted_pop'])
    # delete other columns, because they are useless after groupby
    s_w_p = s_w_p.rename({'weighted_pop':'sum_weighted_pop'},axis = 1)
    middle = pd.merge(OD_nearest_E,s_w_p, how = 'left', on = 'park_id' )
    # calculate the supply-demand ratio for each green space
    middle['green_supply'] = middle['green_area']/middle['sum_weighted_pop']
    
    # caculate the accessbility score for each green space that each population grid cell could reach
    middle['access_score'] = middle['weight'] * middle['green_supply']
    # add the scores for each population grid cell
    pop_score_df = pd.DataFrame(middle.groupby('pop_index').sum('access_score')['access_score'])

    # calculate the mean distance of all the green space each population grid cell could reach
    mean_dist = middle.groupby('pop_index').mean('distance')['distance']
    pop_score_df['mean_dist'] = mean_dist

    # calculate the mean area of all the green space each population grid cell could reach
    mean_area = middle.groupby('pop_index').mean('green_area')['green_area']
    pop_score_df['mean_area'] = mean_area

    # calculate the mean supply_demand ratio of all the green space each population grid cell could reach
    mean_supply = middle.groupby('pop_index').mean('green_supply')['green_supply']
    pop_score_df['mean_supply'] = mean_supply

    return pop_score_df


    


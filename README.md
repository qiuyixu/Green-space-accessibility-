# Urban green space accessibility 

Python script to calculate urban green space (UGS) accessibility using modified 2SFCA model.

The main file include 'code_for_a_single_city' and 'code_for_a_set_of_cities'. The process in each file is similar, includes the data preprocessing for green space and population; calculation of the OD Matrix; Using  M2SFCA model to get the accessibility scores. Differences are (1) the latter uses green space,boundry,network extracted from OSM; (2) the latter could get the accessibility score for a set of cities relatively automatically. 

## **Data and packages needed**
**Packages:** geopandas, networkx, osmnx, numpy, pandas, libpysal<br />
**Data needed for 'code_for_a_set_of_cities':** city boundary, green space, road network data sets could be fetched automatically from OSM. You need to create your own population grid cell.<br />
**Data needed for 'code_for_a_single_city':** you could feed in your own urban boundary, green space, population data according to different needs.

## **Assumptions**
**Catchment size:** 300m, 600m, 1000m<br />
**Travel mode:** 'walking', you could also choose 'driving' according to catchment size.<br />
**Edge effect:** Set a buffer that equals the catchment size around the boundary of the city to clip the green space data. Meanwhile set a buffer that equals 2 times of catchment size around the boundary of the study area to clip the population data.  <br />
**Green space:** Define the green spaces with a 20 m buffer overlap with each other as the same component. In addition, select area > 0.04ha<br />
**Definition of destination:** Use the simulated entrance of UGSs as destination, which are defined as the intersection points of the road network and UGS with buffer. The buffer distance we set is 20 m, usually equals the width of the road network which extends the boundary of UGSs to connect with the road network. Besides, there could be multiple road lines along with each other (usually two walking roads). To solve this problem, if the distance between two intersection points that belong to the same UGS is less than 50m, we chose the first one. <br />

## **Functions**
Several functions were defined to make the whole process replicapable. 
| Function  | Description| Input | 
| ------------- | ------------- |---------|
|green_data_prepocessing |Function to preprocess the green space data. The output is set of fake entrances of UGS based on the chosen destination mode. |**green**: green space geodataframe <br /> **boundry**: the city's administrative boundry or urban boundary <br /> **buffer**: distance added around the green space to do the intersection with road network, usually 20m <br />**destination**: the fake gate of green space, 'centroids' means using centroids of green space as access point. 'Entrance' means using the selected intersections points between the road network and buffered UGS boundary. | 
|population_data_prepocessing|Function to preprocess the population data. The output is population grid cell clipped by the buffered boundary of the city.| **pop**: population geodataframe<br /> **boundry**: city's administrative or urban boundry <br />**distance_threshold**: catchment size, 300m, 600m, 1000m in our case.|
|get_the_index_within_dist|Function to get a dataframe with pairs of centroid of population grid cell and fake entrance whose euclidian distance is smaller than distance threshold|**pop_clip**: output of population_data_prepocessing <br />**green_access**: output of green_data_prepocessing|
|origin_node|Function to get the nearest node id of each centroid of population grid cell| **df_index**: output of get_the_index_within_dist<br />**pop_clip**: output of population_data_prepocessing|
|target_node|Function to get the nearest node id of fake entrance of UGS |**df_index**: output of get_the_index_within_dist<br /> **green_access**: output of green_data_prepocessing|
|OD_Matrix|Function to get the real distance between each pair of population grid cell and fake entrances|**merge**: merge the dataframes of origin_node, target_node, df_index|
|neareat_entrance|Function to get the nearest entrance of each UGS for population grid cell |**OD_mile**: OD_mile is the OD Matrix after selection based on distance threshold, e.g real_distance < 1km|
|M2sfca|Function to calculate the accessibility score based on modified 2SFCA model with Guassian distribution|**OD_nearest_E**: output of the neareat_entrance <br />**distance_threshold**: 300m, 600m, 1000m|
    
## **Methods: Modified 2SFCA model (Guassian distribution)**
### Step1: 
Calculate the area-to-population ratio for each green space, which is the supply-demand ratio. 

<img width="252" alt="image" src="https://user-images.githubusercontent.com/105099474/175978092-ad73ab14-447e-4412-ac35-da2a78b05a81.png">

<img width="419" alt="image" src="https://user-images.githubusercontent.com/105099474/175978132-17b64531-aa82-42f5-9357-1829298fe456.png">

R_j is the supply-demand ratio of UGS j. S_j is the area size of UGS j. P_k is the population number in grid cell k. d_kj is the distance between the centroid of grid cell k and the nearest entrance of UGS j. d_0 is the catchment size (300m, 600m, 1000m)， which determines the service area of UGS j. G(d_kj,d_0) is the distance decay function of UGS j applying the Gaussian distribution.


### Step2:
For each population grid cell, search all green space that are within the distance threshold, and sum up the Rj calculated in step 1. 

<img width="612" alt="image" src="https://user-images.githubusercontent.com/105099474/175976507-ea11e5c2-1e12-470d-99d3-b363fbd98124.png">


**Definition of catchment area:**



<img width="800" alt="image" src="https://user-images.githubusercontent.com/105099474/175978555-b55bdf8a-b57f-4f97-99f6-ce065149a9df.png">



**To make comparable for different cities, we normalized the accessibility score for each population grid cell.**


<img width="134" alt="image" src="https://user-images.githubusercontent.com/105099474/175977020-bf526c53-ab5c-4ebc-b678-b2b3c8dd9b0a.png">


## Example: Normalized accessibility score for Washington D.C. 


<img width="800" alt="image" src="https://user-images.githubusercontent.com/105099474/175977942-f18ffc55-6553-4112-984a-a130f2fa4476.png">



**Contributors**<br />
Labib S.M.  email: s.m.labib@uu.nl<br />
Qiuyi Xu    e-mail: xuqiuyi1015@gmail.com



## **References**
An enhanced two-step floating catchment area (E2SFCA) method for measuring spatial accessibility to primary care physicians <br />
Analysis of urban green space accessibility and distribution inequity in the City of Chicago <br />
World Health Organization. (2013). Environmental sustainability in metropolitan areas <br />
Estimating multiple greenspace exposure types and their associations with neighbourhood premature mortality: A socioecological study <br />
Access to urban parks: Comparing spatial accessibility measures using three GIS-based approaches<br />


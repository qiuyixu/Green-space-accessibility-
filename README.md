# Green-space-accessibility 

Python script to calculate green space accessibility using modified 2SFCA model.

The main process is in the green_accessibility.py. It includes the data preprocessing for green space and population; calculation of the OD Matrix; Using  2SFCA model to get the accessibility scores. 

In the Notebook folder is an example for Ghent. 

This is a project still in progress and will be adjusted. If you found any mistake or have any suggestions, please feel free to contact me xuqiuyi1015@gmail.com. 

## Modified 2SFCA model (Guassian distribution)
### Step1: 
Calculate the area-to-population ratio for each green space, which is the supply-demand ratio. 

<img width="281" alt="image" src="https://user-images.githubusercontent.com/105099474/170116786-df8d98b2-0e0e-4eee-9a01-32ba41942f47.png">

Gj is the area of green space; Pi is the population; dij is the distance between the population grid cell and the green space; D is the distance threshold; v is the distance decay parameter

### Step2:
For each population grid cell, search all green space that are within the distance threshold, and sum up the Rj calculated in step 1. 

<img width="278" alt="image" src="https://user-images.githubusercontent.com/105099474/170117543-1f81ab40-92dc-4a8c-87ab-ac3823473bb0.png">


## Accessibility score for Ghent as an example

<img width="628" alt="image" src="https://user-images.githubusercontent.com/105099474/170119900-7359f88a-ccbb-40e6-8601-2baef243f3b6.png">

## References
An enhanced two-step floating catchment area (E2SFCA) method for measuring spatial accessibility to primary care physicians 
Analysis of urban green space accessibility and distribution inequity in the City of Chicago 

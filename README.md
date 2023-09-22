# HydroXplorer Web App

![stability-stable](https://img.shields.io/badge/stability-stable-green.svg)

This project aims to develop a web application to help firefighters determine the areas covered with existing and planned hydrants. The application:

1. Identifies accessible zones utilizing hydrant location or natural water sources.

2. Pinpoints nearby water sources for firefighting purposes.

3. Calculates elevation disparities between the fire location and surrounding water sources.


## Installation

To create the environemt needed for running the application we use conda:
```
conda create -n hydroxplorer-app python=3.10
conda install --yes --file requirements.txt
```

## Running the application locally
Simply open a terminal and from within your environment, type:
```
python src/app.py
```

## Deploying on docker

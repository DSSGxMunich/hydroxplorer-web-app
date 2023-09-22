#!/usr/bin/env python
"""
test_range_finder.py: Tests the functions defined in rangeFinder.py.
__author__ = "pankajrsingla"
"""

import os
import sys
import matplotlib
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
os.environ['USE_PYGEOS'] = '0'
import geopandas as gpd
import folium
import networkx as nx
import pytest

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import everything from rangeFinder.py
from rangeFinder import *

def test_get_colors():
    """
    Test the 'get_colors' function to ensure it generates color lists correctly.
    """
    # Define a list of predefined matplotlib colors
    mcolors = ['#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', \
               '#7f7f7f', '#bcbd22', '#17becf', '#1f77b4', '#ff7f0e']
    
    # Test getting a subset of colors (5 colors)
    colors_subset = get_colors(5)
    assert colors_subset == mcolors[:5]
    
    # Test getting all available colors (10 colors)
    colors_all = get_colors(10)
    assert colors_all == mcolors

    # Test getting more colors than available (12 colors)
    colors_repeat = get_colors(12)
    assert colors_repeat == mcolors + mcolors[:2]


def test_plot_initialization():
    """
    Test the initialization of the Plot class
    """
    
    # Create a Figure and Axes object for testing
    fig = matplotlib.pyplot.figure()
    ax = fig.add_subplot(111)
    
    # Initialize a Plot object with the created Figure and Axes
    plot = Plot(fig=fig, ax=ax)
    
    # Check if the fig and ax attributes are set correctly
    assert plot.fig is fig
    assert plot.ax is ax


def test_origin_initialization():
    """
    Test case to check the initialization of the Origin class
    """
    
    # Initialize an Origin object with an ID and coordinates
    origin = Origin(id=1, lat=48.152519, long=11.582104)
    
    # Check if the attributes are set correctly
    assert origin.id == 1
    assert origin.lat == 48.152519
    assert origin.long == 11.582104


def test_point_initialization():
    """
    Test case to check the initialization of the Point class
    """
    # Initialize a Point object with latitude, longitude, length, and mode
    lat = 123.456
    long = 23.45
    length = 789
    mode = "walk"
    point_type = "hydrant"
    point = Point(lat=lat, long=long, length=length, 
                  mode=mode, point_type=point_type)
    
    # Check if the attributes are set correctly
    assert point.lat == lat
    assert point.long == long
    assert point.length == length
    assert point.mode == mode
    assert point.point_type == point_type
    assert point.graph is None
    assert point.origin is None
    assert point.gdf is None
    assert point.plot is None
    assert point.points_in_range == []
    assert point.interactive is None
    assert point.debug is False


def test_point_is_in_state():
    """
    Test the 'is_in_state' function to check if a point lies in a state.
    """
    # Point is in the specified state(s)
    point_munich = Point(lat=48.15251938407116, long=11.582103781931604)
    assert point_munich.is_in_state("Bayern") is True

    point_delhi = Point(28.63005551713948, 77.21671040205324)
    assert point_delhi.is_in_state("Delhi") is True
    
    # Point is not in the specified state
    assert point_munich.is_in_state("Berlin") is False


def test_calculate_elevation():
    """
    Test the 'calculate_elevation' function in the Point class.
    """
    # Initialize a RangeFinder object
    point = Point(lat=40.78397967404166, long=-73.96314049062211) # New York
    point.calculate_elevation()

    # Check if elevation is correct
    assert int(point.elevation) == 34


def test_point_get_range_graph():
    """
    Test the 'get_range_graph' function in the Point class.
    """
    # Initialize a Point object for testing
    point = Point(lat=48.152519, long=11.582104, length=500, mode="drive")
    
    # Check if valid graph has been created
    point.get_range_graph()
    assert point.graph is not None
    
    # Invalid graph creation should raise an exception
    
    # Note: Currently the get_range_graph function raises the exception.
    # Uncomment this block when the exception has been gracefully handled.
    
    # lat_invalid = 1000.0 # Invalid latitude value
    # point_invalid = Point(lat=lat_invalid, long=11.582104, length=500, mode="drive")
    # with pytest.raises(Exception) as exc_info:
    #     point_invalid.get_range_graph()
    # assert "No valid network graph can be created" in str(exc_info.value)


def test_point_get_points_in_range():
    """
    Test the 'get_points_in_range' function in the Point class.
    """
    # Initialize a Point object for testing.
    length = 1000
    point = Point(lat=48.152519, long=11.582104, length=length, 
                  mode="drive", point_type="fire")
    point.get_range_graph()
    point.get_origin()
    
    # Calculate points within range for the given Point object.
    point.get_points_in_range()
    
    # Check if number of graph nodes is same as number of points in range.
    assert len(point.points_in_range) == len(point.graph.nodes())
    
    # Check if each node has information in the correct format.
    for node_data in point.points_in_range:
        assert isinstance(node_data, list)
        assert len(node_data) == 4

    # Get distances from the points_in_range list.
    distances = [node_data[3] for node_data in point.points_in_range]
    
    # Assert that the minimum distance is 0 (origin node to itself).
    assert min(distances) == 0
    
    # The maximum distance should be less than or equal to the specified length.
    assert max(distances) <= length


def test_point_get_origin():
    """
    Test the 'get_origin' function in the Point class.
    """
    # Initialize a Point object for testing
    lat = 48.152519
    long = 11.582104
    point = Point(lat=lat, long=long, length=400, mode="walk")
    point.get_range_graph()
    
    # Get the origin for the given Point object
    point.get_origin()
    
    # Check if 'origin' attribute is an instance of Origin
    assert isinstance(point.origin, Origin)

    # Compute origin coordinates directly, and compare
    origin_id = ox.nearest_nodes(point.graph, X=point.long, Y=point.lat, 
                                 return_dist=False)
    origin = Origin(origin_id)
    origin.lat = point.graph.nodes[origin_id]["y"]
    origin.long = point.graph.nodes[origin_id]["x"]

    # Check if 'lat' and 'long' attributes of origin are set correctly
    assert point.origin.lat == pytest.approx(origin.lat, abs=1e-6)
    assert point.origin.long == pytest.approx(origin.long, abs=1e-6)


def test_point_get_gdf():
    """
    Test the 'get_gdf' function in the Point class.
    """
    point = Point(lat=48.15251938407116, long=11.582103781931604, 
                  length=400, mode="drive", point_type="fire")
    point.get_range_graph()
    
    # Generate GeoDataFrame for the given Point object
    point.get_gdf()
    
    # Check if 'gdf' attribute is set, is a GeoDataFrame, and has some rows
    assert point.gdf is not None
    assert isinstance(point.gdf, gpd.GeoDataFrame)
    assert len(point.gdf) > 0


def test_point_plot_network_graph():
    """
    Test the 'plot_network_graph' function in the Point class.
    """
    # Initialize a Point object for testing
    point = Point(lat=28.63005551713948, long=77.21671040205324, 
                  length=500, mode="drive")
    point.get_range_graph()
    
    # Plot the network graph for the given Point object
    point.plot_network_graph()
    
    # Check if 'plot' attribute is set and is an instance of Plot
    assert point.plot is not None
    assert isinstance(point.plot, Plot)

    # Check that the plot has valid fig and ax objects
    assert isinstance(point.plot.fig, matplotlib.figure.Figure)
    assert isinstance(point.plot.ax, matplotlib.axes._axes.Axes)


def test_point_annotate_node_distances_from_centre():
    """
    Test the 'annotate_node_distances_from_centre' function in the Point class.
    """
    # Initialize a Point object for testing
    point = Point(lat=48.152519, long=11.582104, length=480, mode="drive")
    point.get_range_graph()
    
    # Plot the network graph for the given Point object
    point.plot_network_graph()
        
    # Check if 'plot' attribute is set and is an instance of Plot
    assert point.plot is not None
    assert isinstance(point.plot, Plot)

    # Annotate the node distances
    point.annotate_node_distances_from_centre()
    
    # Check if there are at least annotations on the plot
    annotations = point.plot.ax.texts
    assert len(annotations) > 0
    for annotation in annotations:
        assert isinstance(annotation, matplotlib.text.Annotation)


def test_point_annotate_origin_coordinates():
    """
    Test the 'annotate_origin_coordinates' function in the Point class.
    """
    # Initialize a Point object for testing
    point = Point(lat=48.152519, long=11.582104, length=450, mode="drive")
    point.get_range_graph()
    point.plot_network_graph()
    
    # Annotate the origin point's coordinates on the plot
    point.annotate_origin_coordinates()
    
    # Check if there are annotations on the plot (at least some)
    annotations = point.plot.ax.texts
    assert len(annotations) > 0
    
    # Find the annotation that corresponds to the origin coordinates
    origin_annotation = None
    for annotation in annotations:
        if annotation.get_text() == f"({point.origin.long:.3f}, {point.origin.lat:.3f})":
            origin_annotation = annotation
            break
    
    # Assert that the origin annotation is found and has the correct attributes
    assert origin_annotation is not None
    assert isinstance(origin_annotation, matplotlib.text.Annotation)
    assert origin_annotation.xy == (point.origin.long, point.origin.lat)
    assert origin_annotation.get_ha() == 'center'
    assert origin_annotation.get_fontsize() == 10
    assert origin_annotation.get_color() == "white"


def test_point_annotate_street_names():
    """
    Test the 'annotate_street_names' function in the Point class.
    """
    # Initialize a Point object for testing
    point = Point(lat=51.509552216027714, long=-0.1284403947353646, length=1000, mode="walk")
    point.plot_network_graph()
    # Annotate street names on the plot
    point.annotate_street_names()
    
    # Check if there are annotations on the plot (at least some)
    annotations = point.plot.ax.texts
    assert len(annotations) > 0

    # If repeat_street_names is set, there should be more annotations.
    point_copy = Point(lat=51.509552216027714, long=-0.1284403947353646, length=1000, mode="walk")
    point_copy.plot_network_graph()
    point_copy.annotate_street_names(repeat_street_names=True)
    additional_annotations = point_copy.plot.ax.texts
    
    assert len(additional_annotations) > len(annotations)


def test_point_get_plot():
    """
    Test the 'get_plot' function in the Point class.
    """
    # Call the test cases for the functions invoked by get_plot
    test_point_plot_network_graph()
    test_point_annotate_node_distances_from_centre()
    test_point_annotate_origin_coordinates()
    test_point_annotate_street_names()


def test_point_get_interactive_map():
    """
    Test the 'get_interactive_map' function in the Point class.
    """
    # Initialize a Point object for testing
    point = Point(lat=-35.30273276420382, long=149.12567284494077, length=500, mode="drive")

    # Test marker icons
    point.get_interactive_map(default_style="OpenStreetMap", edge_color="red")

    # Check if the map has a valid name
    assert isinstance(point.interactive.get_name(), str)  # Check for map name
    assert "map_" in point.interactive.get_name() # Map name starts with "map_"
    
    # Check that there is a tile layer and a marker
    all_children_value_types = [type(value) for value in list(point.interactive._children.values())]
    assert folium.raster_layers.TileLayer in all_children_value_types
    assert folium.map.Marker in all_children_value_types

    # Check if the generated HTML map contains the expected elements
    interactive_html = point.interactive.get_root().render()
    assert "html" in interactive_html
    assert "head" in interactive_html
    assert "body" in interactive_html
    assert "leaflet" in interactive_html

    # Test if tooltip contains correct information
    point_text = f"Point: ({point.lat},{point.long}), Hose length: {int(point.length)}, Mode: {point.mode}"
    assert point_text in point.interactive.get_root().render()


def test_rangefinder_initialization():
    """
    Test the constructor for the RangeFinder class.
    """
    # Initialize a RangeFinder object
    range_finder = RangeFinder()

    # Check if the show_elevations attribute is False
    assert range_finder.show_elevations == False

    # Check if the 'points' attribute is an empty list
    assert isinstance(range_finder.points, list)
    assert len(range_finder.points) == 0

    # Check if the 'merged_gdf' attribute is set to None
    assert range_finder.merged_gdf is None

    # Check if the 'plots' attribute is an empty list
    assert isinstance(range_finder.plots, list)
    assert len(range_finder.plots) == 0

    # Check if the 'merged_interactive' attribute is set to None
    assert range_finder.merged_interactive is None


def test_rangefinder_add_points():
    """
    Test the 'add_points' function in the RangeFinder class.
    """
    # Initialize a RangeFinder object
    rf = RangeFinder()

    # Create a sample input DataFrame with 4 points
    input_data = {
        "latitude": [48.1525, 48.1536, 48.1547, 48.1558],
        "longitude": [11.5821, 11.5832, 11.5843, 11.5854],
        "hose_length": [800, 600, 500, 400],
        "transportation_mode": ["drive", "drive_service", "bike", "walk"],
        "point_type": ["fire", "hydrant", "hydrant", "fire"]
    }
    input_df = pd.DataFrame(input_data)

    # Add points to the RangeFinder
    rf.add_points(input_df)

    # Check if points have been added to the RangeFinder
    assert len(rf.points) == 4

    # Check if the added points have the correct attributes
    for point in rf.points:
        assert isinstance(point, Point)
        assert isinstance(point.graph, nx.MultiDiGraph)
        assert isinstance(point.origin.id, int)
        assert isinstance(point.gdf, gpd.GeoDataFrame)


def test_rangefinder_get_plots():
    """
    Test the 'get_plots' function in the RangeFinder class.
    """
    # Initialize a RangeFinder object
    range_finder = RangeFinder()

    # Create sample points and add them to the RangeFinder
    points_data = [
        {"latitude": 52.5187, "longitude": 13.3780, "hose_length": 450, "transportation_mode": "walk"},
        {"latitude": 52.5817, "longitude": 13.3890, "hose_length": 550, "transportation_mode": "bike"},
        {"latitude": 52.5781, "longitude": 13.3970, "hose_length": 650, "transportation_mode": "drive_service"},
        {"latitude": 52.5718, "longitude": 13.3980, "hose_length": 750, "transportation_mode": "drive"}
    ]

    for point_data in points_data:
        point = Point(point_data["latitude"], point_data["longitude"], 
                      point_data["hose_length"], point_data["transportation_mode"])
        range_finder.points.append(point)

    # Generate plots for the points using the get_plots method
    range_finder.get_plots()

    # Check if plots have been added to the RangeFinder
    assert len(range_finder.plots) == 4

    # Check if the added plots are instances of the Plot class
    for plot in range_finder.plots:
        assert isinstance(plot, Plot)

        # Check that the plot has valid fig and ax objects
        assert isinstance(plot.fig, matplotlib.figure.Figure)
        assert isinstance(plot.ax, matplotlib.axes._axes.Axes)


def test_calculate_elevations():
    """
    Test the 'calculate_elevations' function in the RangeFinder class.
    """
    # Initialize a RangeFinder object
    rf = RangeFinder()

    # Create a sample input DataFrame with 4 points
    input_data = {
        "latitude": [48.15251938407116, 28.63005551713948],
        "longitude": [11.582103781931604, 77.21671040205324],
        "hose_length": [800, 600],
        "transportation_mode": ["drive", "drive_service"],
        "point_type": ["fire", "hydrant"]
    }
    input_df = pd.DataFrame(input_data)

    # Add points to the RangeFinder
    rf.add_points(input_df)
    rf.show_elevations = True
    rf.calculate_elevations()

    # Check if elevations were calculated and stored correctly
    assert int(rf.points[0].elevation) == 517
    assert int(rf.points[1].elevation) == 218


def test_rangefinder_add_edge_colors():
    """
    Test the 'add_edge_colors' function in the RangeFinder class.
    """
    # Initialize a RangeFinder object
    rf = RangeFinder()

    # Create a sample input DataFrame with 4 points
    input_data = {
        "latitude": [28.63005551713948, 40.78397967404166],
        "longitude": [77.21671040205324, -73.96314049062211],
        "hose_length": [300, 400],
        "transportation_mode": ["walk", "bike"],
        "point_type": ["fire", "fire"]
    }
    input_df = pd.DataFrame(input_data)

    # Add points to the RangeFinder
    rf.add_points(input_df)
    rf.merged_gdf = pd.concat([point.gdf for point in rf.points], 
                              ignore_index=True)
    
    assert rf.merged_interactive is None
    rf.add_edge_colors()
    # Interactive map has been generated
    assert rf.merged_interactive is not None
            
    # All element types in the interactive map
    all_children_vals = [str(value) for value in list(rf.merged_interactive._children.values())]
    # At this stage, the map should only have a TileLayer and a GeoJson
    assert len(all_children_vals) == 2
    assert "folium.raster_layers.TileLayer" in all_children_vals[0]
    assert "folium.features.GeoJson" in all_children_vals[1]


def test_rangefinder_add_markers_to_map():
    """
    Test the 'add_markers_to_map' function in the RangeFinder class.
    """
    # Initialize a RangeFinder object
    rf = RangeFinder()

    # Create a sample input DataFrame with 4 points
    input_data = {
        "latitude": [37.99231816755858, -35.30273276420382],
        "longitude": [23.732845405626346, 149.12567284494077],
        "hose_length": [500, 600],
        "transportation_mode": ["bike", "drive"],
        "point_type": ["hydrant", "fire"]
    }
    input_df = pd.DataFrame(input_data)

    # Add points to the RangeFinder
    rf.add_points(input_df)
    rf.merged_gdf = pd.concat([point.gdf for point in rf.points], 
                              ignore_index=True)
    rf.add_edge_colors()
    rf.add_markers_to_map()

    # n_points can be different than the number of points we specified above 
    # in input_data, since not all points are guaranteed to have a valid graph.
    n_points = len(rf.points)
    
    # All element types in the interactive map
    all_children_vals = [str(value) for value in list(rf.merged_interactive._children.values())]
    
    # Check that the interactive map has n circles for the n origin points
    assert sum("folium.vector_layers.Circle" in value for value in all_children_vals) == n_points
    # Check that the map has n markers for the n points
    assert sum("folium.map.Marker" in value for value in all_children_vals) == n_points

    # For n points, there should be (n * n-1) // 2 lines in the map
    assert sum("folium.vector_layers.PolyLine" in value for value in all_children_vals) == \
           n_points * (n_points - 1) // 2


def test_rangefinder_create_interactive_map():
    # Initialize a RangeFinder object
    rf = RangeFinder()

    # Create a sample input DataFrame with 2 points
    input_data = {
        "latitude": [50.87409910796766, 50.87803070660611],
        "longitude": [4.697961746722167, 4.681290298545937],
        "hose_length": [600, 300],
        "transportation_mode": ["drive", "walk"],
        "point_type": ["fire", "hydrant"]
    }
    input_df = pd.DataFrame(input_data)

    # Add points to the RangeFinder
    rf.add_points(input_df)

    # Test if the method returns a Folium Map object
    rf.create_interactive_map()
    interactive_map = rf.merged_interactive
    assert isinstance(rf.merged_interactive, folium.Map)

    # Test if merged GeoDataFrame is created
    assert isinstance(rf.merged_gdf, gpd.GeoDataFrame)

    # Test if unique colors are generated correctly
    unique_colors = get_colors(len(rf.points))
    assert len(unique_colors) == len(rf.points)

    # Test if edge colors are generated correctly
    edge_colors = ([unique_colors[i]] * len(point.gdf) for i, point in enumerate(rf.points))
    edge_colors = [color for color_list in edge_colors for color in color_list]
    assert len(edge_colors) == len(rf.merged_gdf)

    # Check if the map has a valid name
    assert isinstance(interactive_map.get_name(), str)  # Check for map name
    assert "map_" in interactive_map.get_name() # Map name starts with "map_"

    # Check that there is a tile layer and a marker
    all_children_value_types = [type(value) for value in list(interactive_map._children.values())]
    assert folium.raster_layers.TileLayer in all_children_value_types
    assert folium.map.Marker in all_children_value_types

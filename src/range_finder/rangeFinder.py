#!/usr/bin/env python
"""
rangeFinder.py: Finds and interactively visualizes points within a certain 
range of a central point.

__author__ = "pankajrsingla"
"""

# Import modules
import warnings
warnings.filterwarnings("ignore")
import folium
from folium import plugins
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox
from json import loads
from requests import get
import matplotlib.colors as mcolors
from collections import OrderedDict
from func_timeout import func_timeout, FunctionTimedOut
# parallelization
import os
import multiprocessing
import concurrent.futures 

import geopandas as gpd

# Configure residual file generation
ox.config(use_cache=False, log_console=False)

# Timeout for elevation calculation (and potentially other) APIs.
MAX_SECONDS_TIMEOUT_ELEVATION = 15


def get_num_cores():
    try:
        return os.cpu_count() or multiprocessing.cpu_count()
    except NotImplementedError:
        return 1 

def find_intersection(pair:tuple):
    """Receive a tuple of two geopandas dataframes, return their intersection"""
    i, j = pair
    return gpd.overlay(i,j, how='intersection')

def get_geometry_only_gdf(gdf):
    """
    For a geopandas dataframe with street info, return a gdf with
    only the geometry (incl lat/long values) but no meta data.
    This is is used to simplify graph merges and geojson parsing
    because there will be less redundant data to process.
    """
    return gdf.drop(columns=gdf.columns.difference(['geometry']))

def chuck_geojson_constructor(original_gdf,color):
    """
        Converts a geopandas dataframe to a folium geojson, 
        but does so by first splitting the gdf into chunks,
        then processing them in parallel.
    """
    num_chunks = 4
    gdf_chunks = np.array_split(original_gdf, num_chunks)
    
    def convert_to_geojson(gdf_chunk):
        geojson = folium.GeoJson(
                    get_geometry_only_gdf(gdf_chunk), 
                    style_function=lambda x, 
                    color=color: {
                        'fillColor': color, 
                        'color': color, 
                        'weight': 3,
                        'fillOpacity': 0.5,
                        'lineOpacity': 0.5
                        }
                    )
        return geojson
    
    executor = concurrent.futures.ThreadPoolExecutor(get_num_cores())
    with executor as executor:
        geojson_objects = list(executor.map(convert_to_geojson, gdf_chunks))

    combined_geojson = folium.FeatureGroup()
    for geojson in geojson_objects:
        geojson.add_to(combined_geojson)

    return combined_geojson


def get_colors(n):
    """
    Generate a list of distinct colors.

    This function generates a list of distinct colors using the TABLEAU_COLORS 
    color palette from the matplotlib library. It ensures that if the requested 
    number of colors (n) is smaller than the number of available distinct colors, 
    the complete palette is returned. If n is larger, the palette is repeated 
    and extended as needed to accommodate the requested number.

    Args:
        n (int): The number of distinct colors to generate.

    Returns:
        list: A list of distinct colors.

    Example:
        >>> get_colors(5)
        ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    """
    colorlist = list(mcolors.TABLEAU_COLORS.values())
    # Put blue and orange at the end.
    colorlist = colorlist[2:] + colorlist[:2]
    num_unique_colors = len(colorlist)

    if n <= num_unique_colors:
        return colorlist[:n]
    
    # Calculate how many times to repeat and the remainder
    times, extra = divmod(n, num_unique_colors)
    return colorlist * times + colorlist[:extra]

    
class Plot:
    """
    A class to manage a Matplotlib plot.

    This class provides a simple interface for managing Matplotlib plots. 
    It takes a figure (fig) and an axes (ax) as parameters, which can be 
    optionally provided during initialization.

    Attributes:
        fig (matplotlib.figure.Figure): The figure object for the plot.
        ax (matplotlib.axes._axes.Axes): The axes object for the plot.

    Example:
        >>> import matplotlib.pyplot as plt
        >>> fig, ax = plt.subplots()
        >>> my_plot = Plot(fig, ax)
    """

    def __init__(self, fig=None, ax=None):
        """
        Initialize a Plot object.

        Args:
            fig (matplotlib.figure.Figure, optional): The figure object.
            ax (matplotlib.axes._axes.Axes, optional): The axes object.
        """
        self.fig = fig
        self.ax = ax


class Origin:
    """
    A class to represent the origin point in a network graph.

    This class defines an origin point with attributes for its ID, latitude, 
    and longitude. The ID is a unique identifier for the origin, 
    while latitude and longitude represent its geographic coordinates.

    Attributes:
        id (int): The unique identifier for the origin point.
        lat (float): The latitude of the origin point.
        long (float): The longitude of the origin point.

    Example:
        >>> origin1 = Origin(1, 48.155322, 11.442776)
        >>> origin2 = Origin(2)
    """

    def __init__(self, id, lat=None, long=None):
        """
        Initialize an Origin object.

        Args:
            id (int): The unique identifier for the origin point.
            lat (float, optional): The latitude of the origin point.
            long (float, optional): The longitude of the origin point.
        """
        self.id = id
        self.lat = lat
        self.long = long


class Point:
    """
    A class to represent a geographic point for analysis.

    This class defines a point with geographic coordinates (latitude and 
    longitude). It includes various attributes for customizing analysis 
    parameters and later features additional methods for interacting 
    with the point.

    Attributes:
        lat (float): The latitude of the geographic point.
        long (float): The longitude of the geographic point.
        length (float): The length parameter for analysis (default is 100).
        mode (str): The mode of analysis (default is "drive").
        point_type(str): Type of point, either "hydrant" or "fire"
        elevation (float): Height of the point above sea level.
        graph (networkx.MultiDiGraph): Networkx graph object representing the filtered street network.
        origin: An object representing the origin point in the network graph.
        gdf (geopandas.GeoDataFrame): Geodataframe representing the network graph.
        plot: An object containing the Matplotlib figure and axes for the network plot.
        points_in_range (list of tuple): List of points within the specified length from the point.
        interactive (folium.Map): Folium map for the network with interactive layers and markers.
        debug (bool): Boolean flag to display error/warning messages.

    Example:
        >>> point = Point(48.155322, 11.442776)
    """

    def __init__(self, lat, long, length=1000, mode="drive", point_type="hydrant"):
        """
        Initialize a Point object.

        Args:
            lat (float): The latitude of the geographic point.
            long (float): The longitude of the geographic point.
            length (float, optional): The length parameter for analysis (default is 100).
            mode (str, optional): The mode of analysis (default is "drive").
            point_type(str, optional): Type of point, either "hydrant" (default) or "fire"
        """
        self.lat = lat
        self.long = long
        self.length = length
        self.mode = mode
        self.point_type = point_type
        
        # Additional parameters for later use
        self.elevation = None
        self.graph = None
        self.origin = None
        self.gdf = None
        self.plot = None
        self.points_in_range = []
        self.interactive = None
        self.debug = False


    def is_in_state(self, state="Bayern"):
        """
        Check if the point is located in a specific state.

        This function queries the Nominatim API to determine whether the 
        geographic point is located in the specified state.

        Args:
            state (str, optional): The name of the state to check (default is "Bayern").

        Returns:
            bool: True if the point is located in the specified state, False otherwise.

        Example:
            >>> point = Point(48.155322, 11.442776)
            >>> point.is_in_state("Bayern")
            True
        """
        url = f'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={self.lat}&lon={self.long}&zoom=18&addressdetails=1&namedetails=1'
        point_address_data = loads(get(url).text)
        if "address" not in point_address_data or "state" not in point_address_data["address"]:
            return False
        return point_address_data["address"]["state"] == state
    

    def calculate_elevation(self):
        """
        Retrieve the elevation of a geographical point using an external API.

        This method sends a GET request to an elevation API to obtain the elevation
        of a specific geographic point based on its latitude and longitude coordinates.

        Args:
            self: The current object instance.
            
        Returns:
            None: The elevation data is stored in the object's 'elevation' attribute.
        """
        # API endpoint
        url = "https://api.open-elevation.com/api/v1/lookup"

        # Coordinates
        coordinates = str(self.lat) + "," + str(self.long)

        # Defining a parameter dictionary for the parameters to be sent to the API
        parameters = {'locations': coordinates}

        # Send a GET request and save the response as a JSON object
        response = get(url=url, params=parameters)

        # Extract elevation
        self.elevation = response.json()["results"][0]["elevation"]

    
    def get_range_graph(self):
        """
        Create a network graph around the point with a specified range.

        This function generates a network graph using OSMnx from the geographic 
        point, considering the specified range and mode of travel. It assigns the 
        graph to the 'graph' attribute of the Point object.

        If the graph cannot be created, an exception is raised with an informative 
        error message.

        Returns:
            None

        Example:
            >>> point = Point(48.155322, 11.442776)
            >>> point.get_range_graph()
        """
        try:
            graph = ox.graph_from_point((self.lat, self.long), 
                                                dist=self.length, 
                                                network_type=self.mode, 
                                                dist_type="network",
                                                simplify=True
                                                )
            self.graph = graph
        except Exception as exc:
            error_message = f"No valid network graph can be created for the following parameters: Coordinates: ({self.lat}, {self.long}), Hose length: {self.length}, Mode: {self.mode}"
            raise Exception(error_message) from exc


    def get_points_in_range(self):
        """
        Calculate distances from the origin point to each node in the graph.

        This function calculates the distances from the origin point to each 
        node in the graph and appends the tuple of results to the 'points_in_range' 
        list of the RangeFinder object. Each tuple consists of the node's OSMid, 
        latitude, longitude, and its distance from the origin node.

        Returns:
            None
        """
        for node in self.graph.nodes():
            node_lat = self.graph.nodes[node]["y"]
            node_long = self.graph.nodes[node]["x"]
            node_distance_from_center = float("nan")
            
            try:
                # Calculate shortest path distance from origin to node
                node_distance_from_center = nx.shortest_path_length(
                    self.graph, self.origin.id, node, weight="length")
            
            except nx.NetworkXNoPath as err:
                # Handle cases where no path exists
                if self.debug:
                    print("Error:", err)
                raise Exception("No valid path found.") from err

            self.points_in_range.append([node, node_lat, node_long, 
                                        node_distance_from_center])


    def get_origin(self):
        """
        Retrieve the nearest origin point on the graph.

        This function determines the nearest origin point on the graph using 
        OSMnx based on the point's geographic coordinates. It assigns the 
        origin's latitude and longitude to the 'origin' attribute 
        of the Point object.

        Returns:
            None

        Example:
            >>> point = Point(48.155322, 11.442776)
            >>> point.get_origin()
        """
        origin_id = ox.nearest_nodes(self.graph, X=self.long, Y=self.lat, 
                                     return_dist=False)
        self.origin = Origin(origin_id)
        self.origin.lat = self.graph.nodes[origin_id]["y"]
        self.origin.long = self.graph.nodes[origin_id]["x"]

    
    def get_gdf(self):
        """
        Convert the graph to a GeoDataFrame.

        This function converts the network graph to GeoDataFrame using OSMnx.
        It assigns the resulting GeoDataFrame to the 'gdf' attribute of 
        the Point object.

        Returns:
            None

        Example:
            >>> point = Point(48.155322, 11.442776)
            >>> point.get_gdf()
        """
        self.gdf = ox.graph_to_gdfs(self.graph, nodes=False)


    def plot_network_graph(self, dpi=100, fig_size=(20,16)):
        """
        Plot the network graph centered around the origin point.

        This function generates a plot of the network graph using OSMnx
        and Matplotlib. The origin point is highlighted in red, while other
        nodes are shown in cyan.

        Args:
            dpi (int, optional): Dots per inch for the plot resolution (default is 100).
            fig_size (tuple, optional): Figure size in inches (default is (20, 16)).

        Returns:
            None
        """
        
        # Ensure that we have a graph for the point.
        if not self.graph:
            self.get_range_graph()
        
        # Ensure an origin point is available.
        if not self.origin:
            self.get_origin()
            
        # Get the index of the origin node in the graph
        origin_node_index = list(self.graph.nodes).index(self.origin.id)
        
        # Assign colors to nodes, highlighting the origin node in red
        node_colors = ["cyan"] * self.graph.number_of_nodes()
        node_colors[origin_node_index] = "red"
        
        # Plot the graph and assign the plot to the 'plot' attribute
        fig, ax = ox.plot_graph(self.graph, bgcolor="black", node_size=25, 
                                edge_linewidth=1, node_color=node_colors, 
                                edge_color="lightblue", show=False, 
                                close=True, figsize=fig_size)
        fig.set_dpi(dpi)
        
        self.plot = Plot(fig, ax)


    def annotate_node_distances_from_centre(self, annotate_coordinates=False):
        """
        Annotate node distances from the origin point on the network graph.

        This function annotates the nodes on the network graph with their 
        distances from the origin point. It optionally allows annotation of 
        node coordinates and provides the option to show debugging information.

        Args:
            annotate_coordinates (bool, optional): Whether to annotate 
            node coordinates (default is False).

        Returns:
            None
        """
        # Ensure that we have a valid plot
        if not self.plot:
            self.plot_network_graph()

        # Provide a warning if shortest path calculation might take a long time
        if self.length > 2000:
            print("Warning: Shortest path calculation for a large network can take a long time.")

        # Iterate through all nodes in the graph
        for node in self.graph.nodes():
            node_lat = self.graph.nodes[node]["y"]
            node_long = self.graph.nodes[node]["x"]

            # Annotate node coordinates (for the graph) if required
            if annotate_coordinates:
                self.plot.ax.annotate(f"({node_long:.3f}, {node_lat:.3f})", 
                                    (node_long, node_lat),
                                    textcoords="offset points", xytext=(0, 5), 
                                    ha='center', color="white", fontsize=5)

            try:
                # Calculate shortest path distance from origin to the current node
                node_distance_from_center = nx.shortest_path_length(
                    self.graph, self.origin.id, node, weight="length")
            
            except nx.NetworkXNoPath as err:
                # Handle cases where no path exists
                if self.debug:
                    print("Error:", err)
                self.points_in_range.append((node_lat, node_lat, 
                                             float("nan")))
                raise Exception("Shortest path between the points could not be computed.") from err
                
            else:
                # Annotate node with its distance from origin
                self.plot.ax.annotate(round(node_distance_from_center, 2), 
                                    (node_long, node_lat),
                                    textcoords="offset points", xytext=(0, 5), 
                                    ha="center", color="white", fontsize=5)
                self.points_in_range.append((node, node_lat, node_long, 
                                             node_distance_from_center))


    def annotate_origin_coordinates(self):
        """
        Annotate the origin point's coordinates on the network graph.

        This function annotates the origin point on the network graph 
        with its coordinates.

        Returns:
            None
        """
        # Ensure that we have a valid plot
        if not self.plot:
            self.plot_network_graph()

        # Annotate the origin point's coordinates on the graph
        self.plot.ax.annotate(f"({self.origin.long:.3f}, {self.origin.lat:.3f})", 
                            (self.origin.long, self.origin.lat),
                            textcoords="offset points", xytext=(0, 5), 
                            ha='center', color="white", fontsize=10)


    def annotate_street_names(self, repeat_street_names=False):
        """
        Annotate street names on the network graph.

        This function annotates street names on the network graph. Street 
        names are only annotated once for each unique name unless 
        'repeat_street_names' is set to True.

        Args:
            repeat_street_names (bool, optional): Whether to repeat annotating 
            street names (default is False).

        Returns:
            None
        """
        street_names = set() # Set to store unique street names

        # Ensure that we have a valid Geodataframe
        if self.gdf is None or self.gdf.empty:
            self.get_gdf()

        # Iterate through GeoDataFrame rows to annotate street names:
        for _, edge in self.gdf.fillna("").iterrows():
            if not (hasattr(edge, "name") and "name" in edge):
                continue
            
            street_name = edge["name"]
            if not street_name:
                continue
            
            # Check if street name is a list:
            if isinstance(street_name, list):
                street_name = street_name[0]
            
            # Annotate street name only if unique or if repeat is allowed
            if (street_name not in street_names) or repeat_street_names:
                street_names.add(street_name)
                # Calculate the centroid of the street geometry
                street_centre = edge["geometry"].centroid
                self.plot.ax.annotate(street_name, 
                                      (street_centre.x, street_centre.y), 
                                      c="white", 
                                      fontsize=8)


    def get_plot(self, dpi=100, fig_size=(20,16), annotate_distances=True, 
                 annotate_origin=False, annotate_streets=True, repeat_street_names=False):
        """
        Visualizes points in range of a point.

        Args:
        - dpi (int, optional): Dots per inch (DPI) resolution for the plot. 
        Default is 100.
        - fig_size (tuple): A tuple containing width and height of the plot figure.
        - annotate_distances (bool, optional): Whether to annotate distances 
        from the point. Default is True.
        - annotate_streets (bool, optional): Whether to annotate street names 
        on the plot. Default is True.
        - annotate_origin (bool, optional): Whether to annotate the point's 
        origin point on the plot. Default is True.
        - repeat_street_names (bool, optional): Whether to repeat annotating 
            street names (default is False).

        Returns:
            None
        """
        self.plot_network_graph(dpi=dpi, fig_size=fig_size)
        
        if annotate_distances:
            self.annotate_node_distances_from_centre()
        
        if annotate_origin:
            self.annotate_origin_coordinates()
        
        if annotate_streets:
            self.annotate_street_names(repeat_street_names)


    def get_interactive_map(self, default_style="OpenStreetMap", edge_color="red"):
        """
        Generate an interactive Folium map displaying the network graph.

        This function generates an interactive Folium map using network 
        GeoDataFrame with a customizable style. It includes markers for 
        the origin and the specified point.

        Args:
            default_style (str, optional): Default map style (default is "OpenStreetMap").
            edge_color (str, optional): Color for the edges in the map (default is "red").

        Returns:
            None
        """
        # Ensure that we have a range graph
        if not self.graph:
            self.get_range_graph()
        
        # Ensure an origin point is available.
        if not self.origin:
            self.get_origin()

        # Ensure that we have a valid Geodataframe
        if not self.gdf:
            self.get_gdf()

        # Create the interactive map using the GeoDataFrame
        self.interactive = self.gdf.explore(
            tiles=default_style,
            popup=False,
            width="100%",
            height="100%",
            style_kwds={"color": edge_color, "weight": 3.5, "fillOpacity": 0.1},
            zoom_start=15
        )
        
        # Define available map styles and remove the default style
        map_styles = ["OpenStreetMap", "Stamen Terrain", "Stamen Toner", 
                      "Stamen Water Color", "cartodbpositron", 
                      "cartodbdark_matter"]
        map_styles.remove(default_style)
        
        # Add additional map styles to the interactive map
        for style in map_styles:
            folium.TileLayer(style).add_to(self.interactive)
        
        # Add a layer control to allow switching between map styles
        folium.LayerControl().add_to(self.interactive)
        
        # Add a marker for the specified point and the origin point
        point_text = f"<h4 style='color:black;'>Point: ({self.lat},{self.long}), Hose length: {int(self.length)}, Mode: {self.mode}</h4>"
        point_icon = folium.Icon(color="black", 
                                 icon_color="lightblue", 
                                 prefix="fa", 
                                 icon="fa-faucet")
        if self.point_type == "fire":
            point_icon = folium.Icon(color="black", 
                                     icon_color="orange", 
                                     prefix="fa", 
                                     icon="fa-fire")
        folium.Marker(location=(self.lat, self.long), 
                      popup=None, 
                      tooltip=point_text, 
                      icon=point_icon
                      ).add_to(self.interactive)
        
        origin_icon = folium.Icon(color="blue", icon="none")
        folium.Marker(location=(self.origin.lat, self.origin.long), 
                      popup=None, 
                      tooltip=None, 
                      icon=origin_icon
                      ).add_to(self.interactive)


class RangeFinder:
    """
    A class to manage a collection of geographic points and their analysis.

    This class defines a RangeFinder object that can store multiple geographic 
    points, their GeoDataFrames, plots, and interactive maps. It provides 
    methods for merging and visualizing the collected data.

    Attributes:
        points (list): A list to store Point objects representing geographic points.
        merged_gdf (geopandas.GeoDataFrame): A GeoDataFrame to store merged data.
        plots (list): A list to store Plot objects for each point.
        merged_interactive (folium.Map): An interactive Folium map for merged data.
        show_elevations (bool): Whether to show elevation data for points (default is False)

    Example:
        >>> rf = RangeFinder()
        >>> point1 = Point(48.155322, 11.442776)
        >>> point2 = Point(40.712776, -74.005974)
        >>> rf.points.append(point1)
        >>> rf.points.append(point2)
    """

    def __init__(self):
        """
        Initialize a RangeFinder object.
        """
        self.points = []
        self.merged_gdf = None
        self.plots = []
        self.merged_interactive = None
        self.show_elevations = False
        
    @staticmethod
    def handle_point_graph(row):
        """
        A parralelizable function for generating the Point objects,
        and mx Graphs for each row in the input data.
        """
        # Create a Point object for each row in the input DataFrame
        point = Point(
            row["latitude"], 
            row["longitude"], 
            row["hose_length"], 
            row["transportation_mode"], 
            row["point_type"]
            )
        
        # Check if the point lies within the specified state
        # if not point.is_in_state():
            # print("Warning: The following point does not lie inside Bayern. latitude:", 
            # point.lat, ", longitude:", point.long, ", Hose length:", point.length, ", Mode:", point.mode)
            # continue
        
        # Generate network graph for the point and proceed if successful
        point.get_range_graph()
        if point.graph and type(point.graph) == nx.MultiDiGraph:
            point.get_origin()
            point.get_gdf()
        return point
        

    
    def add_points(self, input_df):
        """
        Add points from an input DataFrame to the RangeFinder.

        This function adds points to the RangeFinder based on an input DataFrame.
        It creates Point objects for each row in the DataFrame, 
        performs validation, and adds valid points along with their data 
        to the RangeFinder.

        Args:
            input_df (pandas.DataFrame): Input DataFrame containing point information.

        Returns:
            None
        """

        executor = concurrent.futures.ProcessPoolExecutor(
            max_workers=get_num_cores()
            )

        row_list = [row[1] for row in input_df.iterrows()]
        with executor as executor:
            points = list(
                    executor.map(
                    RangeFinder.handle_point_graph, 
                    row_list
                    )
                )
        self.points = points


    def get_plots(self):
        """
        Generate plots for each point in the RangeFinder.

        This function generates plots for each point in the RangeFinder. 
        The generated plots are added to the 'plots' attribute of the RangeFinder.

        Returns:
            None
        """
        for point in self.points:
            point.get_plot()
            # Add the generated plot to the 'plots' attribute
            self.plots.append(point.plot)


    def calculate_elevations(self):
        """
        Calculate elevations for multiple geographic points using an external API.

        This method sends a single GET request to an elevation API with 
        multiple coordinates concatenated together to obtain elevations for 
        multiple geographic points simultaneously. The elevations are then 
        stored in the 'elevation' attribute of each respective point.
        
        Returns:
            None: The elevations are stored in the 'elevation' attribute of 
            each individual point object.
        """
        # API endpoint
        url = "https://api.open-elevation.com/api/v1/lookup"

        # Aggregate all coordinates for a single query - saves time
        coordinates = ""
        for point in self.points:
            coordinates += str(point.lat) + "," + str(point.long) + "|"
        coordinates = coordinates[:-1] # Remove the last '|'

        # Defining a parameter dictionary for the parameters to be sent to the API
        parameters = {'locations': coordinates}

        # Send a GET request and save the response as a JSON object
        response = get(url=url, params=parameters)

        # Extract elevation and store per point
        for i, point in enumerate(self.points):
            point.elevation = response.json()["results"][i]["elevation"]

    def add_edge_colors(self):
        """
        Assigns colors to edges in a GeoDataFrame representing a network graph
        based on their association with multiple points' networks.

        This function iterates through each point's GeoDataFrame and identifies
        common edges among different points' networks. It then assigns colors to
        these common edges based on a proportional blend of colors associated
        with each point's network.

        The resulting colored edges are added to the merged GeoDataFrame, and
        an interactive Folium map is generated to visualize the network graph
        with the assigned edge colors.
        
        Returns:
            None: This method updates the instance attributes to store the
            merged GeoDataFrame with colored edges and the interactive Folium map.
        """
        # Get colors for edge styling
        unique_colors = iter(get_colors(len(self.points)+1))
        
        centroid = self.points[0].gdf.geometry.centroid.unary_union.centroid
        
        mymap = folium.Map(
            location=[centroid.y,centroid.x], 
            zoom_start=14
            )
        
        gdf_list = [point.gdf for point in self.points]
        
        for gdf in gdf_list:
            # Create a GeoJson object from the GeoPandas DataFrame
            geojson = chuck_geojson_constructor(gdf,unique_colors.__next__())
            # Add the GeoJson object to the map
            geojson.add_to(mymap)
        
        ## Separately color and render intersections between graphs
        if len(gdf_list) > 1:
            gdf_pairs = []
            ## Necessary to avoid expensive object comparisons with unhashable GeoFrames
            pair_checker = []
            ## get list of tuples of unique parings of graphs
            for i in range(len(gdf_list)):
                for j in range(i + 1, len(gdf_list)):
                    pair = (gdf_list[i], gdf_list[j])
                    pair_idx = (i,j)
                    reversed_pair_idx = (j,i)
                    if pair_idx not in pair_checker and reversed_pair_idx not in pair_checker:
                        pair_checker.append(pair_idx)
                        gdf_pairs.append(pair)
            
            executor = concurrent.futures.ProcessPoolExecutor(
                max_workers=get_num_cores()
                )
            with executor as executor:
                intersections = list(executor.map(
                    find_intersection,
                    gdf_pairs
                    )
                )

            # Combine the results into a single GeoDataFrame
            intersections = gpd.GeoDataFrame(pd.concat(intersections, ignore_index=True))
            if not intersections.empty: ##  skip if no intersections,
                geojson = chuck_geojson_constructor(intersections,unique_colors.__next__())
                # Add the GeoJson object to the map
                geojson.add_to(mymap)
            
        self.merged_interactive = mymap


    def add_markers_to_map(self):
        """
        Add markers (for points, edges, origin nodes) to the interactive folium map.

        This method annotates the different components of the folium interactive
        map, including input points, origin nodes, and edges between the 
        input points.
            
        Returns:
            None: The updated interactive map is stored in the 'merged_interactive'
            attribute of the rangeFinder object.
        """

        if self.show_elevations:
            try:
                func_timeout(MAX_SECONDS_TIMEOUT_ELEVATION, self.calculate_elevations)
            except FunctionTimedOut:
                timeout_error_msg = "Elevation could not be computed, please try without elevation."
                raise Exception(timeout_error_msg)

        # Add marker for the point with a popup containing the details
        unique_colors = get_colors(len(self.points))
        for i, point in enumerate(self.points):
            point_icon = folium.Icon(color="lightblue", 
                                     icon_color="black", 
                                     prefix="fa", 
                                     icon="fa-faucet")
            if point.point_type == "fire":
                point_icon = folium.Icon(color="orange",
                                         icon_color="black",
                                         prefix="fa", 
                                         icon="fa-fire")
            point_text = """\
                <html>
                    <b>Point</b>:({lat}, {long})<br>
                    <b>Hose length</b>: {length}m<br>
                    <b>Mode</b>: {mode}<br>
                    <b>Type</b>: {point_type}<br>
                </html>
                """.format(lat=point.lat, long=point.long, length=point.length, 
                        mode=point.mode, point_type=point.point_type)
            if self.show_elevations:
                point_text += f"<b>Elevation</b>: {int(point.elevation)}m"
            # Format the annotation text
            formatted_point_text = f"<h4 style='color:white;'>{point_text}</h4>"

            # To color the tooltip in the same color as the point's graph
            tooltip_style = f"""
            background-color:{unique_colors[i]}; padding: 0px; border-radius: 0px; border: 0;
            position: absolute
            """

            tooltip_div = f'<div style="{tooltip_style}">{formatted_point_text}</div>'
            iframe = folium.IFrame(html=tooltip_div, width="100%", ratio="100%", figsize=(6,2.5))
            point_popup = folium.Popup(iframe, parse_html=True)
            folium.Marker(location=(point.lat, point.long), 
                          popup=point_popup,
                          icon=point_icon
                          ).add_to(self.merged_interactive)

            # Add marker to indicate the actual origin node in the network
            folium.Circle(location=(point.origin.lat, point.origin.long), 
                          radius=3,
                          color="white",
                          fill=True,
                          fill_color=unique_colors[i],
                          fill_opacity=1,
                          tooltip=None
                          ).add_to(self.merged_interactive)

            # Add edges between each (centre) point in the graph
            for next_point in self.points[i+1:]:
                # Create and add Polyline segments for each point pair
                segment = folium.PolyLine(
                        locations=[(point.lat, point.long), (next_point.lat, next_point.long)],
                        # color=segment_colors[i % len(segment_colors)],
                        color="black",
                        # dash_array=[5],
                        weight=0.5
                    )

                segment.add_to(self.merged_interactive)

                if self.show_elevations:
                    # Add arrow marking the downhill elevation direction:
                    polyline_text = '\u21FE          ' # point -> next_point
                    if next_point.elevation > point.elevation: # next_point -> point
                        polyline_text = '\u21FD          '
                    style_attributes = {'fill': 'black', 'font-size': '24'} # 'font-weight': 'bold'
                    
                    plugins.PolyLineTextPath(
                        segment,
                        polyline_text,
                        repeat=True,
                        offset=7,
                        center=True,
                        attributes=style_attributes
                    ).add_to(self.merged_interactive)


    def create_interactive_map(self, map_style="OpenStreetMap"):
        """
        Generate an interactive Folium map displaying merged data.

        This function generates an interactive Folium map using merged 
        GeoDataFrames and customizes the map with unique edge colors for 
        each point. It includes markers for each point and its origin point.

        Args:
            map_style (str, optional): map layout style (default is "OpenStreetMap").
        """
        # Concatenate GeoDataFrames of all points
        self.merged_gdf = pd.concat([point.gdf for point in self.points], 
                                    ignore_index=True)
        # Add colors to edges
        self.add_edge_colors()

        # Define available map styles and remove the default style
        map_styles = ["OpenStreetMap", "Stamen Terrain", "Stamen Toner", 
                      "Stamen Water Color", "cartodbpositron", 
                      "cartodbdark_matter"]
        map_styles.remove(map_style)
        
        # Add additional map styles to the interactive map
        for style in map_styles:
            folium.TileLayer(style).add_to(self.merged_interactive)
        
        # Add a layer control to allow switching between map styles
        folium.LayerControl().add_to(self.merged_interactive)
        
        self.add_markers_to_map()

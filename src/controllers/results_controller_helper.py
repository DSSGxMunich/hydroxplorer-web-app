import json
import pandas as pd
from range_finder.rangeFinder import RangeFinder
from controllers.error_controller import *
from typing import Tuple

# Expected column headers for the points data
INPUT_TABLE_COLUMNS = [
      'latitude', 
      'longitude', 
      'hose_length', 
      'transportation_mode',
      'point_type'
      ]

# Maps the presentable strings from the webapp frontend to the osmnx strings
MODE_LABELS_TO_MODE_ID = {
    "Walking": "walk",
    "Cycling": "bike", 
    "Driving":"drive",
    "Service_Driving":"drive_service"
}

def input_string_to_df(input: str) -> Tuple[bool, pd.DataFrame]:
    """
    Parse a JSON input string into a pandas DataFrame.

    This function takes a JSON input string, parses it, and constructs a
    pandas DataFrame. It also extracts a boolean flag to indicate whether
    elevations should be displayed.

    Args:
        input (str): A JSON input string.

    Returns:
        Tuple[bool, pd.DataFrame]: A tuple containing two elements:
            - bool: A flag indicating whether to display elevations.
            - pd.DataFrame: A pandas DataFrame containing parsed data.

    Example:
        >>> {
        >>> "elevation": true,
        >>> "points": {
        >>>     "1": {
        >>>     "latitude": "48.140709",
        >>>     "longitude": "11.510707",
        >>>     "length": "111",
        >>>     "mode": "Walking",
        >>>     "point_type": "fire"
        >>> },
        >>> ...
        >>> }
        >>> }
    """

    input = json.loads(input)
    show_elevations = input["elevation"]
    # Parse string to bool
    if show_elevations == 'true':
        show_elevations = True
    elif show_elevations == True:
        pass
    else:
        show_elevations = False

    points = input["points"]
    df = pd.DataFrame.from_dict(points, orient="index")
    
    df.columns = INPUT_TABLE_COLUMNS
    # parsing column types
    df.iloc[:,0:3] = df.iloc[:,0:3].astype(float)
    df.iloc[:,[3,4]] = df.iloc[:,[3,4]].astype(str)
    df = df.convert_dtypes()

    # Mapping the transport mode values from the frontend strings
    df['transportation_mode'] = df['transportation_mode'].map(MODE_LABELS_TO_MODE_ID)
    return show_elevations, df


def pipeline_input_to_map_output(input:str):
    """
    Process a pipeline input string to generate an interactive Folium map.

    This function takes an input string, processes it to create an interactive
    Folium map, and returns the map as a Folium object.

    Args:
        input (str): A pipeline input string.

    Returns:
        folium.Map: An interactive Folium map.

    Example JSON input format:
        >>> {
        >>> "elevation": true,
        >>> "points": {
        >>>     "1": {
        >>>     "latitude": "48.140709",
        >>>     "longitude": "11.510707",
        >>>     "length": "111",
        >>>     "mode": "Walking",
        >>>     "point_type": "fire"
        >>> },
        >>> ...
        >>> }
        >>> }
    """
    show_elevations, points_df = input_string_to_df(input)
    add_constraints(points_df)

    rf = RangeFinder()
    rf.add_points(points_df)
    rf.show_elevations = show_elevations
    if rf.points:
        rf.create_interactive_map()
    return rf.merged_interactive

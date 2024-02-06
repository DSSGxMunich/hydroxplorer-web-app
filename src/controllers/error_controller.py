import traceback
import math
import numpy as np

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth's surface
    using the Haversine formula.

    The Haversine formula calculates the shortest distance between two points on the
    surface of a sphere, given their latitude and longitude in degrees.

    Args:
        lat1 (float): Latitude of the first point in degrees.
        lon1 (float): Longitude of the first point in degrees.
        lat2 (float): Latitude of the second point in degrees.
        lon2 (float): Longitude of the second point in degrees.

    Returns:
        float: The distance between the two points in kilometers.

    """
    R = 6371  # Earth radius in kilometers
    
    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Calculate differences
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


def check_distance(df):
    """
    Check if consecutive points in a DataFrame are within a specified distance threshold.

    This function calculates the distances between consecutive points in a dataFrame
    based on their latitude and longitude coordinates using the Haversine formula.
    It then checks if all calculated distances are within a specified threshold
    (in kilometers).

    Args:
        df (pandas.DataFrame): A DataFrame containing columns 'latitude' and 'longitude'
            with geographic coordinate values.

    Returns:
        bool: True if all consecutive points are within the distance threshold,
            False otherwise.

    Note:
        This function assumes that the DataFrame has been preprocessed with a shift
        operation to create 'pre_latitude' and 'pre_longitude' columns, as well as a
        'distance' column containing the distances between consecutive points.

    """

    df = df.copy()

    # Create shifted columns for latitude and longitude
    df["pre_latitude"] = df["latitude"].shift(+1)
    df["pre_longitude"] = df["longitude"].shift(+1)
    df = df[1:]
    df["distance"] = df.apply(lambda row: haversine(row["pre_latitude"], row["pre_longitude"], row["latitude"], row["longitude"]), axis=1)
    df = df.assign(distance_control=np.where(df["distance"] < 25, True, False))

            
    if all(df["distance_control"].values):
        return True
    else:
        return False
    

def add_constraints(df):
    """
    Apply constraints and validity checks to a dataFrame of points.

    This function applies several constraints and checks to a points dataFrame 
    to ensure that the data is valid and within acceptable limits.
    The constraints include checking the number of points, the validity of hose
    length values, and the maximum distance between consecutive points.

    Args:
        df (pandas.DataFrame): A DataFrame containing point data with columns
            'latitude', 'longitude', 'hose_length', and optionally other columns.

    Returns:
        None: If the data passes all constraints and checks.

    Raises:
        ValueError: If any of the constraints or checks fail, a ValueError is raised
            with a corresponding error message.

    Note:
        - The function checks that the DataFrame is not empty.
        - It limits the number of hydrants to 10 or fewer.
        - It validates the hose length values to be within the range [120, 5000].
        - It checks that each point is not more than 25 kilometers from the previously
          chosen one.
    
    """
    try:
        if df.empty:
            raise ValueError("No data was given")

        if df.shape[0] > 10:
            raise ValueError("More than 10 hydrants were given!")

        # to check validity of the given hose length
        lengths_values = df["hose_length"]

        if not all(120 <= value <= 5000 for value in lengths_values):
            raise ValueError("hose length is out of the range [120, 5000].")

        # check that each hydrant is not more than 25km from the previously chosen one
        if not check_distance(df):
            raise ValueError("At least one of the given hydrants is out of the range")
            
        return None

    except ValueError as ve:
        print(traceback.print_exc())
        raise ve

    
import pytest
from controllers.results_controller_helper import input_string_to_df, add_constraints
import pandas as pd


def test_empty_data_input():
    """
    Test the 'add_constraints' function with empty data.
    """
    df_1 = pd.DataFrame()
    with pytest.raises(ValueError) as exc_info:
        add_constraints(df_1)
    
    exception_raised = exc_info.value
    print(exception_raised)
    assert str(exception_raised) == "No data was given"


def test_numbers_of_hydrants():
    """
    Test the 'add_constraints' function with >10 points.
    """
    example_2 = """
    {
        "elevation": true,
        "points": {
            "1": {
                "latitude": "48.152349",
                "longitude": "11.58096",
                "length": "549",
                "mode": "Cycling",
                "pointType":"fire"
            },
            "2": {
                "latitude": "48.279603",
                "longitude": "11.771702",
                "length": "592",
                "mode": "Cycling",
                "pointType":"fire"
            },
            "3": {
                "latitude": "48.406857",
                "longitude": "11.962444",
                "length": "997",
                "mode": "Walking",
                "pointType":"hydrant"
            },
            "4": {
                "latitude": "48.534111",
                "longitude": "12.153186",
                "length": "4120",
                "mode": "Walking",
                "pointType":"hydrant"
            },
            "5": {
                "latitude": "48.661365",
                "longitude": "12.343928",
                "length": "1170",
                "mode": "Walking",
                "pointType":"hydrant"
            },
            "6": {
                "latitude": "48.788619",
                "longitude": "12.53467",
                "length": "4543",
                "mode": "Walking",
                "pointType":"hydrant"
            },
            "7": {
                "latitude": "48.915873",
                "longitude": "12.725412",
                "length": "2716",
                "mode": "Cycling",
                "pointType":"hydrant"
            },
            "8": {
                "latitude": "49.043127",
                "longitude": "12.916155",
                "length": "4087",
                "mode": "Cycling",
                "pointType":"hydrant"
            },
            "9": {
                "latitude": "49.170381",
                "longitude": "13.106897",
                "length": "514",
                "mode": "Cycling",
                "pointType":"hydrant"
            },
            "10": {
                "latitude": "49.297635",
                "longitude": "13.297639",
                "length": "4500",
                "mode": "Cycling",
                "pointType":"hydrant"
            },
            "11": {
                "latitude": "48.152349",
                "longitude": "11.58096",
                "length": "3755",
                "mode": "Walking",
                "pointType":"hydrant"
            }
        }
    }"""    
    _, df_2 = input_string_to_df(example_2)
    with pytest.raises(ValueError) as exc_info:
        add_constraints(df_2)
    
    exception_raised = exc_info.value
    print(exception_raised)
    assert str(exception_raised) == "More than 10 hydrants were given!"


def test_hose_length():
    """
    Test the 'add_constraints' function with invalid hose length.
    """
    example_3 = """
    {
        "elevation": false,
        "points": {
            "1": {
                "latitude": "48.152349",
                "longitude": "11.58096",
                "length": "7000",
                "mode": "Cycling",
                "pointType":"hydrant"
            }
        }
    }"""
    _, df_3 = input_string_to_df(example_3)
    with pytest.raises(ValueError) as exc_info:
        add_constraints(df_3)
    
    exception_raised = exc_info.value
    print(exception_raised)
    assert str(exception_raised) == "hose length is out of the range [120, 1500]."

example_4 = """
    {
        "elevation": false,
        "points": {
            "1": {
                "latitude": "48.152349",
                "longitude": "11.58096",
                "length": "800",
                "mode": "Walking",
                "pointType":"hydrant"
            },

            "2": {
                "latitude": "50.595615",
                "longitude": "6.972120",
                "length": "1080",
                "mode": "Cycling",
                "pointType":"fire"
            }
        }
}"""

def test_input_string_to_df():
    """
    Test the output of the function 'input_string_to_df'.
    """
    _, result_df = input_string_to_df(example_4)
    assert isinstance(result_df, pd.DataFrame)


def test_hydrants_locations():
    """
    Test the 'add_constraints' function with out of range point.
    """
    _, df_4 = input_string_to_df(example_4)
    with pytest.raises(ValueError) as exc_info:
        add_constraints(df_4)
    
    exception_raised = exc_info.value
    print(exception_raised)
    assert str(exception_raised) == "At least one of the given hydrants is out of the range"

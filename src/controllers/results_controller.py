import controllers.results_controller_helper as helper
import traceback
from flask import render_template
from uuid import uuid4
from add_buttons import get_map_with_buttons
from controllers.saved_maps import map_html_data
from time import time
from controllers.download_controller import cleanup_old_maps

def handle_input_to_output(input:str):
    output_html = None
    try:
        # Remove the previously loaded maps from the dictionary
        cleanup_old_maps()
        output_map = helper.pipeline_input_to_map_output(input)
        # Generate a unique identifier for this user's session
        session_id = str(uuid4())
        # Add download and home buttons to the html
        map_html, map_html_without_buttons = get_map_with_buttons(output_map, session_id)
        # Store the html without buttons in the dictionary for download
        map_html_data[session_id] = (map_html_without_buttons, time())

        output_html = render_template('map_template.html', map_html=map_html, session_id=session_id)
    except Exception as e:
        output_html = render_template('errors.html', variable=str(e),stack_trace=str(traceback.format_exc()))
    if output_html == None:
        output_html = render_template('errors.html', variable=str(
            """Sorry, no valid output map could be generated. 
            Try again with different locations."""
            ))
    return output_html

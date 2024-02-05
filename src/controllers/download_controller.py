from controllers.saved_maps import map_html_data
from flask import render_template, send_file
from io import BytesIO
import sys
from time import time

# Duration (in seconds) for deletion of previously loaded maps
MAX_SECONDS_TIMEOUT_DELETE = 3600

def _handle_download(request):
    # Retrieve the session identifier from the query parameters
    session_id = request.args.get('session_id')
    map_html_without_buttons,_ = map_html_data.get(session_id)

    if not map_html_without_buttons:
        error_message = "No map data available for download."
        return render_template('errors.html', variable=error_message)      
    
    # Return the map HTML as an attachment for download
    return send_file(
        BytesIO(map_html_without_buttons.encode()),
        as_attachment=True,
        download_name="output_map.html",
        mimetype="text/html"
    )
    
def map_cache_size():
    return sum(sys.getsizeof(value) for value in map_html_data.values())

def cleanup_old_maps():
    """
    Remove old map data from the 'map_html_data' dictionary based on a timeout threshold.

    This function iterates over the 'map_html_data' dictionary, which stores map data
    along with timestamps of their creation. It checks each map's timestamp against
    the 'MAX_SECONDS_TIMEOUT_DELETE' threshold to determine if the map data should be
    removed. If a map's timestamp exceeds the threshold, it is deleted from the dictionary.

    This cleanup process helps manage memory and resources by removing stale map data
    that is no longer needed.

    Returns:
        None
    """
    
    maintenance_cashe_size = 250000000 #0.25GB
    current_time = time()
    for session_id, (_, timestamp) in list(map_html_data.items()):
        if current_time - timestamp > MAX_SECONDS_TIMEOUT_DELETE:
            del map_html_data[session_id]
            
    print(map_cache_size())
            
    ## Keep deleting oldest caches until below size limit
    if len(list(map_html_data.keys())) > 1:
        while map_cache_size() > maintenance_cashe_size:
            del map_html_data[list(map_html_data.keys())[0]]
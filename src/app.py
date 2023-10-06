#!venv/bin/python
from flask import Flask, request, render_template, send_file
import traceback
from io import BytesIO
from controllers import results_controller

from controllers.saved_maps import map_html_data

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    """
    Render the homepage of the web application.

    This function handles incoming GET requests to the root URL ('/') and 
    renders the 'index.html' template, which serves as the homepage of the 
    web application.
    
    Returns:
        str: HTML content for the homepage.
    """
    return render_template('index.html')

@app.route('/results', methods=['POST'])
def post_payload():
    """
    Handle a POST request to '/results' endpoint and generate a map for the 
    input payload.

    This function handles incoming POST requests to the '/results' endpoint. 
    It begins by cleaning up old maps in the 'map_html_data' dictionary to 
    manage memory efficiently. Then, it processes the user's input payload, 
    generates a map using 'results_controller', and prepares the map for 
    download by adding download and homepage buttons.
        
    Returns:
        str: HTML content with the generated map and (homepage, download) buttons.
    """

    payload = request.form['submitButton']

    output_map = results_controller.handle_input_to_output(payload)
    return output_map


@app.route('/download', methods=['GET'])
def download():
    """
    Handle map download requests.

    This function handles incoming GET requests to the '/download' endpoint.
    It retrieves a map's HTML content from the 'map_html_data' dictionary using
    the provided session identifier. If the map's HTML is available, it is returned
    as a downloadable attachment named "output_map.html". If no map data is found,
    an error message is displayed.

    Returns:
        Flask.Response: A response object containing the map HTML as a downloadable
        attachment or an error message.
    """
    try:
        session_id = request.args.get('session_id')
        map_html_without_buttons,_ = map_html_data.get(session_id)

        if not map_html_without_buttons:
            error_message = "No map data available for download."
            raise Exception(error_message)
        
        # Return the map HTML as an attachment for download
        return send_file(
            BytesIO(map_html_without_buttons.encode()),
            as_attachment=True,
            download_name="output_map.html",
            mimetype="text/html"
        )
    except Exception as e:
        return render_template('errors.html', 
                               variable="""
                               Sorry, something went wrong with your 
                               download. Your session may have timed 
                               out.
                               Details: """+
                               str(e),
                               stack_trace=str(traceback.format_exc())
                               )  


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) # localhost:5000

#!venv/bin/python
"""
add_buttons.py: Adds download and home page buttons to a folium map.
"""

from folium import Element

def get_map_with_buttons(output_map, session_id):
    """
    Generate a Folium map with download and homepage buttons.

    This function takes a Folium map object and a session identifier and
    adds download and homepage buttons to the map's HTML content. It returns
    the modified map HTML with buttons and a copy of the map HTML without
    the buttons for saving.

    Args:
        output_map (folium.Map): A Folium map object.
        session_id (str): A unique session identifier.

    Returns:
        tuple: A tuple containing two elements:
            - str: The modified map HTML content with buttons.
            - str: A copy of the map HTML content without buttons for saving.
    """
        
    download_button_html = """
        <div style="position: fixed; top: 70px; right: 10px; z-index: 1000;">
            <a href="#" class="btn btn-primary btn-lg" id="download-button" style="background-color: black;"
            data-toggle="tooltip" data-placement="top" title="Download map">
                <i class="fas fa-download"></i>
            </a>
        </div>
        <script>
            // JavaScript to handle the download button click
            document.getElementById('download-button').addEventListener('click', function() {
                // Construct the download link with the session ID
                var downloadLink = document.createElement('a');
                downloadLink.href = '/download?session_id={session_id}';
                downloadLink.click();
            });
        </script>
        """

    homepage_button_html = """
        <div style="position: fixed; top: 120px; right: 10px; z-index: 1000;">
            <a href="/" class="btn btn-primary btn-lg" id="homepage-button" style="background-color: black;"
            data-toggle="tooltip" data-placement="top" title="Return to homepage">
                <i class="fas fa-left-long"></i>
            </a>
        </div>
        <script>
            // JavaScript to handle the homepage button click
            document.getElementById('homepage-button').addEventListener('click', function() {
                window.location.href = '/'; // Redirect to the homepage
            });
        </script>
        """
        
        # Add the download button HTML to the map's HTML
    output_map.get_root().html.add_child(Element(download_button_html))

    # Add the homepage button HTML to the map's HTML
    output_map.get_root().html.add_child(Element(homepage_button_html))

    # Convert the Folium map to HTML
    map_html = output_map.get_root().render()

    # Create a copy of the map without the download and home buttons (for saving)
    map_html_without_buttons = map_html.replace(download_button_html, "").replace(homepage_button_html, "")

    return map_html, map_html_without_buttons

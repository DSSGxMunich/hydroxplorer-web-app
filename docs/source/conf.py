# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'DSSGx Fire Hydrant Range Finder'
copyright = '2023, DSSGx Fire Hydrant Range Finder Team'
author = 'DSSGx Fire Hydrant Range Finder Team'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.todo", "sphinx.ext.viewcode", "sphinx.ext.autodoc", "sphinx.ext.napoleon"]

napoleon_google_docstring = True
napoleon_use_param = False
napoleon_use_ivar = True
add_module_names = False

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = "assets/dssgx_main.png"
html_theme_options = {
    "logo_only": True,
    "display_version": True,
    "style_nav_header_background": "white",
    "collapse_navigation": False,
    "analytics_anonymize_ip": True,
}

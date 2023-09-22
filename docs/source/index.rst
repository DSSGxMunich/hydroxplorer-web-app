.. image:: assets/dssg_cover.png
  :alt: DSSG Cover

.. image:: assets/official_logo_de.png
  :alt: Fire Hydrant Range Finder Logo

=============================================
DSSGx Fire Hydrant Range Finder Documentation
=============================================

This is the documentation for the DSSGx Fire Hydrant Range Finder project.

Usability
=========
Our objective is to offer the most efficient route to the nearest water source from a chosen location on the map.

Below is the homepage of our web application:

.. image:: assets/homepage.png
  :alt: Fire Hydrant Range Finder Homepage

Firstly, you can add a point of interest in two ways:

**Interactively**: Double-click on the point of interest on the map.

**Search**: Use the  search button and type the desired address.

As soon as you select a point on the map, a pop-up window will appear with the following required input:

1. **Hose Length**: Expects a numerical value.

2. **Transport Mode**:
  *Walking*: Route optimized for walkers.

  *Driving*: Driving directions for motor vehicles.

  *Cycling*: Fits Portable Fire Pump Trolley.

  *Service Driving*: Drivable public streets (incl. service roads).

3. **Point Type**: Select whether the point is a fire or a water source.

Secondly, use the ``Submit`` button to use the tool. In case of an error, keep in mind the input values restriction.

Input Values Restriction:
=========================

* Hose length: 120 to 5000 meters.
* Max 10 points on the map.
* Point-to-point distance limit: 20,000 meters.
* For more information and detailed usage instructions, refer to our `GitHub repository <https://github.com/DSSGxMunich/hydroxplorer-web-app/>`_.

.. toctree::
   :maxdepth: 4
   :caption: Contents:

   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

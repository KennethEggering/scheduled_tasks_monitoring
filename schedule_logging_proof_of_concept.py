import inspect
import html
import os
import requests
import socket
import time
from arcgis.gis import GIS
from arcgis.features import Feature
from math import pi, log, tan

gis = GIS("pro") ## use "home" in AGO Notebooks, use "pro" in ArcGIS Pro

## The following Code is now public on Github here:
### https://github.com/KennethEggering/scheduled_tasks_monitoring/blob/main/schedule_logging_proof_of_concept.py
### Code initially developed here: C:\Users\keggering\Projects\Python_Toolboxes\AGO_Backups\schedule_logging_proof_of_concept.py

def create_geometry():
    """
    Editing/including geometry in Feature-Layer ADDS is not all that important. This function is designed to return
    the coords for Boise, ID if it can't get them from requests.get().

    Tries to get the approximate location based on IP, else returns Boise, ID in Web Mercator

    """

    def latlon_to_web_mercator(in_lat, in_lon):
        origin_shift = 2 * pi * 6378137 / 2.0
        mx = in_lon * origin_shift / 180.0
        my = log(tan((90 + in_lat) * pi / 360.0)) / (pi / 180.0)
        my = my * origin_shift / 180.0
        return mx, my

    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            loc = data.get("loc")
            if loc:
                lat_str, lon_str = loc.split(",")
                lat, lon = float(lat_str), float(lon_str)
                x, y = latlon_to_web_mercator(lat, lon)
                geom = {"x": x, "y": y, "spatialReference": {"wkid": 102100, "latestWkid": 3857}}
                print(f"IP-based location: lat={lat}, lon={lon}")
            else:
                raise ValueError("Missing 'loc' in response")
        else:
            raise ConnectionError("Non-200 response")
    except Exception as e:
        print(f"Falling back due to error: {e}")
        # Boise, ID fallback
        geom = {"x": -12957900, "y": 5411910, "spatialReference": {"wkid": 102100, "latestWkid": 3857}}

    print("Geometry:", geom)
    return geom


### TODO: Create a function that can be pulled into misc Toolboxes etc.
### https://stantec.maps.arcgis.com/home/item.html?id=42b6d2ccea08441395d23250ec35b335 <--- Feature-Layer for logging to
scheduled_tasks_log_item = gis.content.get("42b6d2ccea08441395d23250ec35b335")
scheduled_tasks_log_fLyr = scheduled_tasks_log_item.layers[0]
scheduled_tasks_props = scheduled_tasks_log_fLyr.properties
scheduled_tasks_flyr_sr = scheduled_tasks_props.extent["spatialReference"]
scheduled_tasks_flyr_name = scheduled_tasks_props["name"]

host_name = socket.gethostname()
ymdhm = time.strftime("%Y%m%d__%H%M")

### define feature-layer fields
file_that_executed = "File_That_Executed_git_script"
log_note = "Log_Note"
machine_where_scheduled = "Machine_where_scheduled"
toolbox_name = "Toolbox_Name"

print(f"Feature-Layer '{scheduled_tasks_flyr_name}' has a spatial-reference of {scheduled_tasks_flyr_sr}")
# Define the point geometry and attributes


cur_dir = os.curdir

try:
    file_ = os.path.abspath(inspect.getfile(inspect.currentframe()))
except Exception as f_ex:
    file_ = f"Unknown file due to error: {f_ex}"


geometry = create_geometry()
attributes = {
    log_note: f"updated successfully {ymdhm}",
    machine_where_scheduled: host_name,
    toolbox_name: "proof of concept script",
    file_that_executed: html.escape(file_),
    }

# Create and add the feature
feature = Feature(geometry=geometry, attributes=attributes)
scheduled_tasks_log_fLyr.edit_features(adds=[feature])

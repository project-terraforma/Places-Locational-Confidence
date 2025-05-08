from helperfuncs import *

import overturemaps as om
from overturemaps import core
import overturemaps
import pandas
import geopandas as gpd
from shapely import wkb
from shapely.geometry import Point
from lonboard import Map, PolygonLayer, ScatterplotLayer
import ipywidgets as widgets
import numpy as np
from IPython.display import display
from rapidfuzz import process, fuzz 
import argparse
import sys
from tqdm import tqdm

if len(sys.argv) <2:
    raise ValueError("Please provide a bounding box in the format xmin,ymin,xmax,ymax")
# Parse command-line arguments
parser = argparse.ArgumentParser(description="Generate confidence metrics for locations.")
parser.add_argument("bbox",
                    type=str,
                    help="Bounding box as a string in the format: bbox=(xmin,ymin,xmax,ymax)")
args = parser.parse_args()

input_str = args.bbox

# Validate the format "bbox=(...)"
if not (input_str.startswith("bbox=(") and input_str.endswith(")")):
    raise ValueError(
        f"Bounding box argument must be in the format bbox=(xmin,ymin,xmax,ymax). "
        f"Example: bbox=(-74.0,40.0,-73.0,41.0). You provided: '{input_str}'"
    )

# Extract the coordinate string part, e.g., "-74.0,40.0,-73.0,41.0"
coords_str = input_str[len("bbox=("):-1]

try:
    # Split the coordinate string by comma, strip whitespace from each part, and convert to float
    str_values = coords_str.split(',')
    if not all(str_values): # Check for empty strings resulting from "bbox=(,,)" or "bbox=(1,,2,3)"
        raise ValueError("Coordinate string contains empty parts.")
    float_values = [float(s.strip()) for s in str_values]
    if(float_values[0] > float_values[2] or float_values[1] > float_values[3]):
        raise ValueError("Invalid bounding box: xmin must be less than xmax and ymin must be less than ymax")
except ValueError as e: # Catches errors from float() conversion or the custom check above
    raise ValueError(
        f"Invalid numeric value or format in bounding box coordinates: '{coords_str}'. "
        f"Ensure all coordinates are valid numbers separated by commas. Original error detail: {e}"
    )

# The variable `bbox` is expected to be a tuple of floats by the subsequent code.
# The existing code after this selection will check if len(bbox) is 4.
bbox = tuple(float_values)
if len(bbox) != 4:
    raise ValueError("Bounding box must have exactly four values: xmin, ymin, xmax, ymax")
if bbox[0] > bbox[2] or bbox[1] > bbox[3]:
    raise ValueError("Invalid bounding box: xmin must be less than xmax and ymin must be less than ymax")

print(f"Bounding box: {bbox}")
print("Loading places data...")

places_dataset = core.geodataframe("place", bbox=bbox)

print(f'Found {len(places_dataset)} places in the bounding box.')

print("Loading address data...")
address_dataset = core.geodataframe("address",bbox=bbox)
    

print(f'Found {len(address_dataset)} addresses in the bounding box.')


addr_dict, places_dict = dataframes_to_dicts(address_dataset,places_dataset)

p2a_distances, a2p_distances = find_fuzzy_matches_and_distances(places_dict, addr_dict, threshold=80)
import tqdm
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

def compare_number_and_first(places_dict,addr_dict):
    places_dict_processed = {}
    addr_dict_processed = {}
    distances = {}
    for place, (px,py) in places_dict.items():
        place = place.split(' ')
        place = ' '.join(place[0:2])
        #print(f"Processed place: {place}")
        places_dict_processed[place] = (px,py)

    for addr, (ax,ay) in addr_dict.items():
        addr = addr.split(' ')
        addr = ' '.join(addr[0:2])
        addr_dict_processed[addr] = (ax,ay)
    for place, (px,py) in places_dict_processed.items():
        if place in addr_dict_processed.keys():
            addr = addr_dict_processed[place]
            dist = get_dist((px,py),addr)
            distances[place] = (place,dist)
            #print(f"Place: {place}, Address: {addr}, Distance: {dist}")
    return distances


def get_dist(point,address):
    #print(f"Point: {point} Address: {address} !!")
    dist = np.sqrt((point[0] - address[0])**2 + (point[1] - address[1])**2)
    #print(f"Distance between {point} and {address}: ", dist)
    return dist


def dataframes_to_dicts(adf,pdf):
    # build uppercase address strings
    address_list = (adf['number'] + ' ' + adf['street']).str.upper().tolist()

    # pair each address string with its (lon, lat) tuple from the geometry column
    address_dict = {}
    print("Building address_dict...")
    for addr, pt in tqdm.tqdm(zip(address_list, adf.geometry), total=len(address_list), desc="Processing addresses"):
        address_dict[addr.upper()] = (pt.x, pt.y)


    # extract the “freeform” string from each place’s addresses and uppercase it
    places_list_series = (
    pdf['addresses']
    .apply(lambda lst: lst[0].get('freeform', '') if lst else '')
    .str.split(',', n=1).str[0]
    .str.strip()
    .str.upper()
    )
    
    places_list = places_list_series.tolist()

    # now build a dict mapping each freeform address to its (lon, lat)
    places_dict = {}
    print("Building places_dict...")
    # We need to iterate carefully here because of the `if addr != None` condition.
    # We can iterate through the series and geometry together.
    for addr, pt in tqdm.tqdm(zip(places_list_series, pdf.geometry), total=len(places_list_series), desc="Processing places"):
        if pandas.notna(addr) and addr != '': # Check for NaN and empty strings after processing
            places_dict[addr] = (pt.x, pt.y)


    return address_dict, places_dict



def normalize_distances(distances):
    """Normalizes a list of distances to a scale between 0 and 1."""
    if not distances:
        return []
    distances_arr = np.array(distances)
    min_dist = np.min(distances_arr)
    max_dist = np.max(distances_arr)
    if max_dist == min_dist:
        # Avoid division by zero if all distances are the same
        # Return array of zeros or handle as appropriate for the context
        return np.zeros_like(distances_arr)
    normalized = (distances_arr - min_dist) / (max_dist - min_dist)
    return normalized.tolist() 



def find_fuzzy_matches_and_distances(places_dict, address_dict, threshold=90):
    """
    Finds fuzzy matches between place addresses and official addresses (case-insensitive)
    and calculates the distance between matched pairs. Uses rapidfuzz.

    Args:
        places_dict (dict): Dictionary mapping place addresses (str) to coordinates (tuple).
        address_dict (dict): Dictionary mapping official addresses (str) to coordinates (tuple).
        threshold (int): Minimum similarity score (0-100) for a match.

    Returns:
        dict: Dictionary mapping original place addresses to details including
              the matched original official address, score, distance, and coordinates.
        dict: Dictionary mapping original official addresses to details including
              the matched original place address, score, distance, and coordinates.
    """
    p2a_distances_fuzzy = {}
    a2p_distances_fuzzy = {}

    if not places_dict or not address_dict:
        print("Warning: One or both input dictionaries are empty. Cannot perform matching.")
        return p2a_distances_fuzzy, a2p_distances_fuzzy

    # Create uppercase versions for matching, storing original key and coordinates
    places_dict_upper = {k.upper(): (v, k) for k, v in places_dict.items() if isinstance(k, str)}
    address_dict_upper = {k.upper(): (v, k) for k, v in address_dict.items() if isinstance(k, str)}

    place_address_keys_upper = list(places_dict_upper.keys())
    address_address_keys_upper = list(address_dict_upper.keys())

    if not place_address_keys_upper or not address_address_keys_upper:
        print("Warning: One or both dictionaries became empty after filtering non-string keys or uppercasing. Cannot perform matching.")
        return p2a_distances_fuzzy, a2p_distances_fuzzy

    print(f"Starting fuzzy matching (case-insensitive) for {len(place_address_keys_upper)} place addresses against {len(address_address_keys_upper)} official addresses...")
    # Match places to addresses (using uppercase)
    for place_addr_upper, (place_coord, place_addr_orig) in tqdm.tqdm(places_dict_upper.items(), desc="Matching Places <-> Addresses (Places to Addresses)"):
        # Process the address to improve matching: remove initial numbers but keep later ones
        # For example: "123 MAIN ST" -> "MAIN ST", but keep "COUNTY ROAD 74-82" intact
        try:
            parts = place_addr_upper.split()
            # Skip past initial numeric parts (house/building numbers)
            i = 0
            while i < len(parts) and parts[i].isdigit():
                i += 1
            
            # Extract the non-initial-numeric parts (street name, etc.)
            if i > 0 and i < len(parts):
                # Found a meaningful street part after initial numbers
                place_addr_upper = ' '.join(parts[i:])
        except Exception:
            # In case of error, keep the original
            pass
        # Find the best match in address_dict_upper above the threshold
        # Using token_sort_ratio handles word order differences well for addresses.
        best_match_upper, score, _ = process.extractOne(place_addr_upper, address_address_keys_upper, scorer=fuzz.token_sort_ratio)

        if score >= threshold:
            matched_addr_coord, matched_addr_orig = address_dict_upper[best_match_upper]
            distance = get_dist(place_coord, matched_addr_coord)
            # Store results using original keys
            p2a_distances_fuzzy[place_addr_orig] = {
                'matched_address': matched_addr_orig,
                'score': score,
                'distance': distance,
                'place_coord': place_coord,
                'address_coord': matched_addr_coord
            }


    print(f"Found {len(p2a_distances_fuzzy)} potential matches mapping places to addresses (score >= {threshold}).")

    print(f"Starting fuzzy matching (case-insensitive) for {len(address_address_keys_upper)} official addresses against {len(place_address_keys_upper)} place addresses...")
    # Match addresses to places (using uppercase)
    for address_addr_upper, (address_coord, address_addr_orig) in address_dict_upper.items():
        # Find the best match in places_dict_upper above the threshold
        best_match_upper, score, _ = process.extractOne(address_addr_upper, place_address_keys_upper, scorer=fuzz.token_sort_ratio)

        if score >= threshold:
            matched_place_coord, matched_place_orig = places_dict_upper[best_match_upper]
            # Check if the reverse match (place -> address) already calculated this pair using original keys
            if matched_place_orig in p2a_distances_fuzzy and p2a_distances_fuzzy[matched_place_orig]['matched_address'] == address_addr_orig:
                 # Retrieve distance calculated previously
                 distance = p2a_distances_fuzzy[matched_place_orig]['distance']
            else:
                 # Calculate distance if not found in the p2a results
                 distance = get_dist(address_coord, matched_place_coord)

            # Store results using original keys
            a2p_distances_fuzzy[address_addr_orig] = {
                'matched_place': matched_place_orig,
                'score': score,
                'distance': distance,
                'address_coord': address_coord,
                'place_coord': matched_place_coord
            }

    print(f"Found {len(a2p_distances_fuzzy)} potential matches mapping addresses to places (score >= {threshold}).")
    return p2a_distances_fuzzy, a2p_distances_fuzzy
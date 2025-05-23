import streamlit as st
from helperfuncs import dataframes_to_dicts, find_fuzzy_matches_and_distances, compare_number_and_first
import overturemaps.core
import pandas
import geopandas as gpd
import json # Added for json.dumps
# numpy might be needed if helperfuncs returns specific numpy types that need handling,
# but st.json is usually robust.
# import numpy as np

# --- Streamlit UI Configuration ---
st.set_page_config(layout="wide")
st.title("Overture Maps Location Confidence Metrics")

# --- Sidebar for Inputs ---
st.sidebar.header("Settings")

# Bounding box input
default_bbox_str = "-117.05,33,-117,33.05"
bbox_str_input = st.sidebar.text_input(
    "Bounding Box (xmin,ymin,xmax,ymax):",
    value=default_bbox_str,
    help="Enter coordinates as comma-separated values: xmin,ymin,xmax,ymax"
)

# Fuzzy matching toggle
use_fuzzy_matching = st.sidebar.checkbox("Use Fuzzy Matching Mode", value=False)

# Process button
process_button = st.sidebar.button("Process Data")

# --- Main Application Logic ---
if process_button:
    bbox = None
    results_to_download = None # Initialize variable to store results for download
    results_filename = "results.json" # Default filename

    try:
        # Parse and validate the bounding box string
        coords_list_str = bbox_str_input.split(',')
        if len(coords_list_str) != 4:
            raise ValueError("Bounding box must have exactly four values: xmin, ymin, xmax, ymax.")
        
        stripped_coords = [s.strip() for s in coords_list_str]
        if not all(stripped_coords): # Check for empty strings after stripping
            raise ValueError("Coordinate string contains empty parts. Ensure all four values are provided.")

        float_values = [float(s) for s in stripped_coords]
        
        # Optional: Validate coordinate ordering (xmin < xmax, ymin < ymax)
        # if float_values[0] >= float_values[2] or float_values[1] >= float_values[3]:
        #     raise ValueError("Invalid bounding box: xmin must be less than xmax, and ymin must be less than ymax.")
            
        bbox = tuple(float_values)
        st.write(f"Processing for Bounding Box: {bbox}")

    except ValueError as e:
        st.error(f"Invalid bounding box input: {e}. Please use the format: xmin,ymin,xmax,ymax")
        st.stop() # Halt execution if bbox is invalid

    try:
        # Load places data
        with st.spinner("Loading places data..."):
            places_dataset = overturemaps.core.geodataframe("place", bbox=bbox)
        st.write(f'Found {len(places_dataset)} places in the bounding box.')
        if not places_dataset.empty:
            st.caption("Sample Places Data:")
            st.dataframe(places_dataset.head())
        elif len(places_dataset) == 0:
            st.info("No places found for the given bounding box.")


        # Load address data
        with st.spinner("Loading address data..."):
            address_dataset = overturemaps.core.geodataframe("address", bbox=bbox)
        st.write(f'Found {len(address_dataset)} addresses in the bounding box.')
        if not address_dataset.empty:
            st.caption("Sample Address Data:")
            st.dataframe(address_dataset.head())
        elif len(address_dataset) == 0:
            st.info("No addresses found for the given bounding box.")

        # Proceed only if data is available
        if places_dataset.empty or address_dataset.empty:
            st.warning("One or both datasets (places, addresses) are empty. Cannot perform matching.")
            st.stop()

        # Convert dataframes to dictionaries using helper function
        # This assumes dataframes_to_dicts is robust and handles potential empty inputs if not caught above.
        addr_dict, places_dict = dataframes_to_dicts(address_dataset, places_dataset)
        
        if not places_dict:
            st.warning("Places dictionary is empty after conversion. Cannot proceed with matching.")
            st.stop()
        if not addr_dict:
            st.warning("Address dictionary is empty after conversion. Fuzzy matching might not yield results.")
            # For conventional matching, addr_dict might not be strictly necessary depending on compare_number_and_first logic

        st.write(f"Number of entries in places dictionary: {len(places_dict)}")
        st.write(f"Number of entries in address dictionary: {len(addr_dict)}")

        # Perform matching based on user's choice
        if use_fuzzy_matching:
            st.subheader("Fuzzy Matching Results")
            if not addr_dict: # Fuzzy matching needs addresses
                 st.warning("Address dictionary is empty, cannot perform fuzzy matching.")
                 st.stop()
            with st.spinner("Finding fuzzy matches and distances..."):
                p2a_distances, a2p_distances = find_fuzzy_matches_and_distances(places_dict, addr_dict, threshold=80)
            
            if not p2a_distances and not a2p_distances:
                st.write("No fuzzy matches found.")
            elif len(p2a_distances) > len(a2p_distances):
                st.write(f"Place-to-Address Distances (Count: {len(p2a_distances)}):")
                st.json(p2a_distances, expanded=False) # Show collapsed by default for large JSON
                results_to_download = p2a_distances
                results_filename = "fuzzy_p2a_distances.json"
            else: # This covers len(a2p_distances) >= len(p2a_distances)
                st.write(f"Address-to-Place Distances (Count: {len(a2p_distances)}):")
                st.json(a2p_distances, expanded=False)
                results_to_download = a2p_distances
                results_filename = "fuzzy_a2p_distances.json"

        else: # Conventional matching
            st.subheader("Conventional Matching Results")
            with st.spinner("Comparing place and address data (conventional)..."):
                distances = compare_number_and_first(places_dict, addr_dict)
            
            if distances:
                coverage = (len(distances) / len(places_dict)) * 100 if len(places_dict) > 0 else 0
                st.write(f"Distances found for {len(distances)} places. Coverage: {coverage:.2f}%")
                st.json(distances, expanded=False)
                results_to_download = distances
                results_filename = "conventional_distances.json"
            else:
                st.write("No conventional matches found.")
        
        # Add download button if there are results
        if results_to_download:
            json_string = json.dumps(results_to_download, indent=4)
            st.download_button(
                label="Download Results as JSON",
                data=json_string,
                file_name=results_filename,
                mime="application/json"
            )

    except ImportError:
        st.error("Failed to import helper functions. Ensure 'helperfuncs.py' is in the same directory and contains the necessary functions.")
    except Exception as e:
        st.error(f"An error occurred during data processing: {e}")
        # For more detailed debugging, you could uncomment the following:
        # import traceback
        # st.error(traceback.format_exc())
else:
    st.info("Adjust settings in the sidebar and click 'Process Data' to begin.")


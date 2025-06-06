import streamlit as st
from helperfuncs import dataframes_to_dicts, find_fuzzy_matches_and_distances, compare_number_and_first
import overturemaps.core
import pandas as pd
import geopandas as gpd
#import json # Added for json.dumps
import numpy as np
import pydeck as pdk
from lonboard import Map, PolygonLayer, ScatterplotLayer
# numpy might be needed if helperfuncs returns specific numpy types that need handling,
# but st.json is usually robust.
# import numpy as np

# --- Streamlit UI Configuration ---
st.set_page_config(layout="wide")
st.title("Overture Maps Location Confidence Metrics")

# --- Sidebar for Inputs ---
st.sidebar.header("Settings")

# Bounding box input
default_bbox_str = " -122.07097184198727, 36.92905573190209, -121.9761711508025, 37.018639643476284"
bbox_str_input = st.sidebar.text_input(
    "Bounding Box (xmin,ymin,xmax,ymax):",
    value=default_bbox_str,
    help="Enter coordinates as comma-separated values: xmin,ymin,xmax,ymax"
)

# Fuzzy matching toggle
use_fuzzy_matching = st.sidebar.checkbox("Use Fuzzy Matching Mode", value=True)

# Process button
process_button = st.sidebar.button("Process Data")

# --- Main Application Logic ---
st.markdown("""
**Welcome to the Overture Maps Location Confidence Metrics App!**

This app allows you to analyze and visualize location data within a specified bounding box.
Under the hood, it uses fuzzy string matching to match Overture POI's with their official address, and determining locational confidence from that distance.

For now, please use fuzzy matching mode (it's much better than conventional methods!).
""")
if process_button:
    st.header("Processing Data...")
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
        if not places_dataset.empty:
            st.success("Places Data Loaded Successfully", icon="✅")
            st.write(f'Found {len(places_dataset)} places in the bounding box.')
            st.caption("Sample Places Data:")
            st.dataframe(places_dataset.head())
        elif len(places_dataset) == 0:
            st.info("No places found for the given bounding box.")


        # Load address data
        with st.spinner("Loading address data..."):
            address_dataset = overturemaps.core.geodataframe("address", bbox=bbox)
        
        st.success("Address Data Loaded Successfully", icon="✅")
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
                p2a_distances = find_fuzzy_matches_and_distances(places_dict, addr_dict, threshold=80)
             #Add Map Visualization
            st.subheader("Map Visualization | Places (Red) and Addresses (Blue)")
            pdk_places_data = [
                {"lon": coord[0], "lat": coord[1], "name": str(places_dataset.addresses.iloc[i][0]['freeform'])} for i, coord in enumerate(places_dataset.geometry.apply(lambda geom: [geom.x, geom.y]).tolist())
            ]
            # for i in range(len(pdk_places_data)):
            #     if places_dataset.addresses.iloc[i] is None:
            #         pdk_places_data[i]["name"] = "Unknown Place"
            #     pdk_places_data[i]["name"] = places_dataset.addresses.iloc[i]
            pdk_addresses_data = [
                {"lon": coord[0], "lat": coord[1], "name": str(address_dataset.number.iloc[i]) + " " + str(address_dataset.street.iloc[i])} for i, coord in enumerate(address_dataset.geometry.apply(lambda geom: [geom.x, geom.y]).tolist())
            ]
            # for i in range(len(pdk_addresses_data)):
            #     if address_dataset.number.iloc[i] is None or address_dataset.street.iloc[i] is None:
            #         pdk_addresses_data[i]["name"] = "Unknown Address"
            #     pdk_addresses_data[i]["name"] = str(address_dataset.number.iloc[i]) + " " + str(address_dataset.street.iloc[i])
            # Create line data for connections between places and matched addresses
            line_data = []
            if use_fuzzy_matching and len(p2a_distances) > 0:
                for place_id, place_data in p2a_distances.items():
                    print(f"Processing match for place: {place_id}")
                    if 'place_coord' in place_data and 'matched_address' in place_data:
                        print(f" - Found matched address: {place_data['matched_address']}")
                    if 'place_coord' in place_data and 'address_coord' in place_data:

                        line_data.append({
                            "source_lon": place_data['place_coord'][0],
                            "source_lat": place_data['place_coord'][1],
                            "target_lon": place_data['address_coord'][0],
                            "target_lat": place_data['address_coord'][1],
                        })

            event = st.pydeck_chart(
                pdk.Deck(
                map_style=None,
                initial_view_state=pdk.ViewState(
                    latitude= (bbox[1]+bbox[3]) / 2,  # Center latitude
                    longitude=(bbox[0]+bbox[2]) / 2,  # Center longitude
                    zoom=13,
                    pitch=0,
                ),
                # Add layers to the map
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=pdk_places_data,
                        get_position=["lon", "lat"],
                        get_radius=5,
                        get_fill_color=[171, 7, 29, 160],  # Red for places with transparency
                        pickable=True,  # Enable picking for interaction 
                        auto_highlight=True,  # Highlight on hover
                ),
                pdk.Layer(
                        "ScatterplotLayer",
                        data=pdk_addresses_data,
                        get_position=["lon", "lat"],
                        get_radius=5,
                        get_fill_color=[52, 122, 235, 160],  # Blue for addresses with transparency
                        pickable=True,  # Enable picking for interaction
                        auto_highlight=True,  # Highlight on hover
                ),
                pdk.Layer(
                    "LineLayer",
                    data=line_data,
                    get_source_position=["source_lon", "source_lat"],
                    get_target_position=["target_lon", "target_lat"],
                    get_color=[255, 255, 255, 160],  # white lines for connections
                    get_width=2
                ) if line_data else None
                ], tooltip={
                    "text": "{name}\nCoordinates: [{lon}, {lat}]"
                },
                ), selection_mode="multi-object"
            )
            event.selection
            if not p2a_distances:
                st.write("No fuzzy matches found.")
                st.stop()
            st.write(f"Place-to-Address Distances (Count: {len(p2a_distances)}): (Coverage: {len(p2a_distances) / len(places_dict) * 100:.2f}%)")
            # Calculate statistics for the table
            distances = [float(data['distance'].replace('m', '')) for data in p2a_distances.values()]
            distance_scores = [float(data['distance_score']) for data in p2a_distances.values()]
            matched_scores = [float(data['name_match_score']) for data in p2a_distances.values()]

            # Create statistics table
            stats_df = pd.DataFrame({
                'Distance (m)': [np.min(distances), np.mean(distances), np.max(distances)],
                'Distance Score': [np.min(distance_scores), np.mean(distance_scores), np.max(distance_scores)],
                'Matched Score': [np.min(matched_scores), np.mean(matched_scores), np.max(matched_scores)]
            }, index=['Min', 'Average', 'Max'])

            st.subheader("Summary Statistics")
            st.dataframe(stats_df.round(2))
            st.json(p2a_distances, expanded=1) # Show collapsed by default for large JSON
            results_to_download = p2a_distances
            results_filename = "fuzzy_p2a_distances.json"
            st.balloons()
            st.balloons()
            st.balloons()
        else: # Conventional matching
            st.subheader("Conventional Matching Results")
            with st.spinner("Comparing place and address data (conventional)..."):
                distances = compare_number_and_first(places_dict, addr_dict)
            
            if distances:
                coverage = (len(distances) / len(places_dict)) * 100 if len(places_dict) > 0 else 0
                st.write(f"Distances found for {len(distances)} places. Coverage: {coverage:.2f}%")
                st.json(distances, expanded=1)
                results_to_download = distances
                results_filename = "conventional_distances.json"
            else:
                st.write("No conventional matches found.")
        #  # Add download button if there are results
        # if results_to_download:
        #     json_string = json.dumps(results_to_download, indent=4)
        #     st.download_button(
        #         label="Download Results as JSON",
        #         data=json_string,
        #         file_name=results_filename,
        #         mime="application/json"
        #     )

    
       
       
    except ImportError:
        st.error("Failed to import helper functions. Ensure 'helperfuncs.py' is in the same directory and contains the necessary functions.")
    except Exception as e:
        st.error(f"An error occurred during data processing: {e}")
        # For more detailed debugging, you could uncomment the following:
        # import traceback
        # st.error(traceback.format_exc())
else:
    st.info("Adjust settings in the sidebar and click 'Process Data' to begin.")

st.write("Made with ❤️ by [Cyrus Correll](https://www.linkedin.com/in/cyruscorrell/) for Overture Maps through CRWN 102. Special thanks to Professor Rao and Jens Goossens!")

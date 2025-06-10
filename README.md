# Cyrus Correll | Project C: Developing Locational Confidence Metric for POI's

Check out streamlit website here: [`https://places-locational-confidence-metric.streamlit.app/`](https://places-locational-confidence-metric.streamlit.app/)



## Core Application Files

### `helperfuncs.py` - Core Functionality Module
This module contains the essential functions for processing and matching location data:

**Key Functions:**
- **`dataframes_to_dicts()`**: Converts Overture Maps place and address GeoDataFrames into dictionaries mapping address strings to coordinates. Handles data cleaning and normalization.
- **`find_fuzzy_matches_and_distances()`**: Uses RapidFuzz library to perform intelligent string matching between place addresses and official addresses with configurable similarity thresholds (default 90%). Calculates distances and assigns location confidence scores using logarithmic decay (1.0 for <5m, 0.0 for >200m).
- **`compare_number_and_first()`**: Legacy exact matching function that compares the first two words of addresses for exact matches.
- **`get_dist()`**: Calculates Euclidean distance between coordinate pairs and converts to meters.
- **`normalize_distances()`**: Normalizes distance arrays to 0-1 scale for scoring purposes.

**Logic Flow:**
1. Extract address strings from Overture data structures
2. Create coordinate mappings for both places and addresses
3. Perform fuzzy string matching with scoring
4. Calculate physical distances between matched pairs
5. Generate confidence scores based on distance and name similarity

### `streamlit_generate_confidence.py` - Interactive Web Application
A Streamlit-based web interface that provides real-time location confidence analysis:

**Features:**
- **Interactive UI**: Sidebar controls for bounding box input and matching mode selection
- **Data Visualization**: PyDeck-powered maps showing places (red), addresses (blue), and connection lines
- **Real-time Processing**: Live data fetching from Overture Maps API within user-defined geographic bounds
- **Statistical Analysis**: Summary statistics including min/max/average distances and confidence scores
- **Export Functionality**: JSON download of results for further analysis

**Application Logic:**
1. Parse user-input bounding box coordinates
2. Fetch Overture Maps place and address data for the region
3. Convert geodata to processable dictionaries
4. Execute fuzzy matching algorithm
5. Generate interactive map visualization with matched pairs
6. Display statistical summaries and detailed results
7. Provide downloadable results in JSON format

**User Workflow:**
- Enter geographic bounding box (longitude/latitude bounds)
- Select matching algorithm (fuzzy recommended)
- Process data and view results on interactive map
- Analyze statistics and download results

Current Overture confidence metric only measures existential confidence. The addition of a locational confidence metric would allow Overture to further scale with certainty of their locational accuracy. Current plan is to utilize address coordinates and compare it to point-coordinates. Other data, such as land cover, may be utlitized for low-confidence Places. 

O1: Create Location Confidence metric for Place values. Ensure highly existence-confident places are also highly location-confident.

KR1: Generate 10-15k ground truth datapoints. Use address data to ensure places are within 2m of their address.

KR2: Create model to assign confidence values to places. Create a dataset of 30-50k Places points. Locational confidence relies on relation to address, land cover, and elevation.

KR3: Use (address & others) data to improve location of places on your accuracy metrics. Ensure >90% accuracy.

KR4: Scale dataset of Places with locational confidence metric up to 500k Places, across the globe.

Notes from POC:
Measure the calibration of that confidence value (logloss, ROC, calibration graph). Additionally could create an aggregated location accuracy metric (based on distance from you ground truth or similar)

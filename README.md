# Cyrus Correll | Project C: Developing Locational Confidence Metric for POI's

Current Overture confidence metric only measures existential confidence. The addition of a locational confidence metric would allow Overture to further scale with certainty of their locational accuracy. Current plan is to utilize address coordinates and compare it to point-coordinates. Other data, such as land cover, may be utlitized for low-confidence Places. 

O1: Create Location Confidence metric for Place values. Ensure highly existence-confident places are also highly location-confident.

KR1: Generate 10-15k ground truth datapoints. Use address data to ensure places are within 2m of their address.

KR2: Create model to assign confidence values to places. Create a dataset of 30-50k Places points. Locational confidence relies on relation to address, land cover, and elevation.

KR3: Use (address & others) data to improve location of places on your accuracy metrics. Ensure >90% accuracy.

KR4: Scale dataset of Places with locational confidence metric up to 500k Places, across the globe.

Notes from POC:
Measure the calibration of that confidence value (logloss, ROC, calibration graph). Additionally could create an aggregated location accuracy metric (based on distance from you ground truth or similar)

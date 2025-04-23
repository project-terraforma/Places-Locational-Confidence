# Cyrus Correll | Project C: Correcting High Confidence False Positive and Duplicate Places in Overture Maps

The purpose of this project is to develop a solution for detecting and correcting HCFP and Duplicate Places in Overture Maps. A high-confidence false-positive Place location is defined as a Place with over 0.75 confidence that is more than 10m from it's "correct" location. This is when the map is confidently wrong. 

Duplicate Place locations are defined as more than one Place locations meant for the same entity. Examples are prevalent in larger entities, such as airports. Many larger entities have multiple names, which leads to excess data and mistakes.

O1: Develop a reliable method of detecting high-confidence false-positive duplicate Place locations. 
KR1: Create an algorithm to detect false positive Place locations. Generate a dataset of 5-10k misplaced locations.

KR2: Create an algorithm to properly distinguish most significant place in the case of duplicates. Optimize algorithm to run efficiently. Utilize Graph Theory and KNN to determine most significant duplicate.

KR3: Create a benchmark to verify accuracy of aforementioned algorithm. Confirm that >95% of dataset is accurately false-positive Places.

O2: Develop a corrective solution to accurately re-assign location coordinates of high-confidence false-positive Place locations. 

KR1: Research potential approaches. Explore 3-5 different methods of correction, articulate pro's-con's of each.

KR2: Implement best corrective method found from KR1. Create a solution with scalability in mind. 

KR3: Run benchmark created in O1-KR3 on corrected data. Ensure that >80% of Places in original dataset are corrected.

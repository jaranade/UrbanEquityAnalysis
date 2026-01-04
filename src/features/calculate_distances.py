# src/features/calculate_distances.py

import geopandas as gpd
import pandas as pd
import osmnx as ox
import networkx as nx
from pathlib import Path
from tqdm import tqdm
import numpy as np

def load_street_network():
    """Load the street network for routing"""
    print("Loading street network...")
    
    # Try to load the connected network first
    network_path = Path("data/processed/la_street_network_connected.graphml")
    if network_path.exists():
        G = ox.load_graphml(network_path)
    else:
        # Fall back to original
        G = ox.load_graphml("data/raw/la_street_network.graphml")
    
    print(f"  Nodes: {len(G.nodes):,}")
    print(f"  Edges: {len(G.edges):,}")
    
    return G


def calculate_nearest_amenity_distances(max_tracts=None):
    """
    For each census tract, calculate distance to nearest amenity of each type
    Uses network distance (actual walking) not straight-line
    
    Parameters:
    -----------
    max_tracts: int, optional - limit to first N tracts for testing
    """
    
    print("Loading data...")
    tracts = gpd.read_file("data/processed/census_tracts_with_demographics.geojson")
    amenities = gpd.read_file("data/processed/amenities_cleaned.geojson")
    
    # Limit for testing if requested
    if max_tracts:
        print(f"⚠ Testing mode: Using only first {max_tracts} tracts")
        tracts = tracts.head(max_tracts)
    
    print(f"  Tracts: {len(tracts)}")
    print(f"  Amenities: {len(amenities)}")
    
    # Load street network
    G = load_street_network()
    
    # Convert to correct CRS for distance calculations
    if tracts.crs != "EPSG:4326":
        tracts_wgs84 = tracts.to_crs("EPSG:4326")
    else:
        tracts_wgs84 = tracts.copy()
    
    if amenities.crs != "EPSG:4326":
        amenities_wgs84 = amenities.to_crs("EPSG:4326")
    else:
        amenities_wgs84 = amenities.copy()
    
    # Get amenity types
    amenity_types = amenities['amenity_type'].unique()
    print(f"\nAmenity types: {amenity_types}")
    
    # Initialize results dictionary
    distance_data = []
    
    print("\nCalculating distances (this will take several minutes)...")
    
    # For each tract
    for idx, tract in tqdm(tracts_wgs84.iterrows(), total=len(tracts_wgs84), desc="Processing tracts"):
        
        tract_result = {
            'GEOID': tract['GEOID'],
            'centroid_x': tract['centroid_x'],
            'centroid_y': tract['centroid_y']
        }
        
        # Get tract centroid
        tract_centroid = tract.geometry.centroid
        tract_point = (tract_centroid.y, tract_centroid.x)  # lat, lon
        
        # Find nearest network node to tract centroid
        try:
            tract_node = ox.distance.nearest_nodes(G, tract_centroid.x, tract_centroid.y)
        except:
            # If network routing fails, use straight-line distances
            print(f"  Warning: Network routing failed for tract {tract['GEOID']}, using Euclidean distance")
            
            for amenity_type in amenity_types:
                type_amenities = amenities_wgs84[amenities_wgs84['amenity_type'] == amenity_type]
                
                if len(type_amenities) > 0:
                    # Calculate straight-line distances
                    distances = type_amenities.geometry.distance(tract.geometry.centroid)
                    min_dist_meters = distances.min() * 111000  # Rough conversion to meters
                    count_within_1km = (distances * 111000 <= 1000).sum()
                else:
                    min_dist_meters = np.nan
                    count_within_1km = 0
                
                tract_result[f'{amenity_type}_distance_m'] = min_dist_meters
                tract_result[f'{amenity_type}_count_1km'] = count_within_1km
            
            distance_data.append(tract_result)
            continue
        
        # For each amenity type, find nearest
        for amenity_type in amenity_types:
            type_amenities = amenities_wgs84[amenities_wgs84['amenity_type'] == amenity_type]
            
            if len(type_amenities) == 0:
                tract_result[f'{amenity_type}_distance_m'] = np.nan
                tract_result[f'{amenity_type}_count_1km'] = 0
                continue
            
            min_distance = np.inf
            count_within_1km = 0
            
            # Sample up to 10 nearest amenities (to keep it fast)
            # Calculate straight-line distance first to filter
            straight_distances = type_amenities.geometry.distance(tract.geometry.centroid)
            nearest_indices = straight_distances.nsmallest(min(10, len(type_amenities))).index
            
            for amenity_idx in nearest_indices:
                amenity = type_amenities.loc[amenity_idx]
                amenity_point = amenity.geometry
                
                try:
                    # Find nearest network node to amenity
                    amenity_node = ox.distance.nearest_nodes(G, amenity_point.x, amenity_point.y)
                    
                    # Calculate shortest path
                    path_length = nx.shortest_path_length(
                        G, tract_node, amenity_node, weight='length'
                    )
                    
                    if path_length < min_distance:
                        min_distance = path_length
                    
                    if path_length <= 1000:  # Within 1km
                        count_within_1km += 1
                        
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    # No path exists, use straight-line distance as fallback
                    straight_dist = straight_distances.loc[amenity_idx] * 111000
                    if straight_dist < min_distance:
                        min_distance = straight_dist
            
            tract_result[f'{amenity_type}_distance_m'] = min_distance if min_distance != np.inf else np.nan
            tract_result[f'{amenity_type}_count_1km'] = count_within_1km
        
        distance_data.append(tract_result)
    
    # Convert to DataFrame
    distance_df = pd.DataFrame(distance_data)
    
    # Merge back with original tract data
    tracts_with_distances = tracts.merge(distance_df, on='GEOID', how='left', suffixes=('', '_dist'))
    
    # Save
    output_path = Path("data/processed/tracts_with_distances.geojson")
    tracts_with_distances.to_file(output_path, driver='GeoJSON')
    
    print(f"\n✓ Saved to {output_path}")
    print(f"\nDistance features created:")
    distance_cols = [col for col in distance_df.columns if '_distance_m' in col or '_count_1km' in col]
    for col in distance_cols:
        print(f"  - {col}")
    
    return tracts_with_distances


if __name__ == "__main__":
    #Run distance calculations
    tracts = calculate_nearest_amenity_distances()
    
    # Show results
    print("\nSample results:")
    cols = ['GEOID', 'parks_distance_m', 'grocery_stores_distance_m', 'hospitals_distance_m']
    print(tracts[cols].head())
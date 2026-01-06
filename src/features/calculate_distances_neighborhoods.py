# src/features/calculate_distances_neighborhoods.py

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


def calculate_nearest_amenity_distances_neighborhoods(max_neighborhoods=None):
    """
    For each neighborhood, calculate distance to nearest amenity of each type
    Uses network distance (actual walking) not straight-line

    Parameters:
    -----------
    max_neighborhoods: int, optional - limit to first N neighborhoods for testing
    """

    print("Loading data...")
    neighborhoods = gpd.read_file("data/processed/neighborhoods_with_demographics.geojson")
    amenities = gpd.read_file("data/processed/amenities_cleaned.geojson")

    # Limit for testing if requested
    if max_neighborhoods:
        print(f"[!] Testing mode: Using only first {max_neighborhoods} neighborhoods")
        neighborhoods = neighborhoods.head(max_neighborhoods)

    print(f"  Neighborhoods: {len(neighborhoods)}")
    print(f"  Amenities: {len(amenities)}")

    # Load street network
    G = load_street_network()

    # Convert to correct CRS for distance calculations
    if neighborhoods.crs != "EPSG:4326":
        neighborhoods_wgs84 = neighborhoods.to_crs("EPSG:4326")
    else:
        neighborhoods_wgs84 = neighborhoods.copy()

    if amenities.crs != "EPSG:4326":
        amenities_wgs84 = amenities.to_crs("EPSG:4326")
    else:
        amenities_wgs84 = amenities.copy()

    # Get amenity types
    amenity_types = amenities['amenity_type'].unique()
    print(f"\nAmenity types: {amenity_types}")

    # Initialize results dictionary
    distance_data = []

    print("\nCalculating distances from neighborhood centroids...")

    # For each neighborhood
    for idx, neighborhood in tqdm(neighborhoods_wgs84.iterrows(), total=len(neighborhoods_wgs84), desc="Processing neighborhoods"):

        neighborhood_result = {
            'neighborhood_id': neighborhood['neighborhood_id'],
            'neighborhood_name': neighborhood['neighborhood_name'],
            'centroid_x': neighborhood['centroid_x'],
            'centroid_y': neighborhood['centroid_y']
        }

        # Get neighborhood centroid
        neighborhood_centroid = neighborhood.geometry.centroid
        neighborhood_point = (neighborhood_centroid.y, neighborhood_centroid.x)  # lat, lon

        # Find nearest network node to neighborhood centroid
        try:
            neighborhood_node = ox.distance.nearest_nodes(G, neighborhood_centroid.x, neighborhood_centroid.y)
        except:
            # If network routing fails, use straight-line distances
            print(f"  Warning: Network routing failed for {neighborhood['neighborhood_name']}, using Euclidean distance")

            for amenity_type in amenity_types:
                type_amenities = amenities_wgs84[amenities_wgs84['amenity_type'] == amenity_type]

                if len(type_amenities) > 0:
                    # Calculate straight-line distances
                    distances = type_amenities.geometry.distance(neighborhood.geometry.centroid)
                    min_dist_meters = distances.min() * 111000  # Rough conversion to meters
                    count_within_1km = (distances * 111000 <= 1000).sum()
                else:
                    min_dist_meters = np.nan
                    count_within_1km = 0

                neighborhood_result[f'{amenity_type}_distance_m'] = min_dist_meters
                neighborhood_result[f'{amenity_type}_count_1km'] = count_within_1km

            distance_data.append(neighborhood_result)
            continue

        # For each amenity type, find nearest
        for amenity_type in amenity_types:
            type_amenities = amenities_wgs84[amenities_wgs84['amenity_type'] == amenity_type]

            if len(type_amenities) == 0:
                neighborhood_result[f'{amenity_type}_distance_m'] = np.nan
                neighborhood_result[f'{amenity_type}_count_1km'] = 0
                continue

            min_distance = np.inf
            count_within_1km = 0

            # Sample up to 10 nearest amenities (to keep it fast)
            # Calculate straight-line distance first to filter
            straight_distances = type_amenities.geometry.distance(neighborhood.geometry.centroid)
            nearest_indices = straight_distances.nsmallest(min(10, len(type_amenities))).index

            for amenity_idx in nearest_indices:
                amenity = type_amenities.loc[amenity_idx]
                amenity_point = amenity.geometry

                try:
                    # Find nearest network node to amenity
                    amenity_node = ox.distance.nearest_nodes(G, amenity_point.x, amenity_point.y)

                    # Calculate shortest path
                    path_length = nx.shortest_path_length(
                        G, neighborhood_node, amenity_node, weight='length'
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

            neighborhood_result[f'{amenity_type}_distance_m'] = min_distance if min_distance != np.inf else np.nan
            neighborhood_result[f'{amenity_type}_count_1km'] = count_within_1km

        distance_data.append(neighborhood_result)

    # Convert to DataFrame
    distance_df = pd.DataFrame(distance_data)

    # Merge back with original neighborhood data
    neighborhoods_with_distances = neighborhoods.merge(
        distance_df,
        on='neighborhood_id',
        how='left',
        suffixes=('', '_dist')
    )

    # Save
    output_path = Path("data/processed/neighborhoods_with_distances.geojson")
    neighborhoods_with_distances.to_file(output_path, driver='GeoJSON')

    print(f"\n[OK] Saved to {output_path}")
    print(f"\nDistance features created:")
    distance_cols = [col for col in distance_df.columns if '_distance_m' in col or '_count_1km' in col]
    for col in distance_cols:
        print(f"  - {col}")

    return neighborhoods_with_distances


if __name__ == "__main__":
    # Run distance calculations
    neighborhoods = calculate_nearest_amenity_distances_neighborhoods()

    # Show results
    print("\nSample results:")
    cols = ['neighborhood_name', 'parks_distance_m', 'grocery_stores_distance_m', 'hospitals_distance_m']
    available_cols = [col for col in cols if col in neighborhoods.columns]
    print(neighborhoods[available_cols].head())

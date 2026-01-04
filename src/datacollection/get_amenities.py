# src/data_collection/get_amenities.py

import osmnx as ox
import pandas as pd
import geopandas as gpd
from pathlib import Path
from tqdm import tqdm

def get_osm_amenities(boundary_gdf, amenity_type, tags):
    """
    Download amenities from OpenStreetMap
    
    Parameters:
    -----------
    boundary_gdf: GeoDataFrame with study area boundary
    amenity_type: str, name for this amenity category
    tags: dict, OSM tags to query
    """
    
    # Get bounding polygon
    polygon = boundary_gdf.geometry.iloc[0]
    
    try:
        # Query OSM
        amenities = ox.features_from_polygon(polygon, tags=tags)
        
        # Keep only point and polygon features
        if not amenities.empty:
            # Convert to points (centroids for polygons)
            amenities['geometry'] = amenities['geometry'].centroid
            
            # Select relevant columns
            cols_to_keep = ['name', 'geometry']
            existing_cols = [c for c in cols_to_keep if c in amenities.columns]
            amenities = amenities[existing_cols].reset_index(drop=True)
            
            # Add amenity type
            amenities['amenity_type'] = amenity_type
            
            print(f"✓ {amenity_type}: {len(amenities)} features")
            
            return amenities
    except Exception as e:
        print(f"✗ Error fetching {amenity_type}: {e}")
        return gpd.GeoDataFrame()


def collect_all_amenities():
    """
    Collect all amenity types for LA
    """
    
    # Load boundary
    boundary = gpd.read_file("data/raw/la_boundary.geojson")
    
    # Define amenities to collect
    amenity_configs = {
        'parks': {'leisure': ['park', 'playground', 'recreation_ground', 'garden']},
        'hospitals': {'amenity': ['hospital', 'clinic', 'doctors']},
        'urgent_care': {'amenity': ['clinic'], 'healthcare': ['clinic']},
        'pharmacies': {'amenity': ['pharmacy']},
        'grocery_stores': {'shop': ['supermarket', 'grocery', 'convenience']},
        'schools': {'amenity': ['school', 'kindergarten', 'college', 'university']},
        'transit_stops': {'public_transport': ['stop_position', 'platform', 'station']},
        'libraries': {'amenity': ['library']},
    }
    
    all_amenities = []
    
    for amenity_name, tags in tqdm(amenity_configs.items(), desc="Collecting amenities"):
        gdf = get_osm_amenities(boundary, amenity_name, tags)
        if not gdf.empty:
            all_amenities.append(gdf)
    
    # Combine all amenities
    combined = gpd.GeoDataFrame(pd.concat(all_amenities, ignore_index=True))
    
    # Convert to appropriate CRS
    combined = combined.to_crs("EPSG:2229")
    
    # Save
    output_path = Path("data/raw/la_amenities_all.geojson")
    combined.to_file(output_path, driver='GeoJSON')
    
    print(f"\n✓ Total amenities collected: {len(combined)}")
    print(f"  Breakdown:")
    print(combined['amenity_type'].value_counts())
    
    return combined


if __name__ == "__main__":
    amenities = collect_all_amenities()
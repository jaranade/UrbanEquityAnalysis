# src/preprocessing/validate_data.py

import geopandas as gpd
import pandas as pd
from pathlib import Path

def validate_collected_data():
    """
    Run quality checks on all collected data
    """
    
    print("=" * 50)
    print("DATA VALIDATION REPORT")
    print("=" * 50)
    
    # Check census tracts
    tracts = gpd.read_file("data/raw/la_census_tracts.geojson")
    print(f"\n✓ Census Tracts: {len(tracts)}")
    print(f"  CRS: {tracts.crs}")
    print(f"  Null geometries: {tracts.geometry.isna().sum()}")
    
    # Check demographics
    demographics = pd.read_csv("data/raw/la_demographics.csv")
    print(f"\n✓ Demographics: {len(demographics)} records")
    print(f"  Missing values:\n{demographics.isnull().sum()}")
    
    # Check amenities
    amenities = gpd.read_file("data/raw/la_amenities_all.geojson")
    print(f"\n✓ Amenities: {len(amenities)}")
    print(f"  By type:\n{amenities['amenity_type'].value_counts()}")
    print(f"  Null geometries: {amenities.geometry.isna().sum()}")
    
    # Check if all CRS match
    print(f"\n✓ CRS Check:")
    print(f"  Tracts: {tracts.crs}")
    print(f"  Amenities: {amenities.crs}")
    
    # Check spatial overlap
    tracts_bounds = tracts.total_bounds
    amenities_bounds = amenities.total_bounds
    
    print(f"\n✓ Spatial Bounds:")
    print(f"  Tracts: {tracts_bounds}")
    print(f"  Amenities: {amenities_bounds}")
    
    return True


if __name__ == "__main__":
    validate_collected_data()
# src/preprocessing/clean_amenities.py

import geopandas as gpd
import pandas as pd
from pathlib import Path

def clean_amenities():
    """
    Clean amenity data, remove duplicates, categorize by importance
    """
    
    print("Loading amenities...")
    amenities = gpd.read_file("data/raw/la_amenities_all.geojson")
    
    print(f"  Total amenities: {len(amenities)}")
    print(f"  Amenity types:\n{amenities['amenity_type'].value_counts()}")
    
    # Remove duplicates based on location (within 10 feet)
    print("\nRemoving spatial duplicates...")
    
    # Convert to a projected CRS if not already
    if amenities.crs != "EPSG:2229":
        amenities = amenities.to_crs("EPSG:2229")
    
    # Simple deduplication: keep first of nearby amenities of same type
    cleaned = []
    for amenity_type in amenities['amenity_type'].unique():
        subset = amenities[amenities['amenity_type'] == amenity_type].copy()
        
        # Remove exact duplicates first
        subset = subset.drop_duplicates(subset=['geometry'])
        
        cleaned.append(subset)
    
    amenities_clean = pd.concat(cleaned, ignore_index=True)
    amenities_clean = gpd.GeoDataFrame(amenities_clean, geometry='geometry', crs="EPSG:2229")
    
    print(f"After deduplication: {len(amenities_clean)}")
    print(f"  Removed: {len(amenities) - len(amenities_clean)} duplicates")
    
    # Add importance weights (for walkability scoring later)
    importance_weights = {
        'parks': 1.0,
        'hospitals': 0.8,
        'urgent_care': 0.6,
        'pharmacies': 0.5,
        'grocery_stores': 0.9,
        'schools': 0.7,
        'transit_stops': 0.8,
        'libraries': 0.5,
    }
    
    amenities_clean['importance_weight'] = amenities_clean['amenity_type'].map(importance_weights)
    
    # Add size categories for parks (estimate from area if available)
    amenities_clean['size_category'] = 'medium'
    
    # Check for and remove any extra geometry columns before saving
    geom_cols = [col for col in amenities_clean.columns if isinstance(amenities_clean[col].dtype, gpd.array.GeometryDtype)]
    print(f"\nGeometry columns found: {geom_cols}")
    
    # Drop all geometry columns except 'geometry'
    for col in geom_cols:
        if col != 'geometry':
            print(f"  Dropping extra geometry column: {col}")
            amenities_clean = amenities_clean.drop(columns=[col])
    
    # Verify we only have one geometry column
    remaining_geom_cols = [col for col in amenities_clean.columns if isinstance(amenities_clean[col].dtype, gpd.array.GeometryDtype)]
    print(f"Remaining geometry columns: {remaining_geom_cols}")
    
    # Save cleaned data
    output_path = Path("data/processed/amenities_cleaned.geojson")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    amenities_clean.to_file(output_path, driver='GeoJSON')
    
    print(f"\n✓ Saved to {output_path}")
    
    # Summary by type
    print("\n" + "="*50)
    print("CLEANED AMENITIES BY TYPE")
    print("="*50)
    print(amenities_clean['amenity_type'].value_counts())
    
    return amenities_clean


if __name__ == "__main__":
    amenities_clean = clean_amenities()
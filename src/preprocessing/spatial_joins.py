# src/preprocessing/spatial_joins.py

import geopandas as gpd
import pandas as pd
from pathlib import Path

def assign_amenities_to_tracts():
    """
    Perform spatial join to count amenities per census tract
    """
    
    print("Loading data...")
    tracts = gpd.read_file("data/processed/census_tracts_with_demographics.geojson")
    amenities = gpd.read_file("data/processed/amenities_cleaned.geojson")
    
    # Ensure same CRS
    if tracts.crs != amenities.crs:
        amenities = amenities.to_crs(tracts.crs)
    
    print(f"  Tracts: {len(tracts)}")
    print(f"  Amenities: {len(amenities)}")
    
    # Spatial join: which amenities are in which tracts
    print("\nPerforming spatial join...")
    joined = gpd.sjoin(amenities, tracts[['GEOID', 'geometry']], how='left', predicate='within')
    
    # Count amenities per tract by type
    amenity_counts = joined.groupby(['GEOID', 'amenity_type']).size().unstack(fill_value=0)
    amenity_counts.columns = [f'{col}_count' for col in amenity_counts.columns]
    
    # Merge back to tracts
    tracts_with_counts = tracts.merge(amenity_counts, on='GEOID', how='left')
    
    # Fill NaN with 0 for tracts with no amenities
    amenity_cols = [col for col in tracts_with_counts.columns if col.endswith('_count')]
    tracts_with_counts[amenity_cols] = tracts_with_counts[amenity_cols].fillna(0)
    
    # Calculate total amenities per tract
    tracts_with_counts['total_amenities'] = tracts_with_counts[amenity_cols].sum(axis=1)
    
    # Calculate amenities per capita
    tracts_with_counts['amenities_per_1000'] = (
        tracts_with_counts['total_amenities'] / tracts_with_counts['total_population'] * 1000
    )
    
    # Save
    output_path = Path("data/processed/tracts_with_amenity_counts.geojson")
    tracts_with_counts.to_file(output_path, driver='GeoJSON')
    
    print(f"\n✓ Saved to {output_path}")
    
    # Summary
    print("\n" + "="*50)
    print("AMENITY COUNTS SUMMARY")
    print("="*50)
    print(f"\nTracts with 0 amenities: {(tracts_with_counts['total_amenities'] == 0).sum()}")
    print(f"Average amenities per tract: {tracts_with_counts['total_amenities'].mean():.2f}")
    print(f"Max amenities in a tract: {tracts_with_counts['total_amenities'].max():.0f}")
    
    print("\nTop 5 tracts by amenity count:")
    top_tracts = tracts_with_counts.nlargest(5, 'total_amenities')[
        ['GEOID', 'total_amenities', 'total_population', 'amenities_per_1000']
    ]
    print(top_tracts.to_string(index=False))
    
    return tracts_with_counts


if __name__ == "__main__":
    tracts_enriched = assign_amenities_to_tracts()
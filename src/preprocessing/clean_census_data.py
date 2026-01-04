# src/preprocessing/clean_census_data.py

import geopandas as gpd
import pandas as pd
from pathlib import Path

def clean_and_merge_census():
    """
    Merge census tract geometries with demographic data
    Clean and handle missing values
    """
    
    print("Loading census data...")
    
    # Load census tracts (geometries)
    tracts = gpd.read_file("data/raw/la_census_tracts.geojson")
    
    # Load demographics
    demographics = pd.read_csv("data/raw/la_demographics.csv")
    
    print(f"  Tracts: {len(tracts)}")
    print(f"  Demographics: {len(demographics)}")
    
    # DEBUG: Check what columns exist
    print(f"\nTract columns: {tracts.columns.tolist()[:10]}")
    print(f"Demographics columns: {demographics.columns.tolist()}")
    
    # Ensure GEOID is string type in both datasets
    tracts['GEOID'] = tracts['GEOID'].astype(str)
    demographics['GEOID'] = demographics['GEOID'].astype(str)
    
    print(f"\nData types:")
    print(f"  Tracts GEOID: {tracts['GEOID'].dtype}")
    print(f"  Demographics GEOID: {demographics['GEOID'].dtype}")
    
    # DEBUG: Check if total_population exists and has data
    print(f"\nDemographics total_population check:")
    print(f"  Column exists: {'total_population' in demographics.columns}")
    if 'total_population' in demographics.columns:
        print(f"  Data type: {demographics['total_population'].dtype}")
        print(f"  Sample values: {demographics['total_population'].head().tolist()}")
        print(f"  Sum: {demographics['total_population'].sum():,.0f}")
    
    # Merge on GEOID
    merged = tracts.merge(demographics, on='GEOID', how='left')
    
    print(f"\nMerged data: {len(merged)} tracts")
    
    # DEBUG: Check merge results
    print(f"Merged columns: {merged.columns.tolist()}")
    print(f"\nSample merged data:")
    print(merged[['GEOID', 'total_population']].head())
    
    # Check for population data AFTER merge
    print(f"\nPopulation after merge:")
    print(f"  Data type: {merged['total_population'].dtype}")
    print(f"  Total population sum: {merged['total_population'].sum():,.0f}")
    print(f"  Tracts with population > 0: {(merged['total_population'] > 0).sum()}")
    print(f"  Tracts with NaN population: {merged['total_population'].isna().sum()}")
    
    # Calculate derived metrics (handle division by zero)
    merged['area_acres'] = merged.geometry.area / 43560
    merged['population_density'] = merged['total_population'] / merged['area_acres'].replace(0, 1)
    
    # Calculate diversity percentages (avoid division by zero)
    total_pop = merged['total_population'].replace(0, pd.NA)
    merged['pct_white'] = (merged['white_alone'] / total_pop * 100).fillna(0)
    merged['pct_black'] = (merged['black_alone'] / total_pop * 100).fillna(0)
    merged['pct_asian'] = (merged['asian_alone'] / total_pop * 100).fillna(0)
    merged['pct_hispanic'] = (merged['hispanic_latino'] / total_pop * 100).fillna(0)
    
    # Handle missing income data
    print(f"\nMissing median income: {merged['median_household_income'].isna().sum()} tracts")
    
    # FIXED: Don't filter out tracts - the data is good!
    # Only remove if population is actually 0 or NaN
    print(f"\nBefore filtering: {len(merged)} tracts")
    
    # More lenient filtering - only remove truly empty tracts
    merged_filtered = merged[
        (merged['total_population'].notna()) & 
        (merged['total_population'] > 0)
    ].copy()
    
    print(f"After filtering: {len(merged_filtered)} tracts")
    
    # If we lost everything, don't filter at all
    if len(merged_filtered) == 0:
        print("⚠ WARNING: Filtering removed all tracts! Keeping all data.")
        merged_filtered = merged.copy()
    
    # Store centroid coordinates as regular columns (not geometry)
    merged_filtered['centroid_x'] = merged_filtered.geometry.centroid.x
    merged_filtered['centroid_y'] = merged_filtered.geometry.centroid.y
    
    # Check for and remove any extra geometry columns
    geom_cols = [col for col in merged_filtered.columns if isinstance(merged_filtered[col].dtype, gpd.array.GeometryDtype)]
    print(f"\nGeometry columns found: {geom_cols}")
    
    # Drop all geometry columns except 'geometry'
    for col in geom_cols:
        if col != 'geometry':
            print(f"  Dropping extra geometry column: {col}")
            merged_filtered = merged_filtered.drop(columns=[col])
    
    # Verify we only have one geometry column
    remaining_geom_cols = [col for col in merged_filtered.columns if isinstance(merged_filtered[col].dtype, gpd.array.GeometryDtype)]
    print(f"Remaining geometry columns: {remaining_geom_cols}")
    
    # Save processed data
    output_path = Path("data/processed/census_tracts_with_demographics.geojson")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\nSaving to {output_path}...")
    merged_filtered.to_file(output_path, driver='GeoJSON')
    
    print(f"✓ Saved to {output_path}")
    
    # Summary statistics
    print("\n" + "="*50)
    print("SUMMARY STATISTICS")
    print("="*50)
    print(f"\nTotal tracts: {len(merged_filtered)}")
    print(f"Total Population: {merged_filtered['total_population'].sum():,.0f}")
    
    # Check if we have valid income data
    valid_income = merged_filtered['median_household_income'].notna()
    if valid_income.any():
        print(f"Median Income Range: ${merged_filtered.loc[valid_income, 'median_household_income'].min():,.0f} - ${merged_filtered.loc[valid_income, 'median_household_income'].max():,.0f}")
        print(f"Tracts with income data: {valid_income.sum()}")
    else:
        print("⚠ No valid median income data")
    
    print(f"Average Population Density: {merged_filtered['population_density'].mean():.2f} per acre")
    
    return merged_filtered


if __name__ == "__main__":
    census_clean = clean_and_merge_census()
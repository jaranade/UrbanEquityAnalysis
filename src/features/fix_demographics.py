# fix_demographics_v2.py

import geopandas as gpd
import pandas as pd

print("Loading walkability data...")
walkability = gpd.read_file("data/processed/tracts_with_walkability.geojson")

print("Loading raw demographics...")
demographics = pd.read_csv("data/raw/la_demographics.csv")

print(f"\nWalkability tracts: {len(walkability)}")
print(f"Demographics records: {len(demographics)}")

# Fix GEOID formats to match
print("\nFixing GEOID formats...")
print(f"Walkability GEOID sample: {walkability['GEOID'].iloc[0]} (type: {type(walkability['GEOID'].iloc[0])})")
print(f"Demographics GEOID sample: {demographics['GEOID'].iloc[0]} (type: {type(demographics['GEOID'].iloc[0])})")

# Convert both to string with leading zeros
walkability['GEOID'] = walkability['GEOID'].astype(str).str.zfill(11)
demographics['GEOID'] = demographics['GEOID'].astype(str).str.zfill(11)

print(f"\nAfter conversion:")
print(f"Walkability GEOID sample: {walkability['GEOID'].iloc[0]}")
print(f"Demographics GEOID sample: {demographics['GEOID'].iloc[0]}")

# Drop old demographic columns from walkability
walkability = walkability.drop(columns=['total_population', 'median_household_income'], errors='ignore')

# Merge
print("\nMerging...")
merged = walkability.merge(
    demographics[['GEOID', 'total_population', 'median_household_income', 'median_age']], 
    on='GEOID', 
    how='left'
)

print(f"Merged: {len(merged)} tracts")
print(f"\nSample merged data:")
print(merged[['GEOID', 'total_population', 'median_household_income', 'walkability_index']].head(10))

# Check how many have valid demographics
valid_count = merged['total_population'].notna().sum()
print(f"\nTracts with valid demographics: {valid_count} / {len(merged)}")

# Calculate correlations
print("\n" + "="*60)
print("CORRELATION WITH DEMOGRAPHICS")
print("="*60)

valid_data = merged[merged['median_household_income'].notna() & merged['total_population'].notna()]

if len(valid_data) > 0:
    income_corr = valid_data[['walkability_index', 'median_household_income']].corr().iloc[0, 1]
    print(f"Walkability vs. Income: {income_corr:.3f}")
    
    if 'population_density' in merged.columns:
        density_corr = valid_data[['walkability_index', 'population_density']].corr().iloc[0, 1]
        print(f"Walkability vs. Population Density: {density_corr:.3f}")

# Show top/bottom by demographics
print("\n" + "="*60)
print("TOP 5 MOST WALKABLE (WITH DEMOGRAPHICS)")
print("="*60)
top = merged.nlargest(5, 'walkability_index')[
    ['GEOID', 'walkability_index', 'total_population', 'median_household_income']
]
print(top.to_string(index=False))

print("\n" + "="*60)
print("TOP 5 LEAST WALKABLE (WITH DEMOGRAPHICS)")
print("="*60)
bottom = merged[merged['walkability_index'] > 0].nsmallest(5, 'walkability_index')[
    ['GEOID', 'walkability_index', 'total_population', 'median_household_income']
]
print(bottom.to_string(index=False))

# Save
merged.to_file("data/processed/tracts_with_walkability.geojson", driver='GeoJSON')
print("\n✓ Saved fixed data with demographics")
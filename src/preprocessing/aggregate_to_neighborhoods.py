# src/preprocessing/aggregate_to_neighborhoods.py

import geopandas as gpd
import pandas as pd
from pathlib import Path

def aggregate_demographics_to_neighborhoods():
    """
    Aggregate census tract demographics to neighborhood level
    using spatial overlay and weighted averages
    """

    print("Loading data...")

    # Load neighborhoods
    neighborhoods = gpd.read_file("data/raw/la_neighborhoods.geojson")
    print(f"  Neighborhoods: {len(neighborhoods)}")

    # Load census tracts with demographics
    tracts = gpd.read_file("data/processed/census_tracts_with_demographics.geojson")
    print(f"  Census tracts: {len(tracts)}")

    # Ensure both use the same CRS
    if neighborhoods.crs != tracts.crs:
        print(f"  Converting neighborhoods from {neighborhoods.crs} to {tracts.crs}")
        neighborhoods = neighborhoods.to_crs(tracts.crs)

    print("\nPerforming spatial overlay to find tract-neighborhood intersections...")

    # Calculate tract areas for weighting
    tracts['tract_area'] = tracts.geometry.area

    # Perform overlay to find intersections
    overlay = gpd.overlay(tracts, neighborhoods, how='intersection')

    # Calculate intersection area
    overlay['intersection_area'] = overlay.geometry.area

    # Calculate weight (proportion of tract in each neighborhood)
    overlay['weight'] = overlay['intersection_area'] / overlay['tract_area']

    print(f"  Found {len(overlay)} tract-neighborhood intersections")

    # Aggregate demographics to neighborhoods
    print("\nAggregating demographics to neighborhoods...")

    # Numeric columns to aggregate
    numeric_cols = [
        'total_population',
        'white_alone',
        'black_alone',
        'asian_alone',
        'hispanic_latino',
        'median_household_income',
        'median_age'
    ]

    # Weighted sum for population counts
    population_cols = [
        'total_population',
        'white_alone',
        'black_alone',
        'asian_alone',
        'hispanic_latino'
    ]

    # Convert to numeric first
    for col in population_cols:
        overlay[col] = pd.to_numeric(overlay[col], errors='coerce').fillna(0)

    # Create weighted values for population
    for col in population_cols:
        overlay[f'{col}_weighted'] = overlay[col] * overlay['weight']

    # Group by neighborhood and sum
    agg_dict = {f'{col}_weighted': 'sum' for col in population_cols}

    neighborhood_stats = overlay.groupby('neighborhood_id').agg(agg_dict).reset_index()

    # Rename back to original column names and ensure numeric type
    for col in population_cols:
        neighborhood_stats[col] = pd.to_numeric(neighborhood_stats[f'{col}_weighted'], errors='coerce').fillna(0)
        neighborhood_stats = neighborhood_stats.drop(columns=[f'{col}_weighted'])

    # For income and age, calculate weighted average
    # Convert to numeric first
    overlay['median_household_income'] = pd.to_numeric(overlay['median_household_income'], errors='coerce').fillna(0)
    overlay['median_age'] = pd.to_numeric(overlay['median_age'], errors='coerce').fillna(0)

    overlay['income_weighted'] = overlay['median_household_income'] * overlay['total_population'] * overlay['weight']
    overlay['age_weighted'] = overlay['median_age'] * overlay['total_population'] * overlay['weight']
    overlay['pop_weighted'] = overlay['total_population'] * overlay['weight']

    income_age_agg = overlay.groupby('neighborhood_id').agg({
        'income_weighted': 'sum',
        'age_weighted': 'sum',
        'pop_weighted': 'sum'
    }).reset_index()

    # Avoid division by zero
    income_age_agg['median_household_income'] = income_age_agg['income_weighted'] / income_age_agg['pop_weighted'].replace(0, pd.NA)
    income_age_agg['median_age'] = income_age_agg['age_weighted'] / income_age_agg['pop_weighted'].replace(0, pd.NA)

    # Merge back with neighborhood stats
    neighborhood_stats = neighborhood_stats.merge(
        income_age_agg[['neighborhood_id', 'median_household_income', 'median_age']],
        on='neighborhood_id'
    )

    # Merge with neighborhood geometries and names
    neighborhoods_with_demographics = neighborhoods.merge(
        neighborhood_stats,
        on='neighborhood_id',
        how='left'
    )

    # Calculate derived metrics
    neighborhoods_with_demographics['area_acres'] = neighborhoods_with_demographics.geometry.area / 43560
    neighborhoods_with_demographics['population_density'] = (
        neighborhoods_with_demographics['total_population'] /
        neighborhoods_with_demographics['area_acres'].replace(0, 1)
    )

    # Calculate diversity percentages
    total_pop = neighborhoods_with_demographics['total_population'].replace(0, pd.NA)
    neighborhoods_with_demographics['pct_white'] = (neighborhoods_with_demographics['white_alone'] / total_pop * 100).fillna(0)
    neighborhoods_with_demographics['pct_black'] = (neighborhoods_with_demographics['black_alone'] / total_pop * 100).fillna(0)
    neighborhoods_with_demographics['pct_asian'] = (neighborhoods_with_demographics['asian_alone'] / total_pop * 100).fillna(0)
    neighborhoods_with_demographics['pct_hispanic'] = (neighborhoods_with_demographics['hispanic_latino'] / total_pop * 100).fillna(0)

    # Store centroid coordinates
    neighborhoods_with_demographics['centroid_x'] = neighborhoods_with_demographics.geometry.centroid.x
    neighborhoods_with_demographics['centroid_y'] = neighborhoods_with_demographics.geometry.centroid.y

    # Save to file
    output_path = Path("data/processed/neighborhoods_with_demographics.geojson")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving to {output_path}...")
    neighborhoods_with_demographics.to_file(output_path, driver='GeoJSON')

    print(f"[OK] Saved to {output_path}")

    # Summary statistics
    print("\n" + "="*50)
    print("NEIGHBORHOOD DEMOGRAPHICS SUMMARY")
    print("="*50)
    print(f"\nTotal neighborhoods: {len(neighborhoods_with_demographics)}")
    print(f"Total Population: {neighborhoods_with_demographics['total_population'].sum():,.0f}")

    valid_income = neighborhoods_with_demographics['median_household_income'].notna()
    if valid_income.any():
        print(f"Median Income Range: ${neighborhoods_with_demographics.loc[valid_income, 'median_household_income'].min():,.0f} - ${neighborhoods_with_demographics.loc[valid_income, 'median_household_income'].max():,.0f}")

    print(f"Average Population Density: {neighborhoods_with_demographics['population_density'].mean():.2f} per acre")

    # Convert total_population to numeric for sorting
    neighborhoods_with_demographics['total_population'] = pd.to_numeric(
        neighborhoods_with_demographics['total_population'],
        errors='coerce'
    ).fillna(0)

    print("\nTop 5 neighborhoods by population:")
    if neighborhoods_with_demographics['total_population'].sum() > 0:
        top_neighborhoods = neighborhoods_with_demographics.nlargest(5, 'total_population')[
            ['neighborhood_name', 'total_population', 'median_household_income']
        ]
        for idx, row in top_neighborhoods.iterrows():
            income = row['median_household_income']
            if pd.notna(income):
                print(f"  {row['neighborhood_name']}: {row['total_population']:,.0f} people, ${income:,.0f} median income")
            else:
                print(f"  {row['neighborhood_name']}: {row['total_population']:,.0f} people")
    else:
        print("  No population data available")

    return neighborhoods_with_demographics


if __name__ == "__main__":
    neighborhoods = aggregate_demographics_to_neighborhoods()

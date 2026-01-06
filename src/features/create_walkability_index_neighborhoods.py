# src/features/create_walkability_index_neighborhoods.py

import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path

def distance_to_score(distance, ideal=400, acceptable=1000, poor=2000):
    """
    Convert distance (meters) to a score (0-100)

    Parameters:
    -----------
    distance: float, distance in meters
    ideal: float, ideal walking distance (gets 100 points)
    acceptable: float, acceptable distance (gets 70 points)
    poor: float, poor distance (gets 30 points)

    Returns:
    --------
    score: float, 0-100
    """
    if pd.isna(distance):
        return 0

    if distance <= ideal:
        return 100
    elif distance <= acceptable:
        # Linear interpolation between ideal and acceptable
        return 100 - (30 * (distance - ideal) / (acceptable - ideal))
    elif distance <= poor:
        # Linear interpolation between acceptable and poor
        return 70 - (40 * (distance - acceptable) / (poor - acceptable))
    else:
        # Beyond poor distance, score decreases slowly
        return max(0, 30 - (distance - poor) / 100)


def create_walkability_index_neighborhoods():
    """
    Create composite walkability index from distance features for neighborhoods
    """

    print("Loading neighborhood data with distance features...")
    neighborhoods = gpd.read_file("data/processed/neighborhoods_with_distances.geojson")

    print(f"  Loaded {len(neighborhoods)} neighborhoods")

    # Define weights for each amenity type (importance to walkability)
    weights = {
        'parks': 0.20,           # Parks are important for quality of life
        'grocery_stores': 0.25,  # Daily necessity - highest weight
        'transit_stops': 0.15,   # Important for mobility
        'schools': 0.10,         # Important for families
        'hospitals': 0.10,       # Critical but less frequent
        'pharmacies': 0.10,      # Healthcare access
        'libraries': 0.05,       # Nice to have
        'urgent_care': 0.05,     # Emergency access
    }

    print("\nCalculating individual amenity scores...")

    # Calculate score for each amenity type
    for amenity_type in weights.keys():
        distance_col = f'{amenity_type}_distance_m'
        score_col = f'{amenity_type}_score'

        if distance_col in neighborhoods.columns:
            # Different thresholds for different amenities
            if amenity_type in ['parks', 'grocery_stores', 'transit_stops']:
                # Daily use - stricter thresholds
                neighborhoods[score_col] = neighborhoods[distance_col].apply(
                    lambda d: distance_to_score(d, ideal=400, acceptable=800, poor=1500)
                )
            elif amenity_type in ['schools', 'libraries']:
                # Regular use - moderate thresholds
                neighborhoods[score_col] = neighborhoods[distance_col].apply(
                    lambda d: distance_to_score(d, ideal=600, acceptable=1200, poor=2000)
                )
            else:
                # Occasional use - lenient thresholds
                neighborhoods[score_col] = neighborhoods[distance_col].apply(
                    lambda d: distance_to_score(d, ideal=800, acceptable=1500, poor=3000)
                )

            print(f"  {amenity_type}: avg score = {neighborhoods[score_col].mean():.1f}")
        else:
            print(f"  Warning: {distance_col} not found, setting score to 0")
            neighborhoods[score_col] = 0

    # Calculate weighted walkability index
    print("\nCalculating composite walkability index...")

    neighborhoods['walkability_index'] = 0
    for amenity_type, weight in weights.items():
        score_col = f'{amenity_type}_score'
        if score_col in neighborhoods.columns:
            neighborhoods['walkability_index'] += neighborhoods[score_col] * weight

    # Round to 1 decimal place
    neighborhoods['walkability_index'] = neighborhoods['walkability_index'].round(1)

    # Create categorical classification
    def classify_walkability(score):
        if score >= 80:
            return 'Excellent'
        elif score >= 65:
            return 'Good'
        elif score >= 50:
            return 'Moderate'
        elif score >= 35:
            return 'Poor'
        else:
            return 'Very Poor'

    neighborhoods['walkability_category'] = neighborhoods['walkability_index'].apply(classify_walkability)

    # Summary statistics
    print("\n" + "="*60)
    print("NEIGHBORHOOD WALKABILITY INDEX SUMMARY")
    print("="*60)
    print(f"\nTotal neighborhoods: {len(neighborhoods)}")
    print(f"Average walkability: {neighborhoods['walkability_index'].mean():.1f}")
    print(f"Median walkability: {neighborhoods['walkability_index'].median():.1f}")
    print(f"Std deviation: {neighborhoods['walkability_index'].std():.1f}")
    print(f"\nWalkability range: {neighborhoods['walkability_index'].min():.1f} - {neighborhoods['walkability_index'].max():.1f}")

    print("\nDistribution by category:")
    print(neighborhoods['walkability_category'].value_counts().sort_index())

    # Identify most and least walkable neighborhoods
    print("\n" + "="*60)
    print("TOP 5 MOST WALKABLE NEIGHBORHOODS")
    print("="*60)
    top_neighborhoods = neighborhoods.nlargest(5, 'walkability_index')[
        ['neighborhood_name', 'walkability_index', 'total_population', 'median_household_income']
    ]
    print(top_neighborhoods.to_string(index=False))

    print("\n" + "="*60)
    print("TOP 5 LEAST WALKABLE NEIGHBORHOODS (MOST UNDERSERVED)")
    print("="*60)
    bottom_neighborhoods = neighborhoods.nsmallest(5, 'walkability_index')[
        ['neighborhood_name', 'walkability_index', 'total_population', 'median_household_income']
    ]
    print(bottom_neighborhoods.to_string(index=False))

    # Calculate correlation with demographics
    print("\n" + "="*60)
    print("CORRELATION WITH DEMOGRAPHICS")
    print("="*60)

    if 'median_household_income' in neighborhoods.columns:
        # Convert to numeric first
        neighborhoods['median_household_income'] = pd.to_numeric(neighborhoods['median_household_income'], errors='coerce')
        neighborhoods['total_population'] = pd.to_numeric(neighborhoods['total_population'], errors='coerce')

        # Filter out rows with missing or zero values for correlation
        valid_data = neighborhoods[
            (neighborhoods['median_household_income'].notna()) &
            (neighborhoods['median_household_income'] > 0) &
            (neighborhoods['total_population'] > 0)
        ]
        if len(valid_data) > 1:
            income_corr = valid_data[['walkability_index', 'median_household_income']].corr().iloc[0, 1]
            print(f"Walkability vs. Income: {income_corr:.3f}")
        else:
            print("Insufficient demographic data for correlation analysis")

    if 'population_density' in neighborhoods.columns:
        valid_data = neighborhoods[
            (neighborhoods['population_density'].notna()) &
            (neighborhoods['population_density'] > 0)
        ]
        if len(valid_data) > 1:
            density_corr = valid_data[['walkability_index', 'population_density']].corr().iloc[0, 1]
            print(f"Walkability vs. Population Density: {density_corr:.3f}")
        else:
            print("Insufficient density data for correlation analysis")

    # Save
    output_path = Path("data/processed/neighborhoods_with_walkability.geojson")
    neighborhoods.to_file(output_path, driver='GeoJSON')

    print(f"\n[OK] Saved to {output_path}")

    return neighborhoods


if __name__ == "__main__":
    neighborhoods = create_walkability_index_neighborhoods()

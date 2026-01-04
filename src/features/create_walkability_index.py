# src/features/create_walkability_index.py

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


def create_walkability_index():
    """
    Create composite walkability index from distance features
    """
    
    print("Loading data with distance features...")
    tracts = gpd.read_file("data/processed/tracts_with_distances.geojson")
    
    print(f"  Loaded {len(tracts)} tracts")
    
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
        
        if distance_col in tracts.columns:
            # Different thresholds for different amenities
            if amenity_type in ['parks', 'grocery_stores', 'transit_stops']:
                # Daily use - stricter thresholds
                tracts[score_col] = tracts[distance_col].apply(
                    lambda d: distance_to_score(d, ideal=400, acceptable=800, poor=1500)
                )
            elif amenity_type in ['schools', 'libraries']:
                # Regular use - moderate thresholds
                tracts[score_col] = tracts[distance_col].apply(
                    lambda d: distance_to_score(d, ideal=600, acceptable=1200, poor=2000)
                )
            else:
                # Occasional use - lenient thresholds
                tracts[score_col] = tracts[distance_col].apply(
                    lambda d: distance_to_score(d, ideal=800, acceptable=1500, poor=3000)
                )
            
            print(f"  {amenity_type}: avg score = {tracts[score_col].mean():.1f}")
        else:
            print(f"  Warning: {distance_col} not found, setting score to 0")
            tracts[score_col] = 0
    
    # Calculate weighted walkability index
    print("\nCalculating composite walkability index...")
    
    tracts['walkability_index'] = 0
    for amenity_type, weight in weights.items():
        score_col = f'{amenity_type}_score'
        if score_col in tracts.columns:
            tracts['walkability_index'] += tracts[score_col] * weight
    
    # Round to 1 decimal place
    tracts['walkability_index'] = tracts['walkability_index'].round(1)
    
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
    
    tracts['walkability_category'] = tracts['walkability_index'].apply(classify_walkability)
    
    # Summary statistics
    print("\n" + "="*60)
    print("WALKABILITY INDEX SUMMARY")
    print("="*60)
    print(f"\nTotal tracts: {len(tracts)}")
    print(f"Average walkability: {tracts['walkability_index'].mean():.1f}")
    print(f"Median walkability: {tracts['walkability_index'].median():.1f}")
    print(f"Std deviation: {tracts['walkability_index'].std():.1f}")
    print(f"\nWalkability range: {tracts['walkability_index'].min():.1f} - {tracts['walkability_index'].max():.1f}")
    
    print("\nDistribution by category:")
    print(tracts['walkability_category'].value_counts().sort_index())
    
    # Identify most and least walkable tracts
    print("\n" + "="*60)
    print("TOP 5 MOST WALKABLE TRACTS")
    print("="*60)
    top_tracts = tracts.nlargest(5, 'walkability_index')[
        ['GEOID', 'walkability_index', 'total_population', 'median_household_income']
    ]
    print(top_tracts.to_string(index=False))
    
    print("\n" + "="*60)
    print("TOP 5 LEAST WALKABLE TRACTS (MOST UNDERSERVED)")
    print("="*60)
    bottom_tracts = tracts.nsmallest(5, 'walkability_index')[
        ['GEOID', 'walkability_index', 'total_population', 'median_household_income']
    ]
    print(bottom_tracts.to_string(index=False))
    
    # Calculate correlation with demographics
    print("\n" + "="*60)
    print("CORRELATION WITH DEMOGRAPHICS")
    print("="*60)
    
    if 'median_household_income' in tracts.columns:
        income_corr = tracts[['walkability_index', 'median_household_income']].corr().iloc[0, 1]
        print(f"Walkability vs. Income: {income_corr:.3f}")
    
    if 'population_density' in tracts.columns:
        density_corr = tracts[['walkability_index', 'population_density']].corr().iloc[0, 1]
        print(f"Walkability vs. Population Density: {density_corr:.3f}")
    
    # Save
    output_path = Path("data/processed/tracts_with_walkability.geojson")
    tracts.to_file(output_path, driver='GeoJSON')
    
    print(f"\n✓ Saved to {output_path}")
    
    return tracts


if __name__ == "__main__":
    tracts = create_walkability_index()
# run_full_analysis.py
"""
Master pipeline script for Urban Equity Analysis
Runs the complete analysis workflow from data collection to gap analysis
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, 'src')

# Import all pipeline stages
from datacollection.get_study_area import get_los_angeles_boundary
from datacollection.get_neighborhoods import get_los_angeles_neighborhoods
from datacollection.get_censusdata import get_census_tracts_la, get_census_demographics
from datacollection.get_amenities import collect_all_amenities
from datacollection.get_street_network import get_street_network_la

from preprocessing.clean_census_data import clean_and_merge_census
from preprocessing.clean_amenities import clean_amenities
from preprocessing.validate_network import validate_street_network
from preprocessing.aggregate_to_neighborhoods import aggregate_demographics_to_neighborhoods

from features.calculate_distances import calculate_nearest_amenity_distances
from features.calculate_distances_neighborhoods import calculate_nearest_amenity_distances_neighborhoods
from features.create_walkability_index import create_walkability_index
from features.create_walkability_index_neighborhoods import create_walkability_index_neighborhoods

from visualization.create_combined_map import create_combined_interactive_map
from features.identify_amenity_gaps import generate_gap_analysis_report
from visualization.visualize_amenity_gaps import (
    create_gap_analysis_map,
    create_equity_dashboard,
    create_interactive_recommendations_map
)


def run_data_collection(census_api_key):
    """Phase 1: Collect all raw data"""
    print("\n" + "="*80)
    print("PHASE 1: DATA COLLECTION")
    print("="*80)

    print("\nStep 1.1: Getting LA boundary...")
    boundary = get_los_angeles_boundary()

    print("\nStep 1.2: Loading neighborhoods from shapefile...")
    neighborhoods = get_los_angeles_neighborhoods()

    print("\nStep 1.3: Getting census tracts...")
    tracts = get_census_tracts_la()

    print("\nStep 1.4: Getting demographic data...")
    demographics = get_census_demographics(census_api_key)

    print("\nStep 1.5: Collecting amenities from OpenStreetMap...")
    amenities = collect_all_amenities()

    print("\nStep 1.6: Downloading street network...")
    network = get_street_network_la()

    print("\n[OK] Phase 1 Complete: Data collection finished")
    return True


def run_preprocessing():
    """Phase 2: Clean and preprocess data"""
    print("\n" + "="*80)
    print("PHASE 2: DATA PREPROCESSING")
    print("="*80)

    print("\nStep 2.1: Cleaning and merging census data...")
    census_clean = clean_and_merge_census()

    print("\nStep 2.2: Cleaning amenities...")
    amenities_clean = clean_amenities()

    print("\nStep 2.3: Validating street network...")
    network = validate_street_network()

    print("\nStep 2.4: Aggregating demographics to neighborhoods...")
    neighborhoods_with_demographics = aggregate_demographics_to_neighborhoods()

    print("\n[OK] Phase 2 Complete: Data preprocessing finished")
    return True


def run_feature_engineering():
    """Phase 3: Calculate distances and walkability scores"""
    print("\n" + "="*80)
    print("PHASE 3: FEATURE ENGINEERING")
    print("="*80)

    print("\nStep 3.1: Calculating distances for census tracts...")
    tracts_with_distances = calculate_nearest_amenity_distances()

    print("\nStep 3.2: Creating walkability index for census tracts...")
    tracts_with_walkability = create_walkability_index()

    print("\nStep 3.3: Calculating distances for neighborhoods...")
    neighborhoods_with_distances = calculate_nearest_amenity_distances_neighborhoods()

    print("\nStep 3.4: Creating walkability index for neighborhoods...")
    neighborhoods_with_walkability = create_walkability_index_neighborhoods()

    print("\n[OK] Phase 3 Complete: Feature engineering finished")
    return True


def run_visualization():
    """Phase 4: Create visualizations"""
    print("\n" + "="*80)
    print("PHASE 4: VISUALIZATION")
    print("="*80)

    print("\nStep 4.1: Creating combined walkability map...")
    create_combined_interactive_map()

    print("\n[OK] Phase 4 Complete: Visualization finished")
    print("  Output: outputs/walkability_map_combined.html")
    return True


def run_gap_analysis():
    """Phase 5: Equity-focused gap analysis"""
    print("\n" + "="*80)
    print("PHASE 5: AMENITY GAP ANALYSIS")
    print("="*80)

    import geopandas as gpd

    print("\nLoading neighborhood data...")
    neighborhoods = gpd.read_file("data/processed/neighborhoods_with_walkability.geojson")

    # Priority amenities
    amenity_types = ['parks', 'grocery_stores', 'hospitals', 'transit_stops']

    print("\nStep 5.1: Running gap analysis...")
    results = generate_gap_analysis_report(
        neighborhoods,
        amenity_types,
        output_dir="outputs/gap_analysis"
    )

    print("\nStep 5.2: Creating gap visualizations...")
    output_dir = Path("outputs/gap_analysis")

    # Individual maps
    for amenity, data in results.items():
        create_gap_analysis_map(
            data['gdf_with_scores'],
            amenity,
            data,
            output_path=output_dir / f'gap_map_{amenity}.html'
        )

    # Dashboard
    create_equity_dashboard(
        results,
        output_path=output_dir / 'gap_analysis_dashboard.png'
    )

    # Combined recommendations
    create_interactive_recommendations_map(
        results,
        neighborhoods,
        output_path=output_dir / 'recommendations_combined_map.html'
    )

    print("\n[OK] Phase 5 Complete: Gap analysis finished")
    print("  Output: outputs/gap_analysis/")
    return True


def main():
    """Run the complete analysis pipeline"""

    print("="*80)
    print("URBAN EQUITY ANALYSIS - FULL PIPELINE")
    print("Los Angeles Walkability and Amenity Access Study")
    print("="*80)

    # Check for Census API key
    CENSUS_API_KEY = os.getenv('CENSUS_API_KEY')
    if not CENSUS_API_KEY:
        print("\nWARNING: CENSUS_API_KEY not found in .env file")
        print("Phase 1 (data collection) will be skipped.")
        print("Make sure you have already collected data or add API key to .env\n")
        skip_collection = True
    else:
        print(f"\nUsing Census API Key: {CENSUS_API_KEY[:10]}...\n")
        skip_collection = False

    try:
        # Phase 1: Data Collection (optional if data already exists)
        if not skip_collection:
            if input("Run Phase 1: Data Collection? (y/n): ").lower() == 'y':
                run_data_collection(CENSUS_API_KEY)

        # Phase 2: Preprocessing
        if input("\nRun Phase 2: Data Preprocessing? (y/n): ").lower() == 'y':
            run_preprocessing()

        # Phase 3: Feature Engineering
        if input("\nRun Phase 3: Feature Engineering? (y/n): ").lower() == 'y':
            run_feature_engineering()

        # Phase 4: Visualization
        if input("\nRun Phase 4: Visualization? (y/n): ").lower() == 'y':
            run_visualization()

        # Phase 5: Gap Analysis
        if input("\nRun Phase 5: Gap Analysis? (y/n): ").lower() == 'y':
            run_gap_analysis()

        # Summary
        print("\n" + "="*80)
        print("ANALYSIS PIPELINE COMPLETE!")
        print("="*80)

        print("\nKey Outputs:")
        print("  1. Walkability Map: outputs/walkability_map_combined.html")
        print("  2. Gap Analysis: outputs/gap_analysis/")
        print("     - gap_analysis_report.txt")
        print("     - recommendations_combined_map.html")
        print("     - Individual amenity maps and CSVs")

        print("\nData Files:")
        print("  - data/processed/neighborhoods_with_walkability.geojson")
        print("  - data/processed/tracts_with_walkability.geojson")
        print("  - data/processed/neighborhoods_with_demographics.geojson")

    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user.")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

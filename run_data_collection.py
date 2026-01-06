# run_data_collection.py

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables FIRST
load_dotenv()

# Add src to path
sys.path.insert(0, 'src')

from datacollection.get_study_area import get_los_angeles_boundary
from datacollection.get_neighborhoods import get_los_angeles_neighborhoods
from datacollection.get_censusdata import get_census_tracts_la, get_census_demographics
from datacollection.get_amenities import collect_all_amenities
from datacollection.get_street_network import get_street_network_la
from preprocessing.validate_data import validate_collected_data

def main():
    """
    Run complete data collection pipeline
    """
    
    # Get API key
    CENSUS_API_KEY = os.getenv('CENSUS_API_KEY')
    
    if not CENSUS_API_KEY:
        print("ERROR: CENSUS_API_KEY not found in .env file")
        print("Please create a .env file with your Census API key")
        return
    
    print("Starting data collection for Urban Equity Analysis...\n")
    print(f"Using Census API Key: {CENSUS_API_KEY[:10]}...\n")
    
    try:
        # Step 1: Get study area
        print("Step 1: Getting LA boundary...")
        boundary = get_los_angeles_boundary()
        
        # Step 2: Get neighborhoods
        print("\nStep 2: Getting neighborhoods...")
        neighborhoods = get_los_angeles_neighborhoods()

        # Step 3: Get census tracts (for demographics aggregation)
        print("\nStep 3: Getting census tracts...")
        tracts = get_census_tracts_la()

        # Step 4: Get demographics
        print("\nStep 4: Getting demographic data...")
        demographics = get_census_demographics(CENSUS_API_KEY)
        
        # Step 5: Get amenities
        print("\nStep 5: Collecting amenities from OSM...")
        amenities = collect_all_amenities()

        # Step 6: Get street network
        print("\nStep 6: Downloading street network...")
        network = get_street_network_la()

        # Step 7: Validate
        print("\nStep 7: Validating data...")
        validate_collected_data()
        
        print("\n" + "="*50)
        print("✓ DATA COLLECTION COMPLETE!")
        print("="*50)
        print("\nNext steps:")
        print("1. Review data in data/raw/ directory")
        print("2. Run preprocessing scripts")
        print("3. Begin feature engineering")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
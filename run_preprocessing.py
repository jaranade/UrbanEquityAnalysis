# run_preprocessing.py (in project root)

import sys
sys.path.insert(0, 'src')

from preprocessing.clean_census_data import clean_and_merge_census
from preprocessing.clean_amenities import clean_amenities
from preprocessing.validate_network import validate_street_network
from preprocessing.spatial_joins import assign_amenities_to_tracts

def main():
    """
    Run complete preprocessing pipeline
    """
    
    print("="*60)
    print("PHASE 2: DATA PREPROCESSING & CLEANING")
    print("="*60)
    
    try:
        # Step 1: Clean census data
        print("\n" + "="*60)
        print("STEP 1: Cleaning Census Data")
        print("="*60)
        census_clean = clean_and_merge_census()
        
        # Step 2: Clean amenities
        print("\n" + "="*60)
        print("STEP 2: Cleaning Amenities")
        print("="*60)
        amenities_clean = clean_amenities()
        
        # Step 3: Validate network
        print("\n" + "="*60)
        print("STEP 3: Validating Street Network")
        print("="*60)
        network = validate_street_network()
        
        # Step 4: Spatial joins
        print("\n" + "="*60)
        print("STEP 4: Spatial Joins - Amenities to Tracts")
        print("="*60)
        tracts_enriched = assign_amenities_to_tracts()
        
        print("\n" + "="*60)
        print("✓ PREPROCESSING COMPLETE!")
        print("="*60)
        print("\nProcessed data saved in data/processed/")
        print("\nNext steps:")
        print("1. Explore data with notebooks/01_exploratory_analysis.ipynb")
        print("2. Begin feature engineering (Phase 3)")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
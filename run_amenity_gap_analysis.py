# run_amenity_gap_analysis.py

import sys
from pathlib import Path
import geopandas as gpd

sys.path.insert(0, 'src')

from features.identify_amenity_gaps import generate_gap_analysis_report
from visualization.visualize_amenity_gaps import (
    create_gap_analysis_map,
    create_equity_dashboard,
    create_interactive_recommendations_map
)


def main():
    """
    Run complete amenity gap analysis with equity focus
    """

    print("="*80)
    print("URBAN EQUITY ANALYSIS - AMENITY GAP ASSESSMENT")
    print("="*80)
    print("\nThis analysis identifies underserved areas and recommends optimal")
    print("locations for new amenities, with priority given to lower-income")
    print("communities.\n")

    # Load neighborhood data
    print("Loading neighborhood data...")
    try:
        neighborhoods = gpd.read_file("data/processed/neighborhoods_with_walkability.geojson")
        print(f"  Loaded {len(neighborhoods)} neighborhoods")
        print(f"  Total population: {neighborhoods['total_population'].sum():,.0f}")
    except Exception as e:
        print(f"ERROR: Could not load neighborhood data: {e}")
        print("Make sure you have run the walkability analysis first.")
        return

    # Define priority amenities
    amenity_types = [
        'parks',
        'grocery_stores',
        'hospitals',
        'transit_stops'
    ]

    print(f"\nAnalyzing {len(amenity_types)} priority amenity types:")
    for amenity in amenity_types:
        print(f"  - {amenity.replace('_', ' ').title()}")

    # Run gap analysis
    print("\n" + "="*80)
    print("PHASE 1: GAP ANALYSIS")
    print("="*80)

    try:
        results = generate_gap_analysis_report(
            neighborhoods,
            amenity_types,
            output_dir="outputs/gap_analysis"
        )
    except Exception as e:
        print(f"\nERROR during gap analysis: {e}")
        import traceback
        traceback.print_exc()
        return

    # Create visualizations
    print("\n" + "="*80)
    print("PHASE 2: CREATING VISUALIZATIONS")
    print("="*80)

    output_dir = Path("outputs/gap_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Individual maps for each amenity
        print("\nCreating individual gap maps...")
        for amenity, data in results.items():
            create_gap_analysis_map(
                data['gdf_with_scores'],
                amenity,
                data,
                output_path=output_dir / f'gap_map_{amenity}.html'
            )

        # Equity dashboard
        print("\nCreating equity dashboard...")
        create_equity_dashboard(
            results,
            output_path=output_dir / 'gap_analysis_dashboard.png'
        )

        # Combined recommendations map
        print("\nCreating combined recommendations map...")
        create_interactive_recommendations_map(
            results,
            neighborhoods,
            output_path=output_dir / 'recommendations_combined_map.html'
        )

    except Exception as e:
        print(f"\nERROR during visualization: {e}")
        import traceback
        traceback.print_exc()
        return

    # Summary
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)

    print("\nOutputs saved to: outputs/gap_analysis/")
    print("\nGenerated files:")
    print("  Reports:")
    print("    - gap_analysis_report.txt (summary statistics)")
    print("    - all_underserved_areas.csv (ranked areas, all amenities)")
    print("    - all_recommended_locations.csv (proposed new facilities)")
    print("")
    print("  Individual Amenity CSVs:")
    for amenity in amenity_types:
        print(f"    - underserved_areas_{amenity}.csv")
        print(f"    - recommended_locations_{amenity}.csv")
    print("")
    print("  Interactive Maps:")
    for amenity in amenity_types:
        print(f"    - gap_map_{amenity}.html")
    print("    - recommendations_combined_map.html")
    print("")
    print("  Static Charts:")
    print("    - gap_analysis_dashboard.png")

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. Review gap_analysis_report.txt for key findings")
    print("2. Open recommendations_combined_map.html to see all proposed locations")
    print("3. Open individual gap maps to explore specific amenity types")
    print("4. Share recommended_locations CSVs with urban planning stakeholders")
    print("\nThese recommendations prioritize equity by targeting underserved,")
    print("lower-income communities with the poorest access to amenities.")


if __name__ == "__main__":
    main()

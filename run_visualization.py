# run_visualization.py

import sys
from pathlib import Path

sys.path.insert(0, 'src')

from visualization.create_combined_map import create_combined_interactive_map

def main():
    """
    Generate the combined interactive walkability map with layer toggle
    """

    print("="*80)
    print("URBAN EQUITY ANALYSIS - WALKABILITY VISUALIZATION")
    print("="*80)
    print("\nGenerating combined interactive map...")
    print("This map includes both census tract and neighborhood layers")
    print("with a toggle control to switch between them.\n")

    try:
        create_combined_interactive_map()

        print("\n" + "="*80)
        print("SUCCESS!")
        print("="*80)
        print("\nYour interactive walkability map is ready:")
        print("  File: outputs/walkability_map_combined.html")
        print("\nHow to use:")
        print("  1. Open the HTML file in your web browser")
        print("  2. Use the layer control (top-right) to toggle between:")
        print("     - Census Tracts (detailed, 2,478 areas)")
        print("     - Neighborhoods (aggregated, 114 areas from your shapefile)")
        print("  3. Hover over any area to see detailed walkability information")
        print("  4. Zoom and pan to explore different parts of Los Angeles")
        print("\nNext steps:")
        print("  - Run 'python run_amenity_gap_analysis.py' for equity analysis")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

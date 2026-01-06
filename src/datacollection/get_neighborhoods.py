
import geopandas as gpd
import osmnx as ox
from pathlib import Path
import pandas as pd

def get_los_angeles_neighborhoods():
    """
    Load LA neighborhood boundaries from shapefile
    """
    # Load from shapefile
    shapefile_path = Path("data/raw/8494cd42-db48-4af1-a215-a2c8f61e96a22020328-1-621do0.x5yiu.shp")

    if not shapefile_path.exists():
        raise FileNotFoundError(f"Shapefile not found at {shapefile_path}")

    print(f"Reading shapefile from {shapefile_path}...")
    neighborhoods = gpd.read_file(shapefile_path)

    print(f"  Loaded {len(neighborhoods)} neighborhoods")
    print(f"  Original CRS: {neighborhoods.crs}")
    print(f"  Columns: {neighborhoods.columns.tolist()}")

    # Identify the name column (common names: name, NAME, neighborho, etc.)
    name_candidates = ['name', 'NAME', 'Name', 'neighborho', 'NEIGHBORHO', 'label', 'LABEL']
    name_col = None
    for candidate in name_candidates:
        if candidate in neighborhoods.columns:
            name_col = candidate
            break

    if name_col is None:
        # If no name column found, use the first non-geometry column
        non_geom_cols = [col for col in neighborhoods.columns if col != 'geometry']
        if non_geom_cols:
            name_col = non_geom_cols[0]
            print(f"  Using '{name_col}' as neighborhood name column")
        else:
            print("  Warning: No name column found, creating generic names")
            neighborhoods['neighborhood_name'] = [f"Neighborhood_{i+1}" for i in range(len(neighborhoods))]
            name_col = 'neighborhood_name'

    # Standardize column names
    if name_col != 'neighborhood_name':
        neighborhoods['neighborhood_name'] = neighborhoods[name_col]

    # Create unique IDs
    neighborhoods['neighborhood_id'] = range(1, len(neighborhoods) + 1)

    # Keep only necessary columns
    neighborhoods = neighborhoods[['neighborhood_id', 'neighborhood_name', 'geometry']].copy()

    # Convert to EPSG:2229 (California State Plane) for consistency
    if neighborhoods.crs != "EPSG:2229":
        print(f"  Converting from {neighborhoods.crs} to EPSG:2229...")
        neighborhoods = neighborhoods.to_crs(epsg=2229)

    # Save to standardized location
    output_path = Path("data/raw/la_neighborhoods.geojson")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    neighborhoods.to_file(output_path, driver='GeoJSON')

    print(f"[OK] LA neighborhoods saved to {output_path}")
    print(f"  Number of neighborhoods: {len(neighborhoods)}")
    print(f"  CRS: {neighborhoods.crs}")

    # Print some sample names
    print("\nSample neighborhood names:")
    for name in neighborhoods['neighborhood_name'].head(10):
        print(f"  - {name}")

    return neighborhoods

if __name__ == "__main__":
    neighborhoods = get_los_angeles_neighborhoods()

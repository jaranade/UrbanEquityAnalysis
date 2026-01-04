
import geopandas as gpd
import osmnx as ox
from pathlib import Path

def get_los_angeles_boundary():
    """
    Download LA city boundary from OSM
    """
    # Get LA city boundary
    place_name = "Los Angeles, California, USA"
    
    # Download boundary polygon
    city_boundary = ox.geocode_to_gdf(place_name)
    
    # Save to file
    output_path = Path("data/raw/la_boundary.geojson")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    city_boundary.to_file(output_path, driver='GeoJSON')
    
    print(f"✓ LA boundary saved to {output_path}")
    print(f"  Area: {city_boundary.area[0] / 1e6:.2f} km²")
    
    return city_boundary

if __name__ == "__main__":
    boundary = get_los_angeles_boundary()
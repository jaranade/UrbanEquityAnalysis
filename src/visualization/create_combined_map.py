# src/visualization/create_combined_map.py

import geopandas as gpd
import folium
from pathlib import Path

def create_combined_interactive_map():
    """
    Create interactive Folium map with toggleable census tract and neighborhood layers
    """

    print("Loading data...")

    # Load census tracts
    tracts = gpd.read_file("data/processed/tracts_with_walkability.geojson")
    if tracts.crs != "EPSG:4326":
        tracts = tracts.to_crs("EPSG:4326")
    print(f"  Loaded {len(tracts)} census tracts")

    # Load neighborhoods
    neighborhoods = gpd.read_file("data/processed/neighborhoods_with_walkability.geojson")
    if neighborhoods.crs != "EPSG:4326":
        neighborhoods = neighborhoods.to_crs("EPSG:4326")
    print(f"  Loaded {len(neighborhoods)} neighborhoods")

    # Calculate map center (use tracts for center)
    center_lat = tracts.geometry.centroid.y.mean()
    center_lon = tracts.geometry.centroid.x.mean()

    print(f"Map center: ({center_lat:.4f}, {center_lon:.4f})")

    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='CartoDB positron'
    )

    print("\nCreating census tract layer...")

    # Create census tract choropleth
    tract_choropleth = folium.Choropleth(
        geo_data=tracts,
        data=tracts,
        columns=['GEOID', 'walkability_index'],
        key_on='feature.properties.GEOID',
        fill_color='RdYlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Walkability Index (0-100)',
        nan_fill_color='gray',
        nan_fill_opacity=0.3,
        name='Census Tracts',
        show=True  # Show by default
    )
    tract_choropleth.add_to(m)

    # Add census tract tooltips
    tract_style_function = lambda x: {
        'fillColor': '#ffffff00',
        'color': '#00000000',
        'weight': 0.1,
    }

    tract_highlight_function = lambda x: {
        'fillColor': '#000000',
        'color': '#000000',
        'fillOpacity': 0.20,
        'weight': 0.1
    }

    tract_tooltip = folium.GeoJsonTooltip(
        fields=['GEOID', 'walkability_index', 'walkability_category',
                'total_population', 'median_household_income',
                'parks_distance_m', 'grocery_stores_distance_m', 'hospitals_distance_m'],
        aliases=['Tract ID:', 'Walkability Score:', 'Category:',
                 'Population:', 'Median Income:',
                 'Park Distance (m):', 'Grocery Distance (m):', 'Hospital Distance (m):'],
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: #F0EFEF;
            border: 2px solid black;
            border-radius: 3px;
            box-shadow: 3px;
        """,
        max_width=800,
    )

    tract_geojson = folium.features.GeoJson(
        tracts,
        style_function=tract_style_function,
        highlight_function=tract_highlight_function,
        tooltip=tract_tooltip,
        name='Census Tracts (Interactive)',
        show=True
    )

    m.add_child(tract_geojson)

    print("Creating neighborhood layer...")

    # Create neighborhood choropleth
    neighborhood_choropleth = folium.Choropleth(
        geo_data=neighborhoods,
        data=neighborhoods,
        columns=['neighborhood_id', 'walkability_index'],
        key_on='feature.properties.neighborhood_id',
        fill_color='RdYlGn',
        fill_opacity=0.7,
        line_opacity=0.4,
        line_color='darkblue',
        legend_name='Walkability Index (0-100)',
        nan_fill_color='gray',
        nan_fill_opacity=0.3,
        name='Neighborhoods',
        show=False  # Hidden by default
    )
    neighborhood_choropleth.add_to(m)

    # Add neighborhood tooltips
    neighborhood_style_function = lambda x: {
        'fillColor': '#ffffff00',
        'color': '#00000000',
        'weight': 0.1,
    }

    neighborhood_highlight_function = lambda x: {
        'fillColor': '#000000',
        'color': '#000000',
        'fillOpacity': 0.20,
        'weight': 0.1
    }

    neighborhood_tooltip = folium.GeoJsonTooltip(
        fields=['neighborhood_name', 'walkability_index', 'walkability_category',
                'total_population', 'median_household_income',
                'parks_distance_m', 'grocery_stores_distance_m', 'hospitals_distance_m'],
        aliases=['Neighborhood:', 'Walkability Score:', 'Category:',
                 'Population:', 'Median Income:',
                 'Park Distance (m):', 'Grocery Distance (m):', 'Hospital Distance (m):'],
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: #F0EFEF;
            border: 2px solid black;
            border-radius: 3px;
            box-shadow: 3px;
        """,
        max_width=800,
    )

    neighborhood_geojson = folium.features.GeoJson(
        neighborhoods,
        style_function=neighborhood_style_function,
        highlight_function=neighborhood_highlight_function,
        tooltip=neighborhood_tooltip,
        name='Neighborhoods (Interactive)',
        show=False
    )

    m.add_child(neighborhood_geojson)

    # Add layer control with both data layers
    folium.LayerControl(
        position='topright',
        collapsed=False
    ).add_to(m)

    # Add title/instructions using HTML
    title_html = '''
    <div style="position: fixed;
                top: 10px;
                left: 50px;
                width: 400px;
                height: auto;
                background-color: white;
                border:2px solid grey;
                z-index:9999;
                font-size:14px;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                ">
        <h4 style="margin-top:0;">LA Walkability Analysis</h4>
        <p style="margin-bottom:5px;"><b>Use the layer control (top right) to toggle between:</b></p>
        <ul style="margin-top:5px; margin-bottom:5px;">
            <li><b>Census Tracts</b>: Fine-grained detail (2,478 tracts)</li>
            <li><b>Neighborhoods</b>: Aggregated view (114 neighborhoods)</li>
        </ul>
        <p style="margin-bottom:0; font-size:12px; color:grey;">
            Hover over areas for detailed information
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Save map
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "walkability_map_combined.html"
    m.save(str(output_path))

    print(f"\n[OK] Combined interactive map saved to {output_path}")
    print(f"  Open this file in your browser to explore!")
    print(f"\n  Features:")
    print(f"    - Toggle between census tracts and neighborhoods")
    print(f"    - Interactive tooltips with detailed information")
    print(f"    - Color-coded walkability scores (red=low, green=high)")

    return m


if __name__ == "__main__":
    create_combined_interactive_map()

    print("\n" + "="*80)
    print("[OK] COMBINED MAP COMPLETE!")
    print("="*80)
    print("\nOutput created:")
    print("  outputs/walkability_map_combined.html - Open in browser!")
    print("\nLayer options:")
    print("  1. Census Tracts - Detailed view with 2,478 tracts")
    print("  2. Neighborhoods - Aggregated view with 114 neighborhoods")
    print("  3. Toggle between layers using the control in the top-right corner")

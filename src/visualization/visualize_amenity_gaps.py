# src/visualization/visualize_amenity_gaps.py

import geopandas as gpd
import pandas as pd
import folium
from folium import plugins
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path


def create_gap_analysis_map(gdf, amenity_type, gap_results, amenity_locations=None, output_path=None):
    """
    Create interactive map showing equity gaps for an amenity type

    Parameters:
    -----------
    gdf : GeoDataFrame
        Areas with gap scores
    amenity_type : str
        Amenity type being analyzed
    gap_results : dict
        Results from gap analysis (underserved areas, recommendations)
    amenity_locations : GeoDataFrame, optional
        Existing amenity locations to show as markers
    output_path : Path, optional
        Where to save the map

    Returns:
    --------
    folium.Map
    """

    print(f"\nCreating gap analysis map for {amenity_type}...")

    # Convert to WGS84 for Folium
    gdf_map = gdf.to_crs("EPSG:4326") if gdf.crs != "EPSG:4326" else gdf.copy()

    # Calculate map center
    center_lat = gdf_map.geometry.centroid.y.mean()
    center_lon = gdf_map.geometry.centroid.x.mean()

    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='CartoDB positron'
    )

    gap_col = f'{amenity_type}_gap_score'

    # Create choropleth for gap scores
    folium.Choropleth(
        geo_data=gdf_map,
        data=gdf_map,
        columns=['neighborhood_id' if 'neighborhood_id' in gdf_map.columns else 'GEOID', gap_col],
        key_on='feature.properties.neighborhood_id' if 'neighborhood_id' in gdf_map.columns else 'feature.properties.GEOID',
        fill_color='YlOrRd',  # Yellow (low gap) to Red (high gap/underserved)
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name=f'{amenity_type.replace("_", " ").title()} - Equity Gap Score (0-1)',
        nan_fill_color='gray',
        nan_fill_opacity=0.2,
    ).add_to(m)

    # Add interactive tooltips
    name_col = 'neighborhood_name' if 'neighborhood_name' in gdf_map.columns else 'NAME'

    tooltip_fields = [
        name_col,
        'total_population',
        'median_household_income',
        f'{amenity_type}_distance_m',
        gap_col,
        f'{amenity_type}_need_score',
        f'{amenity_type}_access_score'
    ]

    tooltip_aliases = [
        'Area:',
        'Population:',
        'Median Income:',
        'Distance to Nearest (m):',
        'Equity Gap Score:',
        'Need Score:',
        'Access Score:'
    ]

    # Filter to available fields
    available_fields = [f for f in tooltip_fields if f in gdf_map.columns]
    available_aliases = [tooltip_aliases[i] for i, f in enumerate(tooltip_fields) if f in gdf_map.columns]

    tooltip = folium.GeoJsonTooltip(
        fields=available_fields,
        aliases=available_aliases,
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

    folium.features.GeoJson(
        gdf_map,
        style_function=lambda x: {
            'fillColor': '#ffffff00',
            'color': '#00000000',
            'weight': 0.1,
        },
        highlight_function=lambda x: {
            'fillColor': '#000000',
            'color': '#000000',
            'fillOpacity': 0.20,
            'weight': 0.1
        },
        tooltip=tooltip
    ).add_to(m)

    # Add recommended locations as starred markers
    if gap_results and 'recommendations' in gap_results:
        recommendations = gap_results['recommendations']

        for idx, row in recommendations.iterrows():
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(
                    f"<b>Recommended: {amenity_type.replace('_', ' ').title()}</b><br>"
                    f"{row['area_name']}<br>"
                    f"{row['justification']}",
                    max_width=300
                ),
                tooltip=f"Recommended: {row['area_name']}",
                icon=folium.Icon(color='green', icon='star', prefix='fa')
            ).add_to(m)

    # Add existing amenity locations if provided
    if amenity_locations is not None:
        amenity_map = amenity_locations.to_crs("EPSG:4326") if amenity_locations.crs != "EPSG:4326" else amenity_locations

        # Use marker cluster for many amenities
        marker_cluster = plugins.MarkerCluster(name=f'Existing {amenity_type.replace("_", " ").title()}')

        for idx, row in amenity_map.iterrows():
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=3,
                color='blue',
                fill=True,
                fillColor='blue',
                fillOpacity=0.6,
                popup=f"Existing {amenity_type.replace('_', ' ')}",
            ).add_to(marker_cluster)

        marker_cluster.add_to(m)

    # Add title
    title_html = f'''
    <div style="position: fixed;
                top: 10px;
                left: 50px;
                width: 450px;
                background-color: white;
                border:2px solid grey;
                z-index:9999;
                font-size:14px;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                ">
        <h4 style="margin-top:0;">Equity Gap Analysis: {amenity_type.replace("_", " ").title()}</h4>
        <p style="margin-bottom:5px;"><b>Red areas</b> = High equity gap (underserved)</p>
        <p style="margin-bottom:5px;"><b>Yellow areas</b> = Low equity gap (well-served)</p>
        <p style="margin-bottom:5px;"><b>Green stars</b> = Recommended new locations</p>
        <p style="margin-bottom:0; font-size:12px; color:grey;">
            Hover over areas for details. Gap score combines community need with access quality.
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Add layer control
    folium.LayerControl().add_to(m)

    # Save if path provided
    if output_path:
        m.save(str(output_path))
        print(f"  Map saved to {output_path}")

    return m


def create_equity_dashboard(results, output_path=None):
    """
    Create static visualizations showing equity analysis across amenity types

    Parameters:
    -----------
    results : dict
        Gap analysis results for multiple amenity types
    output_path : Path, optional
        Where to save the figure

    Returns:
    --------
    matplotlib Figure
    """

    print("\nCreating equity dashboard...")

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    sns.set_style("whitegrid")

    # 1. Income vs Access scatter (combined for all amenities)
    ax1 = axes[0, 0]

    for amenity, data in results.items():
        gdf = data['gdf_with_scores']
        access_col = f'{amenity}_access_score'

        valid = gdf[['median_household_income', access_col]].dropna()

        if len(valid) > 0:
            ax1.scatter(
                valid['median_household_income'],
                valid[access_col],
                alpha=0.4,
                s=30,
                label=amenity.replace('_', ' ').title()
            )

    ax1.set_xlabel('Median Household Income ($)', fontsize=12)
    ax1.set_ylabel('Access Score (0-1)', fontsize=12)
    ax1.set_title('Access vs. Income by Amenity Type', fontsize=14, fontweight='bold')
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(alpha=0.3)

    # 2. Top underserved areas (combined)
    ax2 = axes[0, 1]

    all_underserved = []
    for amenity, data in results.items():
        underserved = data['underserved'].head(3).copy()
        underserved['amenity'] = amenity.replace('_', ' ').title()
        all_underserved.append(underserved)

    if all_underserved:
        combined = pd.concat(all_underserved)
        combined['label'] = combined['area_name'] + ' (' + combined['amenity'] + ')'

        y_pos = np.arange(len(combined))
        colors = plt.cm.Reds(combined['gap_score'])

        ax2.barh(y_pos, combined['gap_score'], color=colors)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(combined['label'], fontsize=9)
        ax2.set_xlabel('Equity Gap Score', fontsize=12)
        ax2.set_title('Most Underserved Areas (Top 3 per Amenity)', fontsize=14, fontweight='bold')
        ax2.grid(alpha=0.3, axis='x')

    # 3. Gap score heatmap
    ax3 = axes[1, 0]

    # Create matrix of gap scores
    gap_matrix = []
    amenity_names = []
    area_names = []

    for amenity, data in results.items():
        underserved = data['underserved'].head(10)
        amenity_names.append(amenity.replace('_', ' ').title())

        if len(area_names) == 0:
            area_names = underserved['area_name'].tolist()

        gap_matrix.append(underserved['gap_score'].tolist())

    if gap_matrix:
        # Pad to make rectangular
        max_len = max(len(row) for row in gap_matrix)
        gap_matrix = [row + [np.nan] * (max_len - len(row)) for row in gap_matrix]

        sns.heatmap(
            gap_matrix,
            ax=ax3,
            xticklabels=area_names[:max_len],
            yticklabels=amenity_names,
            cmap='YlOrRd',
            annot=False,
            cbar_kws={'label': 'Gap Score'},
            vmin=0,
            vmax=1
        )
        ax3.set_title('Equity Gap Scores by Area and Amenity', fontsize=14, fontweight='bold')
        ax3.set_xlabel('')
        plt.setp(ax3.get_xticklabels(), rotation=45, ha='right', fontsize=9)

    # 4. Population in underserved areas
    ax4 = axes[1, 1]

    amenity_list = []
    underserved_pop = []

    for amenity, data in results.items():
        gdf = data['gdf_with_scores']
        gap_col = f'{amenity}_gap_score'

        high_gap = gdf[gdf[gap_col] > 0.5]
        pop = high_gap['total_population'].sum()

        amenity_list.append(amenity.replace('_', ' ').title())
        underserved_pop.append(pop)

    ax4.barh(amenity_list, underserved_pop, color='coral')
    ax4.set_xlabel('Population', fontsize=12)
    ax4.set_title('Population in High-Gap Areas (score > 0.5)', fontsize=14, fontweight='bold')
    ax4.grid(alpha=0.3, axis='x')

    for i, v in enumerate(underserved_pop):
        ax4.text(v, i, f' {v:,.0f}', va='center', fontsize=9)

    plt.tight_layout()

    # Save if path provided
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  Dashboard saved to {output_path}")

    return fig


def create_interactive_recommendations_map(results, gdf, output_path=None):
    """
    Create combined map with all amenity recommendations

    Parameters:
    -----------
    results : dict
        Gap analysis results for multiple amenity types
    gdf : GeoDataFrame
        Base geographic data
    output_path : Path, optional
        Where to save the map

    Returns:
    --------
    folium.Map
    """

    print("\nCreating combined recommendations map...")

    # Convert to WGS84
    gdf_map = gdf.to_crs("EPSG:4326") if gdf.crs != "EPSG:4326" else gdf.copy()

    # Calculate map center
    center_lat = gdf_map.geometry.centroid.y.mean()
    center_lon = gdf_map.geometry.centroid.x.mean()

    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='CartoDB positron'
    )

    # Color scheme for different amenities
    amenity_colors = {
        'parks': 'green',
        'grocery_stores': 'orange',
        'hospitals': 'red',
        'pharmacies': 'pink',
        'urgent_care': 'darkred',
        'transit_stops': 'blue',
        'schools': 'purple',
        'libraries': 'cadetblue'
    }

    # Add recommendations for each amenity type
    for amenity, data in results.items():
        if 'recommendations' not in data:
            continue

        recommendations = data['recommendations']
        color = amenity_colors.get(amenity, 'gray')

        feature_group = folium.FeatureGroup(name=f'{amenity.replace("_", " ").title()} Recommendations')

        for idx, row in recommendations.iterrows():
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(
                    f"<b>New {amenity.replace('_', ' ').title()}</b><br>"
                    f"<b>Location:</b> {row['area_name']}<br>"
                    f"<b>Population Served:</b> {row['population_served']:,.0f}<br>"
                    f"<b>Gap Score:</b> {row['gap_score']:.3f}<br>"
                    f"{row['justification']}",
                    max_width=350
                ),
                tooltip=f"Recommended {amenity.replace('_', ' ').title()}: {row['area_name']}",
                icon=folium.Icon(color=color, icon='plus-sign')
            ).add_to(feature_group)

        feature_group.add_to(m)

    # Add background areas
    name_col = 'neighborhood_name' if 'neighborhood_name' in gdf_map.columns else 'NAME'

    folium.features.GeoJson(
        gdf_map,
        style_function=lambda x: {
            'fillColor': '#cccccc',
            'color': '#666666',
            'weight': 1,
            'fillOpacity': 0.1,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=[name_col, 'total_population', 'median_household_income'],
            aliases=['Area:', 'Population:', 'Median Income:'],
            localize=True
        )
    ).add_to(m)

    # Add layer control
    folium.LayerControl(position='topright', collapsed=False).add_to(m)

    # Add title
    title_html = '''
    <div style="position: fixed;
                top: 10px;
                left: 50px;
                width: 450px;
                background-color: white;
                border:2px solid grey;
                z-index:9999;
                font-size:14px;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                ">
        <h4 style="margin-top:0;">Recommended Amenity Locations - All Types</h4>
        <p style="margin-bottom:5px;">Toggle layers to view recommendations by amenity type.</p>
        <p style="margin-bottom:5px;">Markers show optimal locations for new facilities based on equity gap analysis.</p>
        <p style="margin-bottom:0; font-size:12px; color:grey;">
            Click markers for details. Recommendations prioritize underserved communities.
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Save if path provided
    if output_path:
        m.save(str(output_path))
        print(f"  Combined map saved to {output_path}")

    return m


if __name__ == "__main__":
    # Example usage
    import sys
    sys.path.insert(0, 'src')
    from features.identify_amenity_gaps import generate_gap_analysis_report

    print("Loading data...")
    neighborhoods = gpd.read_file("data/processed/neighborhoods_with_walkability.geojson")

    # Run gap analysis
    amenity_types = ['parks', 'grocery_stores']
    results = generate_gap_analysis_report(neighborhoods, amenity_types)

    # Create visualizations
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

    # Combined recommendations map
    create_interactive_recommendations_map(
        results,
        neighborhoods,
        output_path=output_dir / 'recommendations_combined_map.html'
    )

    print("\nVisualization complete!")

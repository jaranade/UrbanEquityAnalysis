# src/visualization/create_walkability_map.py

import geopandas as gpd
import pandas as pd
import folium
from folium import plugins
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def create_interactive_map():
    """
    Create interactive Folium map showing walkability scores
    """
    
    print("Loading data...")
    tracts = gpd.read_file("data/processed/tracts_with_walkability.geojson")
    
    # Convert to WGS84 for Folium
    if tracts.crs != "EPSG:4326":
        tracts = tracts.to_crs("EPSG:4326")
    
    print(f"Loaded {len(tracts)} tracts")
    
    # Calculate map center
    center_lat = tracts.geometry.centroid.y.mean()
    center_lon = tracts.geometry.centroid.x.mean()
    
    print(f"Map center: ({center_lat:.4f}, {center_lon:.4f})")
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='CartoDB positron'
    )
    
    # Create choropleth layer for walkability
    print("\nCreating choropleth layer...")
    
    folium.Choropleth(
        geo_data=tracts,
        data=tracts,
        columns=['GEOID', 'walkability_index'],
        key_on='feature.properties.GEOID',
        fill_color='RdYlGn',  # Red (low) to Yellow to Green (high)
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Walkability Index (0-100)',
        nan_fill_color='gray',
        nan_fill_opacity=0.3,
    ).add_to(m)
    
    # Add tooltips with detailed info
    print("Adding interactive tooltips...")
    
    style_function = lambda x: {
        'fillColor': '#ffffff00',
        'color': '#00000000',
        'weight': 0.1,
    }
    
    highlight_function = lambda x: {
        'fillColor': '#000000',
        'color': '#000000',
        'fillOpacity': 0.20,
        'weight': 0.1
    }
    
    # Create tooltip
    tooltip = folium.GeoJsonTooltip(
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
    
    NIL = folium.features.GeoJson(
        tracts,
        style_function=style_function,
        control=False,
        highlight_function=highlight_function,
        tooltip=tooltip
    )
    
    m.add_child(NIL)
    m.keep_in_front(NIL)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save map
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "walkability_map_interactive.html"
    m.save(str(output_path))
    
    print(f"\n✓ Interactive map saved to {output_path}")
    print(f"  Open this file in your browser to explore!")
    
    return m


def create_static_visualizations():
    """
    Create static matplotlib/seaborn visualizations
    """
    
    print("\nCreating static visualizations...")
    
    tracts = gpd.read_file("data/processed/tracts_with_walkability.geojson")
    
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (15, 10)
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Walkability distribution histogram
    ax1 = axes[0, 0]
    tracts['walkability_index'].hist(bins=50, ax=ax1, color='steelblue', edgecolor='black')
    ax1.axvline(tracts['walkability_index'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
    ax1.axvline(tracts['walkability_index'].median(), color='orange', linestyle='--', linewidth=2, label='Median')
    ax1.set_xlabel('Walkability Index', fontsize=12)
    ax1.set_ylabel('Number of Tracts', fontsize=12)
    ax1.set_title('Distribution of Walkability Scores Across LA County', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # 2. Walkability by category
    ax2 = axes[0, 1]
    category_counts = tracts['walkability_category'].value_counts()
    colors = {'Excellent': '#2ecc71', 'Good': '#3498db', 'Moderate': '#f39c12', 
              'Poor': '#e74c3c', 'Very Poor': '#c0392b'}
    category_counts.plot(kind='bar', ax=ax2, color=[colors.get(x, '#95a5a6') for x in category_counts.index])
    ax2.set_xlabel('Walkability Category', fontsize=12)
    ax2.set_ylabel('Number of Tracts', fontsize=12)
    ax2.set_title('Tracts by Walkability Category', fontsize=14, fontweight='bold')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(alpha=0.3)
    
    # 3. Walkability vs Income scatter
    ax3 = axes[1, 0]
    valid_data = tracts[tracts['median_household_income'].notna()]
    scatter = ax3.scatter(
        valid_data['median_household_income'], 
        valid_data['walkability_index'],
        c=valid_data['walkability_index'],
        cmap='RdYlGn',
        alpha=0.6,
        s=50
    )
    ax3.set_xlabel('Median Household Income ($)', fontsize=12)
    ax3.set_ylabel('Walkability Index', fontsize=12)
    ax3.set_title('Walkability vs. Income (Correlation: 0.033)', fontsize=14, fontweight='bold')
    plt.colorbar(scatter, ax=ax3, label='Walkability Index')
    ax3.grid(alpha=0.3)
    
    # 4. Average distance to amenities
    ax4 = axes[1, 1]
    amenity_distances = {
        'Parks': tracts['parks_distance_m'].mean(),
        'Grocery': tracts['grocery_stores_distance_m'].mean(),
        'Transit': tracts['transit_stops_distance_m'].mean(),
        'Schools': tracts['schools_distance_m'].mean(),
        'Hospitals': tracts['hospitals_distance_m'].mean(),
        'Pharmacies': tracts['pharmacies_distance_m'].mean(),
        'Libraries': tracts['libraries_distance_m'].mean(),
        'Urgent Care': tracts['urgent_care_distance_m'].mean(),
    }
    
    pd.Series(amenity_distances).sort_values().plot(kind='barh', ax=ax4, color='coral')
    ax4.set_xlabel('Average Distance (meters)', fontsize=12)
    ax4.set_ylabel('Amenity Type', fontsize=12)
    ax4.set_title('Average Walking Distance to Nearest Amenity', fontsize=14, fontweight='bold')
    ax4.grid(alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    # Save figure
    output_path = Path("outputs/walkability_analysis.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"✓ Static visualizations saved to {output_path}")
    
    plt.close()


def create_summary_report():
    """
    Generate text summary report
    """
    
    print("\nGenerating summary report...")
    
    tracts = gpd.read_file("data/processed/tracts_with_walkability.geojson")
    
    report = []
    report.append("=" * 80)
    report.append("URBAN EQUITY ANALYSIS - LOS ANGELES COUNTY")
    report.append("Walkability and Amenity Accessibility Assessment")
    report.append("=" * 80)
    report.append("")
    
    # Overall statistics
    report.append("OVERALL STATISTICS")
    report.append("-" * 80)
    report.append(f"Total Census Tracts Analyzed: {len(tracts):,}")
    report.append(f"Total Population Covered: {tracts['total_population'].sum():,.0f}")
    report.append(f"Average Walkability Score: {tracts['walkability_index'].mean():.1f} / 100")
    report.append(f"Median Walkability Score: {tracts['walkability_index'].median():.1f} / 100")
    report.append("")
    
    # Category breakdown
    report.append("WALKABILITY CATEGORY DISTRIBUTION")
    report.append("-" * 80)
    for category in ['Excellent', 'Good', 'Moderate', 'Poor', 'Very Poor']:
        count = (tracts['walkability_category'] == category).sum()
        pct = count / len(tracts) * 100
        pop = tracts[tracts['walkability_category'] == category]['total_population'].sum()
        report.append(f"{category:12s}: {count:4d} tracts ({pct:5.1f}%) - Population: {pop:,.0f}")
    report.append("")
    
    # Underserved population
    underserved = tracts[tracts['walkability_category'].isin(['Poor', 'Very Poor'])]
    report.append("UNDERSERVED AREAS")
    report.append("-" * 80)
    report.append(f"Tracts with Poor/Very Poor walkability: {len(underserved):,}")
    report.append(f"Population in underserved areas: {underserved['total_population'].sum():,.0f}")
    report.append(f"Percentage of LA County population: {underserved['total_population'].sum() / tracts['total_population'].sum() * 100:.1f}%")
    report.append("")
    
    # Amenity distances
    report.append("AVERAGE WALKING DISTANCES TO AMENITIES")
    report.append("-" * 80)
    amenities = ['parks', 'grocery_stores', 'hospitals', 'transit_stops', 'schools', 
                 'pharmacies', 'libraries', 'urgent_care']
    for amenity in amenities:
        col = f'{amenity}_distance_m'
        avg_dist = tracts[col].mean()
        report.append(f"{amenity.replace('_', ' ').title():20s}: {avg_dist:7.0f} meters ({avg_dist/1000:.2f} km)")
    report.append("")
    
    # Equity analysis
    report.append("EQUITY ANALYSIS")
    report.append("-" * 80)
    report.append(f"Correlation: Walkability vs Income: {tracts[['walkability_index', 'median_household_income']].corr().iloc[0,1]:.3f}")
    report.append("Interpretation: Very weak correlation - walkability issues affect all income levels")
    report.append("")
    
    report_text = "\n".join(report)
    
    # Save report
    output_path = Path("outputs/walkability_report.txt")
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    print(f"✓ Summary report saved to {output_path}")
    print("\n" + report_text)


if __name__ == "__main__":
    # Create all visualizations
    create_interactive_map()
    create_static_visualizations()
    create_summary_report()
    
    print("\n" + "="*80)
    print("✓ ALL VISUALIZATIONS COMPLETE!")
    print("="*80)
    print("\nOutputs created:")
    print("  1. outputs/walkability_map_interactive.html - Open in browser!")
    print("  2. outputs/walkability_analysis.png - Static charts")
    print("  3. outputs/walkability_report.txt - Summary statistics")
    
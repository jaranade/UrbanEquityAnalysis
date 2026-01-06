# src/features/identify_amenity_gaps.py

import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path


def normalize(series):
    """Normalize a series to 0-1 range"""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val)


def calculate_equity_scores(gdf, amenity_type):
    """
    Calculate equity gap scores for an amenity type

    Parameters:
    -----------
    gdf : GeoDataFrame
        Geographic data with demographics and amenity metrics
    amenity_type : str
        One of: 'parks', 'grocery_stores', 'hospitals', 'pharmacies',
                'urgent_care', 'transit_stops', 'schools', 'libraries'

    Returns:
    --------
    GeoDataFrame with added columns:
        - {amenity}_need_score: Community need (0-1, higher = more need)
        - {amenity}_access_score: Current access (0-1, higher = better access)
        - {amenity}_gap_score: Equity gap (0-1, higher = more underserved)
    """

    gdf = gdf.copy()

    # Column names
    distance_col = f'{amenity_type}_distance_m'
    count_col = f'{amenity_type}_count_1km'
    score_col = f'{amenity_type}_score'

    # Validate columns exist
    required_cols = ['median_household_income', 'population_density',
                     distance_col, 'total_population']
    missing = [col for col in required_cols if col not in gdf.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    print(f"\nCalculating equity scores for {amenity_type}...")

    # --- NEED SCORE (0-1, higher = more need) ---

    # Income need: Lower income = higher need
    # Filter out extreme/invalid values
    valid_income = gdf['median_household_income'].notna() & (gdf['median_household_income'] > 0)
    income_need = pd.Series(0.5, index=gdf.index)  # Default to medium need
    if valid_income.any():
        income_need[valid_income] = 1 - normalize(gdf.loc[valid_income, 'median_household_income'])

    # Density need: Higher population density = higher need
    valid_density = gdf['population_density'].notna() & (gdf['population_density'] > 0)
    density_need = pd.Series(0.5, index=gdf.index)
    if valid_density.any():
        density_need[valid_density] = normalize(gdf.loc[valid_density, 'population_density'])

    # Combined need score (weighted: 70% income, 30% density)
    need_score = (income_need * 0.7) + (density_need * 0.3)

    # --- ACCESS SCORE (0-1, higher = better access) ---

    # Distance score: Closer = better
    valid_distance = gdf[distance_col].notna() & (gdf[distance_col] > 0)
    distance_score = pd.Series(0.0, index=gdf.index)  # Default to worst
    if valid_distance.any():
        # Inverse: high distance = low score
        distance_score[valid_distance] = 1 - normalize(gdf.loc[valid_distance, distance_col])

    # Count score: More amenities nearby = better
    count_score = pd.Series(0.0, index=gdf.index)
    if count_col in gdf.columns:
        valid_count = gdf[count_col].notna()
        if valid_count.any():
            count_score[valid_count] = normalize(gdf.loc[valid_count, count_col])

    # Existing amenity score (if available)
    existing_score = pd.Series(0.0, index=gdf.index)
    if score_col in gdf.columns:
        valid_score = gdf[score_col].notna()
        if valid_score.any():
            existing_score[valid_score] = gdf.loc[valid_score, score_col] / 100.0

    # Combined access score (weighted)
    access_score = (distance_score * 0.4) + (count_score * 0.3) + (existing_score * 0.3)

    # --- GAP SCORE (0-1, higher = bigger equity gap) ---
    # High need + low access = high gap
    gap_score = need_score * (1 - access_score)

    # Add to dataframe
    prefix = amenity_type
    gdf[f'{prefix}_need_score'] = need_score
    gdf[f'{prefix}_access_score'] = access_score
    gdf[f'{prefix}_gap_score'] = gap_score

    print(f"  Need score range: {need_score.min():.3f} - {need_score.max():.3f}")
    print(f"  Access score range: {access_score.min():.3f} - {access_score.max():.3f}")
    print(f"  Gap score range: {gap_score.min():.3f} - {gap_score.max():.3f}")

    return gdf


def identify_underserved_areas(gdf, amenity_type, top_n=10, min_population=1000):
    """
    Identify the most underserved areas for an amenity type

    Parameters:
    -----------
    gdf : GeoDataFrame
        Data with gap scores (from calculate_equity_scores)
    amenity_type : str
        Amenity type to analyze
    top_n : int
        Number of top underserved areas to return
    min_population : int
        Minimum population threshold to avoid unpopulated areas

    Returns:
    --------
    DataFrame with underserved areas ranked by gap score
    """

    gap_col = f'{amenity_type}_gap_score'

    if gap_col not in gdf.columns:
        raise ValueError(f"Gap scores not found. Run calculate_equity_scores() first.")

    # Filter by population
    filtered = gdf[gdf['total_population'] >= min_population].copy()

    print(f"\nIdentifying underserved areas for {amenity_type}...")
    print(f"  Areas with population >= {min_population}: {len(filtered)}")

    # Sort by gap score (descending)
    underserved = filtered.sort_values(gap_col, ascending=False).head(top_n)

    # Prepare output columns
    id_col = 'neighborhood_id' if 'neighborhood_id' in gdf.columns else 'GEOID'
    name_col = 'neighborhood_name' if 'neighborhood_name' in gdf.columns else 'NAME'

    output_cols = [
        id_col,
        name_col,
        'total_population',
        'median_household_income',
        f'{amenity_type}_distance_m',
        f'{amenity_type}_gap_score',
        f'{amenity_type}_need_score',
        f'{amenity_type}_access_score'
    ]

    # Add count column if available
    count_col = f'{amenity_type}_count_1km'
    if count_col in gdf.columns:
        output_cols.insert(5, count_col)

    # Filter to available columns
    available_cols = [col for col in output_cols if col in underserved.columns]
    result = underserved[available_cols].copy()

    # Rename for clarity
    result = result.rename(columns={
        id_col: 'area_id',
        name_col: 'area_name',
        'total_population': 'population',
        'median_household_income': 'median_income',
        f'{amenity_type}_distance_m': 'distance_to_nearest_m',
        f'{amenity_type}_count_1km': 'count_within_1km',
        f'{amenity_type}_gap_score': 'gap_score',
        f'{amenity_type}_need_score': 'need_score',
        f'{amenity_type}_access_score': 'access_score'
    })

    print(f"  Top {len(result)} underserved areas identified")

    return result


def find_optimal_locations(gdf, amenity_type, underserved_areas):
    """
    Find optimal coordinates for new amenity placements

    Parameters:
    -----------
    gdf : GeoDataFrame
        Areas with geometry
    amenity_type : str
        Type of amenity
    underserved_areas : DataFrame
        Output from identify_underserved_areas()

    Returns:
    --------
    DataFrame with recommended locations (lat, lon, area_name, justification)
    """

    print(f"\nFinding optimal locations for new {amenity_type}...")

    # Ensure gdf is in WGS84 for lat/lon
    gdf_wgs84 = gdf.to_crs("EPSG:4326") if gdf.crs != "EPSG:4326" else gdf.copy()

    id_col = 'neighborhood_id' if 'neighborhood_id' in gdf.columns else 'GEOID'
    name_col = 'neighborhood_name' if 'neighborhood_name' in gdf.columns else 'NAME'

    recommendations = []

    for idx, row in underserved_areas.iterrows():
        area_id = row['area_id']
        area_name = row['area_name']
        population = row['population']
        gap_score = row['gap_score']

        # Find the area in gdf
        area = gdf_wgs84[gdf_wgs84[id_col] == area_id]

        if len(area) == 0:
            continue

        # Use centroid as optimal location
        centroid = area.geometry.centroid.iloc[0]
        lat = centroid.y
        lon = centroid.x

        # Create justification
        justification = (
            f"High equity gap (score: {gap_score:.2f}). "
            f"Would serve {population:,.0f} residents with "
            f"median income ${row['median_income']:,.0f}."
        )

        recommendations.append({
            'area_name': area_name,
            'latitude': lat,
            'longitude': lon,
            'population_served': population,
            'gap_score': gap_score,
            'justification': justification
        })

    result = pd.DataFrame(recommendations)

    print(f"  Generated {len(result)} location recommendations")

    return result


def generate_gap_analysis_report(gdf, amenity_types, output_dir="outputs/gap_analysis"):
    """
    Generate comprehensive gap analysis report for multiple amenity types

    Parameters:
    -----------
    gdf : GeoDataFrame
        Neighborhood or tract data
    amenity_types : list
        List of amenity types to analyze
    output_dir : str
        Directory to save outputs

    Returns:
    --------
    dict with DataFrames for each amenity type
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("AMENITY GAP ANALYSIS - EQUITY ASSESSMENT")
    print("="*80)

    results = {}
    all_underserved = []
    all_recommendations = []

    for amenity in amenity_types:
        print(f"\n{'='*80}")
        print(f"ANALYZING: {amenity.upper().replace('_', ' ')}")
        print(f"{'='*80}")

        try:
            # Calculate scores
            gdf = calculate_equity_scores(gdf, amenity)

            # Identify underserved areas
            underserved = identify_underserved_areas(gdf, amenity, top_n=10)

            # Find optimal locations
            recommendations = find_optimal_locations(gdf, amenity, underserved)

            # Save individual CSVs
            underserved.to_csv(output_path / f'underserved_areas_{amenity}.csv', index=False)
            recommendations.to_csv(output_path / f'recommended_locations_{amenity}.csv', index=False)

            # Store for combined report
            underserved['amenity_type'] = amenity
            recommendations['amenity_type'] = amenity
            all_underserved.append(underserved)
            all_recommendations.append(recommendations)

            results[amenity] = {
                'underserved': underserved,
                'recommendations': recommendations,
                'gdf_with_scores': gdf
            }

        except Exception as e:
            print(f"  ERROR analyzing {amenity}: {e}")
            continue

    # Save combined reports
    if all_underserved:
        combined_underserved = pd.concat(all_underserved, ignore_index=True)
        combined_underserved.to_csv(output_path / 'all_underserved_areas.csv', index=False)

    if all_recommendations:
        combined_recommendations = pd.concat(all_recommendations, ignore_index=True)
        combined_recommendations.to_csv(output_path / 'all_recommended_locations.csv', index=False)

    # Generate text summary report
    generate_text_summary(results, output_path, gdf)

    print("\n" + "="*80)
    print("GAP ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nOutputs saved to: {output_path}")

    return results


def generate_text_summary(results, output_path, gdf):
    """Generate human-readable text summary"""

    report = []
    report.append("=" * 80)
    report.append("URBAN EQUITY ANALYSIS - AMENITY GAP ASSESSMENT")
    report.append("Los Angeles Neighborhoods")
    report.append("=" * 80)
    report.append("")

    total_population = gdf['total_population'].sum()
    report.append(f"Total Population Analyzed: {total_population:,.0f}")
    report.append(f"Number of Areas: {len(gdf)}")
    report.append("")

    for amenity, data in results.items():
        report.append("=" * 80)
        report.append(f"{amenity.upper().replace('_', ' ')} - GAP ANALYSIS")
        report.append("=" * 80)
        report.append("")

        underserved = data['underserved']
        recommendations = data['recommendations']

        report.append(f"Top 10 Most Underserved Areas:")
        report.append("-" * 80)

        for idx, row in underserved.head(10).iterrows():
            report.append(
                f"  {row['area_name']:30s} | "
                f"Pop: {row['population']:>8,.0f} | "
                f"Income: ${row['median_income']:>8,.0f} | "
                f"Distance: {row['distance_to_nearest_m']:>6,.0f}m | "
                f"Gap: {row['gap_score']:.3f}"
            )

        report.append("")
        report.append(f"Recommended New {amenity.replace('_', ' ').title()} Locations:")
        report.append("-" * 80)

        for idx, row in recommendations.head(5).iterrows():
            report.append(
                f"  {row['area_name']:30s} | "
                f"Lat: {row['latitude']:>9.5f}, Lon: {row['longitude']:>10.5f} | "
                f"Serves: {row['population_served']:>8,.0f}"
            )

        # Calculate equity metrics
        gdf_with_scores = data['gdf_with_scores']
        gap_col = f'{amenity}_gap_score'

        underserved_pop = gdf_with_scores[
            gdf_with_scores[gap_col] > 0.5
        ]['total_population'].sum()

        report.append("")
        report.append(f"Population in High-Gap Areas (score > 0.5): {underserved_pop:,.0f}")
        report.append(f"Percentage of Total: {(underserved_pop/total_population*100):.1f}%")
        report.append("")

    report_text = "\n".join(report)

    # Save report
    with open(output_path / 'gap_analysis_report.txt', 'w') as f:
        f.write(report_text)

    print("\n" + report_text)


if __name__ == "__main__":
    # Example usage
    print("Loading neighborhood data...")
    neighborhoods = gpd.read_file("data/processed/neighborhoods_with_walkability.geojson")

    # Analyze all priority amenities
    amenity_types = ['parks', 'grocery_stores', 'hospitals', 'transit_stops']

    results = generate_gap_analysis_report(neighborhoods, amenity_types)

    print("\nAnalysis complete! Check outputs/gap_analysis/ for results.")

# Function Reference - Urban Equity Analysis

## Quick Reference for Imports

This document lists the correct function names to import from each module.

---

## Data Collection (`src/datacollection/`)

```python
from datacollection.get_study_area import get_los_angeles_boundary
from datacollection.get_neighborhoods import get_los_angeles_neighborhoods
from datacollection.get_censusdata import get_census_tracts_la, get_census_demographics
from datacollection.get_amenities import collect_all_amenities
from datacollection.get_street_network import get_street_network_la
```

---

## Preprocessing (`src/preprocessing/`)

```python
from preprocessing.clean_census_data import clean_and_merge_census
from preprocessing.clean_amenities import clean_amenities
from preprocessing.validate_network import validate_street_network
from preprocessing.spatial_joins import assign_amenities_to_tracts
from preprocessing.aggregate_to_neighborhoods import aggregate_demographics_to_neighborhoods
```

**Note:** `clean_census_data.py` automatically fixes GEOID formatting (pads to 11 digits) on lines 29-30.

---

## Features (`src/features/`)

### Distance Calculations

```python
# Census tracts
from features.calculate_distances import calculate_nearest_amenity_distances

# Neighborhoods
from features.calculate_distances_neighborhoods import calculate_nearest_amenity_distances_neighborhoods
```

### Walkability Index

```python
# Census tracts
from features.create_walkability_index import create_walkability_index

# Neighborhoods
from features.create_walkability_index_neighborhoods import create_walkability_index_neighborhoods
```

### Gap Analysis

```python
from features.identify_amenity_gaps import (
    calculate_equity_scores,
    identify_underserved_areas,
    find_optimal_locations,
    generate_gap_analysis_report
)
```

---

## Visualization (`src/visualization/`)

### Walkability Maps

```python
from visualization.create_combined_map import create_combined_interactive_map
```

### Gap Analysis Maps

```python
from visualization.visualize_amenity_gaps import (
    create_gap_analysis_map,
    create_equity_dashboard,
    create_interactive_recommendations_map
)
```

---

## Common Usage Patterns

### Full Pipeline (Automated)

```python
# Just run the master script
python run_full_analysis.py
```

### Manual Step-by-Step

```python
import geopandas as gpd
from features.identify_amenity_gaps import calculate_equity_scores, identify_underserved_areas

# Load data
neighborhoods = gpd.read_file("data/processed/neighborhoods_with_walkability.geojson")

# Calculate gap scores
neighborhoods = calculate_equity_scores(neighborhoods, 'parks')

# Get underserved areas
underserved = identify_underserved_areas(neighborhoods, 'parks', top_n=10)

print(underserved)
```

### Custom Gap Analysis

```python
from features.identify_amenity_gaps import generate_gap_analysis_report
import geopandas as gpd

neighborhoods = gpd.read_file("data/processed/neighborhoods_with_walkability.geojson")

# Analyze specific amenities
amenities = ['parks', 'libraries']
results = generate_gap_analysis_report(neighborhoods, amenities)
```

---

## Function Signatures

### `calculate_nearest_amenity_distances(max_tracts=None)`
Calculates network distances from census tracts to all amenity types.
- **Returns:** GeoDataFrame with distance columns
- **Output:** `data/processed/tracts_with_distances.geojson`

### `calculate_nearest_amenity_distances_neighborhoods(max_neighborhoods=None)`
Calculates network distances from neighborhoods to all amenity types.
- **Returns:** GeoDataFrame with distance columns
- **Output:** `data/processed/neighborhoods_with_distances.geojson`

### `create_walkability_index()`
Creates composite walkability score (0-100) for census tracts.
- **Returns:** GeoDataFrame with walkability_index column
- **Output:** `data/processed/tracts_with_walkability.geojson`

### `create_walkability_index_neighborhoods()`
Creates composite walkability score (0-100) for neighborhoods.
- **Returns:** GeoDataFrame with walkability_index column
- **Output:** `data/processed/neighborhoods_with_walkability.geojson`

### `calculate_equity_scores(gdf, amenity_type)`
Calculates need, access, and gap scores.
- **Parameters:**
  - `gdf`: GeoDataFrame (neighborhoods or tracts)
  - `amenity_type`: 'parks', 'grocery_stores', 'hospitals', etc.
- **Returns:** GeoDataFrame with `{amenity}_gap_score` columns

### `identify_underserved_areas(gdf, amenity_type, top_n=10, min_population=1000)`
Identifies most underserved areas.
- **Returns:** DataFrame ranked by gap score

### `generate_gap_analysis_report(gdf, amenity_types, output_dir="outputs/gap_analysis")`
Runs complete gap analysis for multiple amenities.
- **Returns:** Dict with results for each amenity type
- **Output:** CSV files and text report

---

## Correct vs Incorrect Imports

### ❌ INCORRECT (will cause ImportError):
```python
from features.calculate_distances import calculate_all_distances  # Wrong!
```

### ✅ CORRECT:
```python
from features.calculate_distances import calculate_nearest_amenity_distances  # Right!
```

---

## File Outputs Reference

### Data Files
- `data/raw/la_neighborhoods.geojson` - Your 114 neighborhoods from shapefile
- `data/processed/census_tracts_with_demographics.geojson` - 2,478 tracts + demographics
- `data/processed/neighborhoods_with_demographics.geojson` - 114 neighborhoods + demographics
- `data/processed/tracts_with_walkability.geojson` - Census tracts + walkability scores
- `data/processed/neighborhoods_with_walkability.geojson` - Neighborhoods + walkability scores

### Map Files
- `outputs/walkability_map_combined.html` - Main walkability map (toggle layers)
- `outputs/gap_analysis/gap_map_*.html` - Individual amenity gap maps
- `outputs/gap_analysis/recommendations_combined_map.html` - All recommendations

### Report Files
- `outputs/gap_analysis/gap_analysis_report.txt` - Text summary
- `outputs/gap_analysis/all_recommended_locations.csv` - All proposals with lat/lon
- `outputs/gap_analysis/all_underserved_areas.csv` - All underserved rankings

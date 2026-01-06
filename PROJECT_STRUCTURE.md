# Urban Equity Analysis - Complete Project Structure

## Overview
Complete walkability and equity analysis for Los Angeles with 114 neighborhoods from your shapefile.

---

## 📁 File Structure (23 Python Files)

### Root Runner Scripts (5 files)
```
run_full_analysis.py              # ✨ Master pipeline (all phases)
run_data_collection.py            # Phase 1: Download data
run_preprocessing.py              # Phase 2: Clean & merge
run_visualization.py              # Phase 4: Create maps
run_amenity_gap_analysis.py       # Phase 5: Gap analysis
```

### Source Code Modules

#### `src/datacollection/` (5 files)
```
get_study_area.py                 # Downloads LA boundary from OSM
get_neighborhoods.py              # Loads YOUR shapefile (114 neighborhoods)
get_censusdata.py                 # Downloads census tracts + demographics
get_amenities.py                  # Downloads 8 amenity types from OSM
get_street_network.py             # Downloads walkable street network
```

#### `src/preprocessing/` (6 files)
```
clean_census_data.py              # Merges demographics (includes GEOID fix)
clean_amenities.py                # Deduplicates amenities
validate_network.py               # Validates street network connectivity
validate_data.py                  # General data validation
spatial_joins.py                  # Spatial overlay operations
aggregate_to_neighborhoods.py     # Census tracts → Neighborhoods
```

#### `src/features/` (5 files)
```
calculate_distances.py                         # Census tract distances
calculate_distances_neighborhoods.py           # Neighborhood distances
create_walkability_index.py                    # Census tract walkability (0-100)
create_walkability_index_neighborhoods.py      # Neighborhood walkability (0-100)
identify_amenity_gaps.py                       # ✨ Gap analysis logic
```

#### `src/visualization/` (2 files)
```
create_combined_map.py                         # Main map (both layers)
visualize_amenity_gaps.py                      # Gap analysis maps
```

---

## 📊 Data Files

### Input Data (`data/raw/`)
```
8494cd42-...-621do0.x5yiu.shp     # YOUR 114 neighborhoods shapefile
la_neighborhoods.geojson           # Standardized version
la_census_tracts.geojson           # 2,498 census tracts
la_demographics.csv                # Demographics from Census API
la_boundary.geojson                # LA city boundary
la_amenities_all.geojson           # All amenities from OSM
la_street_network.graphml          # Street network for routing
la_network_edges.geojson
la_network_nodes.geojson
```

### Processed Data (`data/processed/`)
```
neighborhoods_with_walkability.geojson     # 114 neighborhoods + scores (1.22 MB)
neighborhoods_with_demographics.geojson    # 114 neighborhoods + demographics (1.11 MB)
tracts_with_walkability.geojson            # 2,498 tracts + scores (19.66 MB)
census_tracts_with_demographics.geojson    # 2,478 tracts + demographics (17.27 MB)
amenities_cleaned.geojson                  # 14,209 amenities (3.46 MB)
```

---

## 📋 Column Reference

### 1. Neighborhoods with Walkability (114 rows × 47 columns)

**Geographic Info:**
- `neighborhood_id` - Unique ID (1-114)
- `neighborhood_name` - Name from your shapefile
- `geometry` - Polygon geometry
- `centroid_x`, `centroid_y` - Center coordinates

**Demographics:**
- `total_population`
- `median_household_income`
- `median_age`
- `population_density` (per acre)
- `area_acres`

**Race/Ethnicity:**
- `white_alone`, `black_alone`, `asian_alone`, `hispanic_latino`
- `pct_white`, `pct_black`, `pct_asian`, `pct_hispanic`

**Amenity Distances (meters):**
- `parks_distance_m`
- `grocery_stores_distance_m`
- `hospitals_distance_m`
- `transit_stops_distance_m`
- `schools_distance_m`
- `pharmacies_distance_m`
- `libraries_distance_m`
- `urgent_care_distance_m`

**Amenity Counts:**
- `parks_count_1km` (within 1km radius)
- `grocery_stores_count_1km`
- `hospitals_count_1km`
- ... (same for all 8 amenity types)

**Amenity Scores (0-100):**
- `parks_score`
- `grocery_stores_score`
- `hospitals_score`
- ... (same for all 8 amenity types)

**Walkability:**
- `walkability_index` (0-100 composite score)
- `walkability_category` (Excellent/Good/Moderate/Poor/Very Poor)

---

### 2. Census Tracts with Walkability (2,498 rows × 60 columns)

**Same as neighborhoods PLUS:**
- `GEOID` - 11-digit census tract ID
- `NAME`, `NAMELSAD` - Tract names
- `STATEFP`, `COUNTYFP`, `TRACTCE` - FIPS codes
- `ALAND`, `AWATER` - Land/water area
- `INTPTLAT`, `INTPTLON` - Internal point coordinates

---

### 3. Amenities Cleaned (14,209 rows × 5 columns)

**Columns:**
- `amenity_type` - One of 8 types
- `name` - Amenity name
- `geometry` - Point location
- `importance_weight` - Priority weight
- `size_category` - Small/Medium/Large

**Amenity Type Counts:**
```
transit_stops       9,121
parks               2,349
schools             1,206
grocery_stores        832
hospitals             260
pharmacies            171
urgent_care           160
libraries             110
TOTAL:             14,209
```

---

## 🗺️ Output Files

### Walkability Maps (`outputs/`)
```
walkability_map_combined.html                  # Main map (31.41 MB)
  - Toggle between census tracts and neighborhoods
  - Color-coded walkability scores
  - Interactive tooltips
```

### Gap Analysis (`outputs/gap_analysis/`)

**Reports:**
```
gap_analysis_report.txt                        # Summary statistics
all_underserved_areas.csv                      # All rankings
all_recommended_locations.csv                  # All proposals (lat/lon)
```

**Per-Amenity CSVs:**
```
underserved_areas_parks.csv
recommended_locations_parks.csv
underserved_areas_grocery_stores.csv
recommended_locations_grocery_stores.csv
underserved_areas_hospitals.csv
recommended_locations_hospitals.csv
underserved_areas_transit_stops.csv
recommended_locations_transit_stops.csv
```

**Interactive Maps:**
```
gap_map_parks.html                             # Parks gap map (2.18 MB)
gap_map_grocery_stores.html                    # Grocery gap map (2.21 MB)
gap_map_hospitals.html                         # Hospital gap map (2.24 MB)
gap_map_transit_stops.html                     # Transit gap map (2.28 MB)
recommendations_combined_map.html              # All recommendations (1.13 MB)
```

**Static Charts:**
```
gap_analysis_dashboard.png                     # 4-panel analysis
```

---

## 🔧 Function Reference

### Data Collection
```python
from datacollection.get_study_area import get_los_angeles_boundary
from datacollection.get_neighborhoods import get_los_angeles_neighborhoods
from datacollection.get_censusdata import get_census_tracts_la, get_census_demographics
from datacollection.get_amenities import collect_all_amenities
from datacollection.get_street_network import get_street_network_la
```

### Preprocessing
```python
from preprocessing.clean_census_data import clean_and_merge_census
from preprocessing.clean_amenities import clean_amenities
from preprocessing.validate_network import validate_street_network
from preprocessing.aggregate_to_neighborhoods import aggregate_demographics_to_neighborhoods
```

### Feature Engineering
```python
# Distance calculations
from features.calculate_distances import calculate_nearest_amenity_distances
from features.calculate_distances_neighborhoods import calculate_nearest_amenity_distances_neighborhoods

# Walkability index
from features.create_walkability_index import create_walkability_index
from features.create_walkability_index_neighborhoods import create_walkability_index_neighborhoods

# Gap analysis
from features.identify_amenity_gaps import (
    calculate_equity_scores,
    identify_underserved_areas,
    find_optimal_locations,
    generate_gap_analysis_report
)
```

### Visualization
```python
from visualization.create_combined_map import create_combined_interactive_map
from visualization.visualize_amenity_gaps import (
    create_gap_analysis_map,
    create_equity_dashboard,
    create_interactive_recommendations_map
)
```

---

## 📈 Data Flow

```
YOUR SHAPEFILE (114 neighborhoods)
    ↓
get_neighborhoods.py
    ↓
la_neighborhoods.geojson (standardized)
    ↓
aggregate_to_neighborhoods.py (adds census demographics)
    ↓
neighborhoods_with_demographics.geojson
    ↓
calculate_nearest_amenity_distances_neighborhoods()
    ↓
neighborhoods_with_distances.geojson
    ↓
create_walkability_index_neighborhoods()
    ↓
neighborhoods_with_walkability.geojson
    ↓
    ├─→ create_combined_map() → walkability_map_combined.html
    └─→ generate_gap_analysis_report() → gap_analysis/
```

---

## 🎯 Quick Commands

### Run Everything
```bash
python run_full_analysis.py
```

### Individual Phases
```bash
python run_data_collection.py        # Downloads all data
python run_preprocessing.py          # Cleans and merges
python run_visualization.py          # Creates walkability map
python run_amenity_gap_analysis.py   # Creates gap analysis
```

### Check Structure
```bash
python show_structure.py             # Shows this structure + column names
```

---

## 📝 Key Features

✅ **Uses YOUR 114 neighborhoods** from shapefile
✅ **Automatic GEOID fix** built into preprocessing
✅ **Network-based distances** (actual walking routes)
✅ **Equity-focused gap analysis** (prioritizes low-income areas)
✅ **Interactive maps** with layer toggle
✅ **Complete documentation** (this file + PIPELINE_GUIDE.md)

---

## 🔍 Important Notes

1. **GEOID Fix**: Automatically handled in `clean_census_data.py:29-30`
2. **Neighborhood Count**: 114 from your shapefile (not 55)
3. **Distance Method**: Network routing (OSMnx), not straight-line
4. **Gap Score Formula**: `need_score × (1 - access_score)`
5. **Walkability Weights**:
   - Grocery stores: 25%
   - Parks: 20%
   - Transit: 15%
   - Hospitals: 10%
   - Schools: 10%
   - Pharmacies: 10%
   - Libraries: 5%
   - Urgent care: 5%

---

## 📚 Documentation Files

- `PROJECT_STRUCTURE.md` (this file) - Complete structure reference
- `PIPELINE_GUIDE.md` - How to use the pipeline
- `FUNCTION_REFERENCE.md` - Function names and imports
- `show_structure.py` - Script to display structure

---

**Total Files:** 23 Python scripts + 3 documentation files + your data

**Last Updated:** After codebase cleanup

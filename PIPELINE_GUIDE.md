# Urban Equity Analysis - Pipeline Guide

## Overview
This project analyzes walkability and amenity access across Los Angeles neighborhoods, with a focus on equity and identifying underserved communities.

## Quick Start

### Option 1: Run Full Pipeline (Interactive)
```bash
python run_full_analysis.py
```
This master script will prompt you to run each phase step-by-step.

### Option 2: Run Individual Stages

#### Phase 1: Data Collection
```bash
python run_data_collection.py
```
**Prerequisites:** Census API key in `.env` file

**What it does:**
- Downloads LA boundary from OpenStreetMap
- Loads your 114 neighborhoods from shapefile
- Gets census tracts and demographics
- Collects amenities (parks, stores, hospitals, etc.)
- Downloads walkable street network

**Output:** `data/raw/`

---

#### Phase 2: Data Preprocessing
```bash
python run_preprocessing.py
```

**What it does:**
- Merges census demographics with tract geometries (includes GEOID fix)
- Cleans and deduplicates amenities
- Validates street network connectivity
- Aggregates demographics to neighborhoods via spatial overlay

**Output:** `data/processed/`

---

#### Phase 3 & 4: Walkability Analysis
This is integrated into the preprocessing/feature engineering workflow.

**Automatically runs:**
- Distance calculations (network-based walking distances)
- Walkability index creation (0-100 score)
- For both census tracts and neighborhoods

---

#### Phase 4: Visualization
```bash
python run_visualization.py
```

**What it does:**
- Creates interactive map with census tract AND neighborhood layers
- Toggle between detailed (2,478 tracts) and aggregated (114 neighborhoods) views
- Color-coded by walkability score
- Hover tooltips with full details

**Output:** `outputs/walkability_map_combined.html`

---

#### Phase 5: Gap Analysis
```bash
python run_amenity_gap_analysis.py
```

**What it does:**
- Calculates equity gap scores (need × poor access)
- Identifies top 10 underserved areas per amenity
- Recommends optimal locations for new facilities
- Prioritizes lower-income communities

**Analyzes:**
- Parks
- Grocery stores
- Hospitals
- Transit stops

**Output:** `outputs/gap_analysis/`
- `gap_analysis_report.txt` - Summary
- `all_recommended_locations.csv` - All proposals with lat/lon
- Individual amenity maps and CSVs
- `recommendations_combined_map.html` - Interactive map

---

## Project Structure

```
Urban-Equity-Analysis/
├── run_full_analysis.py          # Master pipeline (NEW)
├── run_data_collection.py        # Phase 1
├── run_preprocessing.py          # Phase 2
├── run_visualization.py          # Phase 4 (updated)
├── run_amenity_gap_analysis.py   # Phase 5
│
├── src/
│   ├── datacollection/
│   │   ├── get_study_area.py
│   │   ├── get_neighborhoods.py      # Loads YOUR shapefile
│   │   ├── get_censusdata.py
│   │   ├── get_amenities.py
│   │   └── get_street_network.py
│   │
│   ├── preprocessing/
│   │   ├── clean_census_data.py      # Includes GEOID fix
│   │   ├── clean_amenities.py
│   │   ├── validate_network.py
│   │   ├── validate_data.py
│   │   ├── spatial_joins.py
│   │   └── aggregate_to_neighborhoods.py
│   │
│   ├── features/
│   │   ├── calculate_distances.py
│   │   ├── calculate_distances_neighborhoods.py
│   │   ├── create_walkability_index.py
│   │   ├── create_walkability_index_neighborhoods.py
│   │   └── identify_amenity_gaps.py   # Gap analysis logic
│   │
│   └── visualization/
│       ├── create_combined_map.py     # Main walkability map
│       └── visualize_amenity_gaps.py  # Gap analysis maps
│
├── data/
│   ├── raw/                          # Downloaded/input data
│   │   ├── 8494cd42...shp           # Your neighborhood shapefile
│   │   ├── la_neighborhoods.geojson  # Standardized version
│   │   ├── la_demographics.csv
│   │   └── ...
│   │
│   └── processed/                    # Cleaned data
│       ├── neighborhoods_with_walkability.geojson
│       ├── tracts_with_walkability.geojson
│       └── ...
│
└── outputs/
    ├── walkability_map_combined.html
    └── gap_analysis/
        ├── gap_analysis_report.txt
        ├── recommendations_combined_map.html
        └── ...
```

---

## What Was Cleaned Up

### Deleted Files (Redundant)
1. ✅ `src/features/fix_demographics.py` - Fix now integrated into `clean_census_data.py`
2. ✅ `src/visualization/create_walkability_map.py` - Replaced by combined map
3. ✅ `src/visualization/create_walkability_map_neighborhoods.py` - Replaced by combined map

### Key Improvements
- **Demographics fix integrated:** GEOID padding (`.str.zfill(11)`) now happens automatically in `clean_census_data.py:29-30`
- **Single visualization:** `create_combined_map.py` has both census tract and neighborhood layers with toggle
- **Master pipeline:** `run_full_analysis.py` orchestrates entire workflow

---

## Common Workflows

### First Time Setup
```bash
# 1. Create .env file with Census API key
echo "CENSUS_API_KEY=your_key_here" > .env

# 2. Run full pipeline
python run_full_analysis.py
```

### Update Analysis (Data Already Collected)
```bash
# Skip data collection, just reprocess and analyze
python run_full_analysis.py
# Answer 'n' to Phase 1, 'y' to everything else
```

### Just Regenerate Maps
```bash
python run_visualization.py
```

### Just Run Gap Analysis
```bash
python run_amenity_gap_analysis.py
```

---

## Key Features

### 1. Uses Your Shapefile
The 114 neighborhoods come from your shapefile:
`E:\Work\Projects\Urban-Equity-Analysis\data\raw\8494cd42...-621do0.x5yiu.shp`

Loaded in: `src/datacollection/get_neighborhoods.py:12`

### 2. Automatic Data Fixes
- GEOID padding for census data merge
- Amenity deduplication
- Network connectivity validation
- Spatial overlay with area weighting

### 3. Network-Based Distances
All distances use actual walking routes via street network (OSMnx), not straight-line.

### 4. Equity Focus
Gap analysis prioritizes:
- Lower-income communities (70% weight)
- Higher population density (30% weight)
- Poor access to amenities

---

## Outputs Explained

### Walkability Map
- **File:** `outputs/walkability_map_combined.html`
- **Layers:** Toggle between census tracts and neighborhoods
- **Colors:** Red (poor) → Yellow → Green (excellent)
- **Scores:** 0-100 composite of 8 amenity types

### Gap Analysis Report
- **File:** `outputs/gap_analysis/gap_analysis_report.txt`
- **Shows:** Top 10 underserved areas per amenity
- **Metrics:** Gap score, population, income, distance

### Recommendations
- **File:** `outputs/gap_analysis/all_recommended_locations.csv`
- **Contains:** Lat/lon coordinates for proposed new facilities
- **Format:** Ready for GIS import or stakeholder review

---

## Troubleshooting

### "GEOID mismatch" error
✅ **Fixed!** Now handled automatically in `clean_census_data.py`

### Missing census data
Run: `python run_data_collection.py`
Ensure Census API key is in `.env`

### Map layers not showing
Check that both files exist:
- `data/processed/tracts_with_walkability.geojson`
- `data/processed/neighborhoods_with_walkability.geojson`

---

## Next Steps

1. **Review results:**
   - Open `outputs/walkability_map_combined.html`
   - Read `outputs/gap_analysis/gap_analysis_report.txt`

2. **Refine analysis:**
   - Adjust gap score weights in `src/features/identify_amenity_gaps.py`
   - Add more amenity types
   - Use census tract level for finer detail

3. **Share findings:**
   - Export CSVs to stakeholders
   - Present interactive maps in meetings
   - Use recommendations for urban planning decisions

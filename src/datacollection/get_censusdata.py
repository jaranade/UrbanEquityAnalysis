# src/datacollection/get_census_data.py

import geopandas as gpd
import requests
import pandas as pd
from pathlib import Path

def get_census_tracts_la():
    """
    Download census tracts for LA County
    Using Census Bureau TIGER/Line Shapefiles
    """
    
    # Census TIGER/Line API for LA County (FIPS: 06037)
    url = "https://www2.census.gov/geo/tiger/TIGER2022/TRACT/tl_2022_06_tract.zip"
    
    # Download and read
    gdf = gpd.read_file(url)
    
    # Filter to LA County only (COUNTYFP == '037')
    la_tracts = gdf[gdf['COUNTYFP'] == '037'].copy()
    
    # Convert to appropriate CRS (NAD83 / California zone 5)
    la_tracts = la_tracts.to_crs("EPSG:2229")  # CA State Plane (feet)
    
    # Save
    output_path = Path("data/raw/la_census_tracts.geojson")
    la_tracts.to_file(output_path, driver='GeoJSON')
    
    print(f"✓ Census tracts saved: {len(la_tracts)} tracts")
    
    return la_tracts


def get_census_demographics(census_api_key):
    """
    Get demographic data from Census API
    Variables: Population, Race, Income, Age
    """
    
    # Use 2021 ACS 5-year estimates (more stable than 2022)
    base_url = "https://api.census.gov/data/2021/acs/acs5"
    
    # Variables to fetch
    variables = {
        'B01003_001E': 'total_population',
        'B19013_001E': 'median_household_income',
        'B01002_001E': 'median_age',
        'B02001_002E': 'white_alone',
        'B02001_003E': 'black_alone',
        'B02001_005E': 'asian_alone',
        'B03003_003E': 'hispanic_latino',
    }
    
    var_string = ','.join(variables.keys())
    
    # LA County FIPS: 06037, all tracts (*)
    params = {
        'get': var_string,
        'for': 'tract:*',
        'in': 'state:06 county:037',
        'key': census_api_key
    }
    
    print(f"Requesting Census data...")
    print(f"URL: {base_url}")
    
    response = requests.get(base_url, params=params)
    
    # Check response status
    print(f"Response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error response: {response.text}")
        raise Exception(f"Census API request failed with status {response.status_code}")
    
    # Try to parse JSON
    try:
        data = response.json()
    except Exception as e:
        print(f"Failed to parse JSON response")
        print(f"Response text: {response.text[:500]}")  # Print first 500 chars
        raise e
    
    # Check if we got an error message from the API
    if isinstance(data, dict) and 'error' in data:
        print(f"Census API error: {data}")
        raise Exception(f"Census API returned error: {data}")
    
    # Convert to DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])
    
    # Rename columns
    for old, new in variables.items():
        if old in df.columns:
            df.rename(columns={old: new}, inplace=True)
    
    # Create GEOID for joining
    df['GEOID'] = df['state'] + df['county'] + df['tract']
    
    # Convert to numeric
    for col in variables.values():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Save
    output_path = Path("data/raw/la_demographics.csv")
    df.to_csv(output_path, index=False)
    
    print(f"✓ Demographics saved: {len(df)} tracts")
    print(f"  Sample data:")
    print(df[['GEOID', 'total_population', 'median_household_income']].head())
    
    return df


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    
    # Get Census API key
    load_dotenv()
    API_KEY = os.getenv('CENSUS_API_KEY')
    
    if not API_KEY:
        print("ERROR: CENSUS_API_KEY not found in .env file")
    else:
        tracts = get_census_tracts_la()
        demographics = get_census_demographics(API_KEY)
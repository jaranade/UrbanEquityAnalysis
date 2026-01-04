# src/data_collection/get_street_network.py

import osmnx as ox
import networkx as nx
from pathlib import Path

def get_street_network_la():
    """
    Download walkable street network for LA
    """
    
    place_name = "Los Angeles, California, USA"
    
    # Download street network (walk mode only)
    print("Downloading street network (this may take several minutes)...")
    G = ox.graph_from_place(
        place_name, 
        network_type='walk',  # Only walkable streets
        simplify=True
    )
    
    print(f"✓ Network downloaded: {len(G.nodes)} nodes, {len(G.edges)} edges")
    
    # Save as GraphML (preserves graph structure)
    output_path = Path("data/raw/la_street_network.graphml")
    ox.save_graphml(G, output_path)
    
    # Also save as GeoDataFrames for visualization
    nodes, edges = ox.graph_to_gdfs(G)
    nodes.to_file("data/raw/la_network_nodes.geojson", driver='GeoJSON')
    edges.to_file("data/raw/la_network_edges.geojson", driver='GeoJSON')
    
    return G


if __name__ == "__main__":
    network = get_street_network_la()
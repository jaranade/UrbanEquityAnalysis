# src/preprocessing/validate_network.py

import osmnx as ox
import networkx as nx
from pathlib import Path

def validate_street_network():
    """
    Load and validate street network
    Check connectivity, identify issues
    """
    
    print("Loading street network...")
    G = ox.load_graphml("data/raw/la_street_network.graphml")
    
    print(f"  Nodes: {len(G.nodes):,}")
    print(f"  Edges: {len(G.edges):,}")
    
    # Check if graph is connected
    print("\nChecking connectivity...")
    
    if nx.is_strongly_connected(G):
        print("  ✓ Graph is strongly connected")
    else:
        # Find largest strongly connected component
        largest_cc = max(nx.strongly_connected_components(G), key=len)
        print(f"  ⚠ Graph is NOT strongly connected")
        print(f"  Largest component: {len(largest_cc):,} nodes ({len(largest_cc)/len(G.nodes)*100:.1f}%)")
        
        # Extract largest component for routing
        G_connected = G.subgraph(largest_cc).copy()
        
        # Save connected component
        output_path = Path("data/processed/la_street_network_connected.graphml")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ox.save_graphml(G_connected, output_path)
        
        print(f"  ✓ Saved connected component to {output_path}")
        G = G_connected
    
    # Check for isolated nodes
    isolates = list(nx.isolates(G))
    print(f"\nIsolated nodes: {len(isolates)}")
    
    # Calculate basic network statistics
    print("\n" + "="*50)
    print("NETWORK STATISTICS")
    print("="*50)
    
    # Average node degree
    degrees = dict(G.degree())
    avg_degree = sum(degrees.values()) / len(degrees)
    print(f"Average node degree: {avg_degree:.2f}")
    
    # Edge lengths
    edge_lengths = [data.get('length', 0) for u, v, data in G.edges(data=True)]
    avg_length = sum(edge_lengths) / len(edge_lengths)
    print(f"Average edge length: {avg_length:.2f} meters")
    
    return G


if __name__ == "__main__":
    network = validate_street_network()
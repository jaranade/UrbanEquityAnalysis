import torch
import networkx as nx
import geopandas as gpd
import pandas as pd
import numpy as np
from torch_geometric.data import Data
from sklearn.preprocessing import StandardScaler
import pickle
import os

class GNNDataPreparation:
    """
    Converts LA census tracts into PyTorch Geometric graph format
    """
    
    def __init__(self, 
                 network_path='data/raw/la_street_network.graphml',
                 tracts_path='data/processed/tracts_with_walkability.geojson',
                 amenities_path='data/processed/amenities_cleaned.geojson'):
        
        self.network_path = network_path
        self.tracts_path = tracts_path
        self.amenities_path = amenities_path
        
        # Load data
        print("📂 Loading data...")
        self.G = nx.read_graphml(network_path)
        self.tracts = gpd.read_file(tracts_path)
        self.amenities = gpd.read_file(amenities_path)
        
        print(f"✅ Street network: {len(self.G.nodes):,} nodes, {len(self.G.edges):,} edges")
        print(f"✅ Census tracts: {len(self.tracts):,}")
        print(f"✅ Amenities: {len(self.amenities):,}")
    
    def create_tract_level_graph(self):
        """
        Create graph where nodes = census tracts, edges = spatial neighbors
        """
        print("\n" + "="*60)
        print("🔧 CREATING TRACT-LEVEL GRAPH")
        print("="*60)
        
        # 1. Node features
        node_features = self._create_node_features()
        
        # 2. Edges (spatial adjacency)
        edge_index, edge_weights = self._create_edges()
        
        # 3. Labels (walkability scores)
        labels = self._create_labels()
        
        # 4. Create PyTorch Geometric Data object
        data = Data(
            x=node_features,
            edge_index=edge_index,
            edge_attr=edge_weights,
            y=labels,
            num_nodes=len(self.tracts)
        )
        
        print("\n" + "="*60)
        print("✅ GRAPH CREATED SUCCESSFULLY")
        print("="*60)
        print(f"   📊 Nodes: {data.num_nodes:,}")
        print(f"   🔗 Edges: {data.num_edges:,}")
        print(f"   📈 Features per node: {data.x.shape[1]}")
        print(f"   🎯 Average degree: {data.num_edges / data.num_nodes:.1f}")
        print("="*60)
        
        return data
    
    def _create_node_features(self):
        """
        Create feature vector for each census tract
        """
        print("\n🔧 Step 1/3: Creating node features...")
        
        # Feature columns matching YOUR data
        feature_columns = [
            # Demographics (7 features)
            'total_population',
            'median_household_income',
            'median_age_y',
            'pct_white',
            'pct_black',
            'pct_asian',
            'pct_hispanic',

            # Amenity distances (8 features)
            'parks_distance_m',
            'hospitals_distance_m',
            'grocery_stores_distance_m',
            'schools_distance_m',
            'libraries_distance_m',
            'pharmacies_distance_m',
            'urgent_care_distance_m',
            'transit_stops_distance_m',

            # Amenity counts (8 features)
            'parks_count_1km',
            'grocery_stores_count_1km',
            'hospitals_count_1km',
            'schools_count_1km',
            'libraries_count_1km',
            'pharmacies_count_1km',
            'urgent_care_count_1km',
            'transit_stops_count_1km'
        ]
        
        # Extract features
        features_df = self.tracts[feature_columns].copy()
        
        print(f"   ✅ Extracted {len(feature_columns)} base features")
        
        # Handle missing values
        missing_count = features_df.isnull().sum().sum()
        if missing_count > 0:
            print(f"   ⚠️  Found {missing_count} missing values, filling with median...")
            features_df = features_df.fillna(features_df.median())
        
        # Add spatial coordinates
        centroids = self.tracts.geometry.centroid
        features_df['centroid_x'] = centroids.x.values
        features_df['centroid_y'] = centroids.y.values
        
        print(f"   ✅ Added spatial coordinates (2 features)")
        
        # Normalize features
        print(f"   🔄 Normalizing features...")
        scaler = StandardScaler()
        features_normalized = scaler.fit_transform(features_df)
        
        # Save scaler
        self.feature_scaler = scaler
        self.feature_columns = list(features_df.columns)
        
        # Convert to PyTorch tensor
        node_features = torch.FloatTensor(features_normalized)
        
        print(f"   ✅ Final feature tensor: {node_features.shape}")
        print(f"      ({node_features.shape[0]:,} nodes × {node_features.shape[1]} features)")
        
        return node_features
    
    def _create_edges(self):
        """
        Create edges between spatially adjacent census tracts
        """
        print("\n🔧 Step 2/3: Creating edges (spatial adjacency)...")
        
        try:
            from libpysal.weights import Queen
            
            print("   🔄 Computing Queen contiguity weights...")
            w = Queen.from_dataframe(self.tracts)
            
            edge_list = []
            edge_weights = []
            
            for i, neighbors in w.neighbors.items():
                for j in neighbors:
                    edge_list.append([i, j])
                    
                    dist = self.tracts.iloc[i].geometry.centroid.distance(
                        self.tracts.iloc[j].geometry.centroid
                    )
                    edge_weights.append([1.0 / (dist + 1e-6)])
            
            print(f"   ✅ Used libpysal Queen contiguity")
            
        except ImportError:
            print("   ⚠️  libpysal not available, using GeoPandas fallback...")
            
            edge_list = []
            edge_weights = []
            
            for i, tract_i in self.tracts.iterrows():
                neighbors = self.tracts[self.tracts.geometry.touches(tract_i.geometry)]
                
                for j, tract_j in neighbors.iterrows():
                    if i < j:
                        edge_list.append([i, j])
                        edge_list.append([j, i])
                        
                        dist = tract_i.geometry.centroid.distance(tract_j.geometry.centroid)
                        weight = 1.0 / (dist + 1e-6)
                        edge_weights.append([weight])
                        edge_weights.append([weight])
            
            print(f"   ✅ Used GeoPandas spatial joins")
        
        # Convert to tensors
        edge_index = torch.LongTensor(edge_list).t().contiguous()
        edge_attr = torch.FloatTensor(edge_weights)
        
        print(f"   ✅ Edge tensor: {edge_index.shape}")
        print(f"      ({edge_index.shape[1]:,} edges)")
        
        return edge_index, edge_attr
    
    def _create_labels(self):
        """
        Extract walkability scores as prediction targets
        """
        print("\n🔧 Step 3/3: Creating labels (walkability scores)...")
        
        labels = self.tracts['walkability_index'].values / 100.0
        labels = torch.FloatTensor(labels).unsqueeze(1)
        
        print(f"   ✅ Labels shape: {labels.shape}")
        print(f"   📊 Range: [{labels.min():.3f}, {labels.max():.3f}]")
        print(f"   📊 Mean: {labels.mean():.3f}, Std: {labels.std():.3f}")
        
        return labels
    
    def spatial_train_test_split(self, data, test_size=0.2, val_size=0.1):
        """
        Spatial split to avoid data leakage
        """
        print("\n" + "="*60)
        print("🔧 CREATING SPATIAL TRAIN/VAL/TEST SPLIT")
        print("="*60)
        
        centroids = self.tracts.geometry.centroid
        lons = centroids.x.values
        lats = centroids.y.values
        
        print("   🔄 Dividing LA into 5×5 spatial blocks...")
        lon_blocks = pd.cut(lons, bins=5, labels=False)
        lat_blocks = pd.cut(lats, bins=5, labels=False)
        spatial_blocks = lon_blocks * 5 + lat_blocks
        
        unique_blocks = np.unique(spatial_blocks)
        np.random.seed(42)
        np.random.shuffle(unique_blocks)
        
        n_test = int(len(unique_blocks) * test_size)
        n_val = int(len(unique_blocks) * val_size)
        
        test_blocks = unique_blocks[:n_test]
        val_blocks = unique_blocks[n_test:n_test + n_val]
        train_blocks = unique_blocks[n_test + n_val:]
        
        train_mask = torch.BoolTensor([block in train_blocks for block in spatial_blocks])
        val_mask = torch.BoolTensor([block in val_blocks for block in spatial_blocks])
        test_mask = torch.BoolTensor([block in test_blocks for block in spatial_blocks])
        
        data.train_mask = train_mask
        data.val_mask = val_mask
        data.test_mask = test_mask
        
        print(f"\n   ✅ Train: {train_mask.sum():,} tracts ({train_mask.sum()/len(train_mask)*100:.1f}%)")
        print(f"   ✅ Val:   {val_mask.sum():,} tracts ({val_mask.sum()/len(val_mask)*100:.1f}%)")
        print(f"   ✅ Test:  {test_mask.sum():,} tracts ({test_mask.sum()/len(test_mask)*100:.1f}%)")
        print("="*60)
        
        return data
    
    def save_processed_data(self, data, output_path='data/processed/gnn_data.pt'):
        """Save processed graph data"""
        print("\n" + "="*60)
        print("💾 SAVING PROCESSED DATA")
        print("="*60)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        torch.save(data, output_path)
        print(f"   ✅ Saved graph: {output_path}")
        
        metadata = {
            'feature_scaler': self.feature_scaler,
            'feature_columns': self.feature_columns,
            'num_nodes': data.num_nodes,
            'num_edges': data.num_edges,
            'num_features': data.x.shape[1],
            'train_size': data.train_mask.sum().item(),
            'val_size': data.val_mask.sum().item(),
            'test_size': data.test_mask.sum().item()
        }
        
        metadata_path = output_path.replace('.pt', '_metadata.pkl')
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"   ✅ Saved metadata: {metadata_path}")
        
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(f"   Total nodes: {data.num_nodes:,}")
        print(f"   Total edges: {data.num_edges:,}")
        print(f"   Features per node: {data.x.shape[1]}")
        print(f"   Train/Val/Test: {data.train_mask.sum()}/{data.val_mask.sum()}/{data.test_mask.sum()}")
        print("="*60)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 GNN DATA PREPARATION FOR LA WALKABILITY")
    print("="*60)
    
    prep = GNNDataPreparation()
    data = prep.create_tract_level_graph()
    data = prep.spatial_train_test_split(data)
    prep.save_processed_data(data)
    
    print("\n" + "="*60)
    print("✅ GNN DATA PREPARATION COMPLETE!")
    print("="*60)
    print("\nNext step: Build the GNN model")
    print("="*60 + "\n")
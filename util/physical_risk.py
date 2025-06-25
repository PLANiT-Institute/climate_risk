import pandas as pd
import numpy as np
import os

# Optional imports for advanced functionality
try:
    import geopandas as gpd
    from shapely.geometry import Point
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False
    
try:
    import rasterio
    from rasterio.sample import sample_gen
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

class PhysicalRisk:
    """
    Simple Physical Risk assessment using rasterio and geopandas.
    Works with hazard raster data (GeoTIFF, NetCDF, etc.)
    """
    
    def __init__(self, facilities_df, hazard_file_path=None):
        self.facilities_df = facilities_df
        self.hazard_file_path = hazard_file_path
        
        # Default damage functions by hazard type
        self.damage_functions = {
            'flood': {
                'low': 0.05,     # 5% damage for low hazard
                'medium': 0.15,  # 15% damage for medium hazard
                'high': 0.35,    # 35% damage for high hazard
                'very_high': 0.60  # 60% damage for very high hazard
            },
            'wildfire': {
                'low': 0.03,
                'medium': 0.10,
                'high': 0.30,
                'very_high': 0.70
            },
            'drought': {
                'low': 0.02,
                'medium': 0.08,
                'high': 0.20,
                'very_high': 0.40
            }
        }

    def _create_facilities_gdf(self):
        """Convert facilities DataFrame to GeoDataFrame."""
        if not HAS_GEOPANDAS:
            print("Warning: geopandas not available, using basic coordinate handling")
            return self.facilities_df
            
        geometry = [Point(xy) for xy in zip(self.facilities_df['longitude'], 
                                          self.facilities_df['latitude'])]
        gdf = gpd.GeoDataFrame(self.facilities_df, geometry=geometry, crs='EPSG:4326')
        return gdf

    def _sample_hazard_from_raster(self, hazard_path, facilities_data):
        """Sample hazard values from raster at facility locations."""
        if not HAS_RASTERIO:
            print("Warning: rasterio not available, cannot read raster files")
            n_facilities = len(self.facilities_df)
            return [0.1] * n_facilities
            
        try:
            with rasterio.open(hazard_path) as src:
                if HAS_GEOPANDAS and hasattr(facilities_data, 'crs'):
                    # Transform coordinates to raster CRS if needed
                    if facilities_data.crs != src.crs:
                        facilities_proj = facilities_data.to_crs(src.crs)
                    else:
                        facilities_proj = facilities_data
                    
                    # Extract coordinates
                    coords = [(geom.x, geom.y) for geom in facilities_proj.geometry]
                else:
                    # Use basic coordinate extraction
                    coords = [(lon, lat) for lon, lat in zip(
                        self.facilities_df['longitude'], 
                        self.facilities_df['latitude']
                    )]
                
                # Sample raster values
                hazard_values = list(sample_gen(src, coords))
                hazard_values = [val[0] if val and not np.isnan(val[0]) else 0 
                               for val in hazard_values]
                
                return hazard_values
                
        except Exception as e:
            print(f"Warning: Could not read hazard file {hazard_path}: {e}")
            # Return default low risk values
            n_facilities = len(self.facilities_df)
            return [0.1] * n_facilities

    def _classify_hazard_level(self, hazard_values):
        """Classify continuous hazard values into risk categories."""
        hazard_array = np.array(hazard_values)
        
        # Define thresholds (adjust based on your data)
        thresholds = np.percentile(hazard_array[hazard_array > 0], [25, 50, 75])
        
        if len(thresholds) < 3:
            # If not enough non-zero values, use simple classification
            thresholds = [0.1, 0.3, 0.6]
        
        categories = []
        for val in hazard_values:
            if val <= thresholds[0]:
                categories.append('low')
            elif val <= thresholds[1]:
                categories.append('medium')
            elif val <= thresholds[2]:
                categories.append('high')
            else:
                categories.append('very_high')
                
        return categories

    def _calculate_annual_loss(self, asset_value, hazard_category, hazard_type='flood'):
        """Calculate expected annual loss based on asset value and hazard level."""
        damage_rate = self.damage_functions[hazard_type].get(hazard_category, 0.1)
        
        # Assume annual probability based on hazard category
        annual_probabilities = {
            'low': 0.01,      # 1% annual chance
            'medium': 0.02,   # 2% annual chance  
            'high': 0.05,     # 5% annual chance
            'very_high': 0.10 # 10% annual chance
        }
        
        annual_prob = annual_probabilities.get(hazard_category, 0.01)
        expected_annual_loss = asset_value * damage_rate * annual_prob
        
        return expected_annual_loss

    def _generate_synthetic_hazard_data(self, facilities_data):
        """Generate synthetic hazard data when no raster file is available."""
        np.random.seed(42)  # For reproducible results
        
        # Generate hazard values based on geographic clustering
        # (facilities close together have similar risk)
        n_facilities = len(self.facilities_df)
        
        # Create some spatial correlation
        base_risk = np.random.beta(2, 8, n_facilities)  # Skewed toward low risk
        
        # Add some geographic variation (simplified)
        if HAS_GEOPANDAS and hasattr(facilities_data, 'geometry'):
            lats = facilities_data.geometry.y.values
            lons = facilities_data.geometry.x.values
        else:
            lats = self.facilities_df['latitude'].values
            lons = self.facilities_df['longitude'].values
        
        # Normalize coordinates
        lat_norm = (lats - lats.min()) / (lats.max() - lats.min()) if lats.max() != lats.min() else np.zeros_like(lats)
        lon_norm = (lons - lons.min()) / (lons.max() - lons.min()) if lons.max() != lons.min() else np.zeros_like(lons)
        
        # Add geographic bias (e.g., coastal areas have higher flood risk)
        geographic_factor = 0.3 * lat_norm + 0.2 * lon_norm
        
        synthetic_hazard = base_risk + 0.3 * geographic_factor
        synthetic_hazard = np.clip(synthetic_hazard, 0, 1)
        
        return synthetic_hazard.tolist()

    def run(self):
        """
        Run physical risk analysis.
        
        Returns:
            DataFrame: Results with facility_id and annual_flood_loss
        """
        # Create GeoDataFrame from facilities (or use DataFrame if geopandas not available)
        facilities_data = self._create_facilities_gdf()
        
        # Get hazard values
        if self.hazard_file_path and os.path.exists(self.hazard_file_path):
            print(f"Using hazard data from: {self.hazard_file_path}")
            hazard_values = self._sample_hazard_from_raster(self.hazard_file_path, facilities_data)
        else:
            print("No hazard file provided or file not found. Using synthetic hazard data.")
            hazard_values = self._generate_synthetic_hazard_data(facilities_data)
        
        # Classify hazard levels
        hazard_categories = self._classify_hazard_level(hazard_values)
        
        # Calculate annual losses
        results = []
        for idx, row in self.facilities_df.iterrows():
            facility_id = row['facility_id']
            asset_value = row.get('asset_value', 1000000)  # Default 1M if not provided
            hazard_cat = hazard_categories[idx]
            
            annual_loss = self._calculate_annual_loss(asset_value, hazard_cat)
            
            results.append({
                'facility_id': facility_id,
                'hazard_value': hazard_values[idx],
                'hazard_category': hazard_cat,
                'annual_flood_loss': annual_loss
            })
        
        results_df = pd.DataFrame(results)
        
        print(f"Physical risk analysis completed for {len(results_df)} facilities")
        print(f"Total annual expected loss: ${results_df['annual_flood_loss'].sum():,.2f}")
        
        return results_df[['facility_id', 'annual_flood_loss']]  # Return same format as original
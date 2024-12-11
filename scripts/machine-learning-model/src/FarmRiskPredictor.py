import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from typing import List, Dict, Union
import difflib
import os

class FarmRiskPredictor:
    def __init__(self, dataset_path='../datasets/farm_data.csv'):
        # Load dataset
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset at {dataset_path} not found.")
        
        self.dataset = pd.read_csv(dataset_path)
        
        
        # Crop database for similarity matching
        self.crop_database = self._build_crop_database()
        
        self.risk_categories = ['Low', 'Moderate', 'High', 'Critical']
        
        # Setup preprocessing and model training
        self.setup_preprocessing()
        self.train_base_model()

    def _build_crop_database(self):
        """Build a crop database from the dataset."""
        unique_crops = set()
        for crops in self.dataset['Crop_Type'].str.split(','):
            unique_crops.update(crops)
        
        crop_database = {}
        for crop in unique_crops:
            # Extract crop characteristics from the dataset
            crop_data = self.dataset[self.dataset['Crop_Type'].str.contains(crop)]
            
            crop_database[crop] = {
                'avg_farm_size': crop_data['Farm_Size'].mean(),
                'irrigation_rate': (crop_data['Irrigation'] == 'Yes').mean(),
                'avg_experience': crop_data['Farmer_Experience'].mean(),
            }
        
        return crop_database

    def setup_preprocessing(self):
        """Setup preprocessing pipeline for different feature types."""
        # Categorical features
        categorical_features = [
            'Region', 'Rainy_Season_Length', 'Flood_Frequency', 
            'Soil_Health', 'Irrigation', 'Disaster_Loss_Impact',
            'Crop_Type'  # Added Crop_Type
        ]
        
        # Numerical features
        numerical_features = ['Farm_Size', 'Farmer_Experience']
        
        # Preprocessing steps
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='Unknown')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])
        
        numerical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        # Combine preprocessing steps
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', numerical_transformer, numerical_features),
                ('cat', categorical_transformer, categorical_features)
            ]
        )
    def train_base_model(self):
        """Train a base model using the dataset and evaluate it with multiple metrics."""
    # Prepare features and target
        X = self.dataset.drop('Risk_Score', axis=1)
        y = self.dataset['Risk_Score']
    
    # Split the data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create and train model pipeline
        self.model = Pipeline([
        ('preprocessor', self.preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    # Train the model
        self.model.fit(X_train, y_train)
    
    # Make predictions
        y_pred = self.model.predict(X_test)
    
    # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=1)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=1)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=1)
        conf_matrix = confusion_matrix(y_test, y_pred)
    
    # Display results
        print(f"Model Accuracy: {accuracy:.2f}")
        print(f"Precision: {precision:.2f}")
        print(f"Recall: {recall:.2f}")
        print(f"F1 Score: {f1:.2f}")
        print("\nConfusion Matrix:")
        print(conf_matrix)


    def find_most_similar_crops(self, unknown_crops: List[str]) -> List[str]:
        """Find the most similar known crops using multiple similarity metrics."""
        similar_crops = []
        for crop in unknown_crops:
            # Similarity matching using multiple approaches
            crop_matches = []
            
            # 1. Direct name similarity using difflib
            known_crops = list(self.crop_database.keys())
            crop_matches.extend(
                difflib.get_close_matches(crop, known_crops, n=2, cutoff=0.6)
            )
            
            # If no matches found, use all known crops
            if not crop_matches:
                crop_matches = known_crops[:2]
            
            similar_crops.extend(set(crop_matches))
        
        return list(set(similar_crops))
    
    def predict_risk(self, farm_data: Dict[str, Union[str, int, List[str]]]) -> str:
        """Predict risk for given farm data with advanced crop handling."""
        # Handle multiple or unknown crops
        input_crops = farm_data.get('Crop_Type', [])
        if isinstance(input_crops, str):
            input_crops = [crop.strip() for crop in input_crops.split(',')]
        
        # Find similar known crops
        matched_crops = self.find_most_similar_crops(input_crops)
        
        # Update farm data with matched crops
        farm_data['Crop_Type'] = ','.join(matched_crops)
        
        # Validate and fill missing features
        required_features = [
            'Region', 'Crop_Type', 'Farm_Size', 'Rainy_Season_Length', 
            'Flood_Frequency', 'Soil_Health', 'Irrigation', 
            'Farmer_Experience', 'Disaster_Loss_Impact'
        ]
        
        for feature in required_features:
            if feature not in farm_data or farm_data[feature] is None:
                farm_data[feature] = self.get_default_value(feature)
        
        # Convert to DataFrame for prediction
        df = pd.DataFrame([farm_data])
        
        # Predict risk
        risk_prediction = self.model.predict(df)[0]
        
        return risk_prediction

    def get_default_value(self, feature: str) -> Union[str, int]:
        """Provide a default value for missing features."""
        defaults = {
            'Region': 'Normal Zone',
            'Crop_Type': list(self.crop_database.keys())[0],
            'Farm_Size': 20,
            'Rainy_Season_Length': '4 months',
            'Flood_Frequency': 'Occasional',
            'Soil_Health': 'Good',
            'Irrigation': 'No',
            'Farmer_Experience': 5,
            'Disaster_Loss_Impact': 'Low'
        }
        return defaults.get(feature, None)
    
def main():
    # Initialize the risk predictor
    risk_predictor = FarmRiskPredictor()
    
    # Example scenarios
    scenarios = [
        # Single unknown crop
        {
            "Region": "Flood Zone",
            "Crop_Type": "Quinoa",
            "Farm_Size": 20,
            "Rainy_Season_Length": "4 months",
            "Flood_Frequency": "Occasional",
            "Soil_Health": "Good",
            "Irrigation": "Yes",
            "Farmer_Experience": 10,
            "Disaster_Loss_Impact": "Moderate"
        },
        # Multiple crops
        {
            "Region": "Drought Zone",
            "Crop_Type": "Amaranth, Hemp",
            "Farm_Size": 25,
            "Rainy_Season_Length": "3 months",
            "Flood_Frequency": "Rare",
            "Soil_Health": "Average",
            "Irrigation": "No",
            "Farmer_Experience": 15,
            "Disaster_Loss_Impact": "Low"
        }
    ]
    
    # Predict risk for each scenario
    
    for i, farm_data in enumerate(scenarios, 1):
        risk_score = risk_predictor.predict_risk(farm_data)
        print(f"Scenario {i} - Predicted Risk Score: {risk_score}")
        print(f"Input Crops: {farm_data['Crop_Type']}\n")

if __name__ == "__main__":
    main()
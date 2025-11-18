#!/usr/bin/env python3
"""
Unit Tests for Predictive Maintenance Model

Tests the training script components and model functionality.
"""

import unittest
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Add model directory to path
sys.path.insert(0, str(Path(__file__).parent))

from train_xgboost_model import (
    DataLoader,
    FeatureEngineer,
    ModelTrainer,
    MetricsCalculator,
    ArtifactManager,
    time_based_split
)

class TestDataLoader(unittest.TestCase):
    """Test DataLoader class"""
    
    def setUp(self):
        self.loader = DataLoader(prediction_horizon=[1, 6, 24])
    
    def test_generate_synthetic_data(self):
        """Test synthetic data generation"""
        df = self.loader.generate_synthetic_data(n_samples=1000)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertIn('target', df.columns)
        self.assertIn('time_until_failure', df.columns)
        self.assertIn('timestamp', df.columns)
    
    def test_predictive_labeling(self):
        """Test predictive labeling"""
        df = self.loader.generate_synthetic_data(n_samples=100)
        # Check that targets are binary
        self.assertTrue(df['target'].isin([0, 1]).all())
        # Check that time_until_failure is numeric
        self.assertTrue(pd.api.types.is_numeric_dtype(df['time_until_failure']))

class TestFeatureEngineer(unittest.TestCase):
    """Test FeatureEngineer class"""
    
    def setUp(self):
        self.engineer = FeatureEngineer(auto_detect_windows=False)
        # Generate test data
        loader = DataLoader()
        self.df = loader.generate_synthetic_data(n_samples=500)
    
    def test_create_time_features(self):
        """Test time feature creation"""
        df = self.engineer.create_time_features(self.df)
        self.assertIn('hour', df.columns)
        self.assertIn('day_of_week', df.columns)
        self.assertIn('time_since_last', df.columns)
    
    def test_create_windowed_features(self):
        """Test windowed feature creation"""
        df = self.engineer.create_time_features(self.df)
        df = self.engineer.create_windowed_features(df, ['5min', '15min'])
        # Check that window features were created
        window_features = [col for col in df.columns if '5min' in col or '15min' in col]
        self.assertGreater(len(window_features), 0)
    
    def test_create_early_warning_indicators(self):
        """Test early warning indicator creation"""
        df = self.engineer.create_early_warning_indicators(self.df)
        self.assertIn('cpu_high', df.columns)
        self.assertIn('memory_high', df.columns)
        self.assertIn('early_warning_score', df.columns)
    
    def test_engineer_features(self):
        """Test complete feature engineering"""
        df, features = self.engineer.engineer_features(self.df, target_col='target')
        self.assertGreater(len(features), 0)
        self.assertGreater(len(df.columns), len(self.df.columns))

class TestModelTrainer(unittest.TestCase):
    """Test ModelTrainer class"""
    
    def setUp(self):
        self.trainer = ModelTrainer(use_xgboost=False)  # Use GradientBoosting for testing
        # Generate test data
        loader = DataLoader()
        df = loader.generate_synthetic_data(n_samples=500)
        engineer = FeatureEngineer(auto_detect_windows=False)
        df, features = engineer.engineer_features(df, target_col='target')
        
        train_df, test_df = time_based_split(df, test_size=0.2, target_col='target')
        self.X_train = train_df[features].values
        self.y_train = train_df['target'].values
        self.X_test = test_df[features].values
        self.y_test = test_df['target'].values
    
    def test_train_classification(self):
        """Test classification model training"""
        model, reg_model = self.trainer.train(
            self.X_train, self.y_train, self.X_test, self.y_test,
            tune_hyperparameters=False,
            y_train_regression=None
        )
        self.assertIsNotNone(model)
        self.assertIsNone(reg_model)
    
    def test_predict(self):
        """Test prediction"""
        model, _ = self.trainer.train(
            self.X_train, self.y_train, self.X_test, self.y_test,
            tune_hyperparameters=False
        )
        predictions = self.trainer.predict(self.X_test)
        self.assertEqual(len(predictions), len(self.y_test))
        self.assertTrue((predictions >= 0).all())
        self.assertTrue((predictions <= 1).all())

class TestMetricsCalculator(unittest.TestCase):
    """Test MetricsCalculator class"""
    
    def setUp(self):
        self.calc = MetricsCalculator(Path(__file__).parent / "artifacts" / "test")
        self.y_true = np.array([0, 1, 1, 0, 1, 0, 0, 1])
        self.y_pred = np.array([0, 1, 0, 0, 1, 0, 1, 1])
        self.y_pred_proba = np.array([0.1, 0.9, 0.4, 0.2, 0.8, 0.3, 0.6, 0.95])
    
    def test_calculate_metrics(self):
        """Test metrics calculation"""
        metrics = self.calc.calculate_metrics(self.y_true, self.y_pred, self.y_pred_proba)
        self.assertIn('accuracy', metrics)
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        self.assertIn('f1_score', metrics)
        self.assertIn('roc_auc', metrics)
        self.assertTrue(0 <= metrics['accuracy'] <= 1)

class TestArtifactManager(unittest.TestCase):
    """Test ArtifactManager class"""
    
    def setUp(self):
        self.manager = ArtifactManager(base_dir=Path(__file__).parent / "artifacts" / "test")
    
    def test_version_dir_creation(self):
        """Test version directory creation"""
        version_dir = self.manager.get_version_dir()
        self.assertTrue(version_dir.exists())
        self.assertIn('v', version_dir.name)

def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestDataLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestFeatureEngineer))
    suite.addTests(loader.loadTestsFromTestCase(TestModelTrainer))
    suite.addTests(loader.loadTestsFromTestCase(TestMetricsCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestArtifactManager))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)


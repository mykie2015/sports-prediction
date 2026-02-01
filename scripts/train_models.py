#!/usr/bin/env python3
"""
Model Training Script
====================

Trains ML models on historical tennis data.

Models trained:
1. Logistic Regression (baseline)
2. Random Forest (primary)
3. XGBoost (advanced)
"""

import os
import sys
import json
from pathlib import Path
import numpy as np
from sklearn.model_selection import train_test_split

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sports_prediction.sports.tennis.ml_predictor import TennisMLPredictor


def load_training_data(dataset_path: Path) -> tuple:
    """Load training dataset from JSON file."""
    if not dataset_path.exists():
        print(f"\n✗ ERROR: Training dataset not found at {dataset_path}")
        print("   Run collect_historical_data.py first!")
        return None, None, None
    
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)
    
    X = np.array(dataset['X'])
    y = np.array(dataset['y'])
    feature_names = dataset['feature_names']
    
    print(f"\n✓ Loaded training dataset")
    print(f"  Samples: {len(X)}")
    print(f"  Features: {len(X[0])}")
    print(f"  Class distribution: {sum(y)} Player1 wins, {len(y) - sum(y)} Player2 wins")
    
    return X, y, feature_names


def main():
    """Main execution."""
    print("\n" + "="*70)
    print("TENNIS ML MODEL TRAINING")
    print("="*70)
    
    # Load dataset
    dataset_path = Path(__file__).parent.parent / "data" / "training_dataset.json"
    X, y, feature_names = load_training_data(dataset_path)
    
    if X is None:
        return 1
    
    # Split data (80% train, 20% validation)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n📊 Data split:")
    print(f"  Training: {len(X_train)} samples")
    print(f"  Validation: {len(X_val)} samples")
    
    # Initialize predictor
    model_dir = Path(__file__).parent.parent / "src" / "sports_prediction" / "sports" / "tennis" / "models"
    predictor = TennisMLPredictor(model_dir=model_dir)
    
    # Train models
    print(f"\n{'='*70}")
    print("TRAINING MODELS")
    print(f"{'='*70}")
    
    results = {}
    
    # 1. Logistic Regression
    print(f"\n1️⃣  LOGISTIC REGRESSION")
    print("-" * 70)
    lr_metrics = predictor.train_logistic_regression(X_train, y_train, X_val, y_val)
    results['logistic_regression'] = lr_metrics
    print(f"✓ Training complete")
    print(f"  Train Accuracy: {lr_metrics['train_accuracy']:.3f}")
    print(f"  Val Accuracy: {lr_metrics['val_accuracy']:.3f}")
    print(f"  Val Log Loss: {lr_metrics['val_log_loss']:.3f}")
    
    # 2. Random Forest
    print(f"\n2️⃣  RANDOM FOREST")
    print("-" * 70)
    rf_metrics = predictor.train_random_forest(X_train, y_train, X_val, y_val, n_estimators=100)
    results['random_forest'] = rf_metrics
    print(f"✓ Training complete")
    print(f"  Train Accuracy: {rf_metrics['train_accuracy']:.3f}")
    print(f"  Val Accuracy: {rf_metrics['val_accuracy']:.3f}")
    print(f"  Val Log Loss: {rf_metrics['val_log_loss']:.3f}")
    
    # 3. XGBoost
    print(f"\n3️⃣  XGBOOST")
    print("-" * 70)
    xgb_metrics = predictor.train_xgboost(X_train, y_train, X_val, y_val)
    results['xgboost'] = xgb_metrics
    print(f"✓ Training complete")
    print(f"  Train Accuracy: {xgb_metrics['train_accuracy']:.3f}")
    print(f"  Val Accuracy: {xgb_metrics['val_accuracy']:.3f}")
    print(f"  Val Log Loss: {xgb_metrics['val_log_loss']:.3f}")
    
    # Summary
    print(f"\n{'='*70}")
    print("TRAINING SUMMARY")
    print(f"{'='*70}")
    
    print(f"\n{'Model':<20} {'Train Acc':>12} {'Val Acc':>12} {'Val LogLoss':>12}")
    print("-" * 70)
    for model_name, metrics in results.items():
        print(f"{model_name:<20} {metrics['train_accuracy']:>12.3f} "
              f"{metrics['val_accuracy']:>12.3f} {metrics['val_log_loss']:>12.3f}")
    
    # Find best model
    best_model = max(results.items(), key=lambda x: x[1]['val_accuracy'])
    print(f"\n🏆 Best Model: {best_model[0].upper()}")
    print(f"   Validation Accuracy: {best_model[1]['val_accuracy']:.3f}")
    
    # Save results
    results_path = Path(__file__).parent.parent / "data" / "training_results.json"
    with open(results_path, 'w') as f:
        json.dump({
            'results': results,
            'best_model': best_model[0],
            'dataset_size': len(X),
            'train_size': len(X_train),
            'val_size': len(X_val),
            'feature_count': len(feature_names),
        }, f, indent=2)
    
    print(f"\n💾 Training results saved to: {results_path}")
    print(f"💾 Models saved to: {model_dir}")
    
    print(f"\n{'='*70}")
    print("✓ MODEL TRAINING COMPLETE!")
    print(f"{'='*70}")
    print(f"\nNext step: Run examples/ao2026_ml_prediction.py")
    print(f"           It will now use trained ML models instead of heuristics!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Tennis ML Predictor - Machine Learning models for tennis match prediction.

Implements multiple models:
- Logistic Regression (baseline)
- Random Forest (primary)
- XGBoost (advanced)
"""

from typing import Dict, Any, Tuple, Optional, List
import logging
import numpy as np
from pathlib import Path
import joblib

from sports_prediction.sports.tennis.features import TennisFeatureExtractor

logger = logging.getLogger(__name__)


class TennisMLPredictor:
    """
    ML-based tennis match predictor.
    
    Uses ensemble of models to predict match outcomes.
    """
    
    def __init__(self, model_dir: Optional[Path] = None):
        """
        Initialize predictor.
        
        Args:
            model_dir: Directory containing trained models (optional)
        """
        self.feature_extractor = TennisFeatureExtractor()
        self.model_dir = model_dir or Path(__file__).parent / "models"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.models = {}
        self._load_models()
    
    def _load_models(self):
        """Load trained models from disk if available."""
        model_files = {
            'logistic': self.model_dir / 'logistic_regression.joblib',
            'random_forest': self.model_dir / 'random_forest.joblib',
            'xgboost': self.model_dir / 'xgboost.joblib',
        }
        
        for name, path in model_files.items():
            if path.exists():
                try:
                    self.models[name] = joblib.load(path)
                    logger.info(f"Loaded {name} model from {path}")
                except Exception as e:
                    logger.warning(f"Failed to load {name} model: {e}")
    
    def predict(
        self,
        player1_stats: Dict[str, Any],
        player2_stats: Dict[str, Any],
        h2h_data: Optional[Dict[str, Any]] = None,
        surface: str = "hard",
        tournament_name: str = "",
        use_ensemble: bool = True
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Predict match outcome.
        
        Args:
            player1_stats: Player 1 API data
            player2_stats: Player 2 API data
            h2h_data: Head-to-head data
            surface: Court surface
            tournament_name: Tournament name
            use_ensemble: If True, use ensemble of all available models
            
        Returns:
            Tuple of (prob_player1_wins, prob_player2_wins, metadata)
        """
        # Extract features
        features = self.feature_extractor.extract_match_features(
            player1_stats=player1_stats,
            player2_stats=player2_stats,
            h2h_data=h2h_data,
            surface=surface,
            tournament_name=tournament_name
        )
        
        # Convert to numpy array in correct order
        feature_names = self.feature_extractor.get_feature_names()
        X = np.array([[features[name] for name in feature_names]])
        
        # If no trained models, use simple heuristic
        if not self.models:
            logger.warning("No trained models available, using heuristic prediction")
            prob_p1, prob_p2 = self._heuristic_prediction(features)
            metadata = {
                'method': 'heuristic',
                'features_used': len(feature_names),
                'feature_values': features
            }
            return prob_p1, prob_p2, metadata
        
        # Use trained models
        if use_ensemble and len(self.models) > 1:
            # Ensemble prediction (average probabilities)
            predictions = []
            for name, model in self.models.items():
                try:
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba(X)[0]
                        predictions.append(proba)
                        logger.info(f"{name} predicted: {proba}")
                except Exception as e:
                    logger.error(f"Error predicting with {name}: {e}")
            
            if predictions:
                # Average probabilities
                avg_proba = np.mean(predictions, axis=0)
                prob_p1, prob_p2 = float(avg_proba[0]), float(avg_proba[1])
                metadata = {
                    'method': 'ensemble',
                    'models_used': list(self.models.keys()),
                    'features_used': len(feature_names),
                    'feature_values': features
                }
            else:
                prob_p1, prob_p2 = self._heuristic_prediction(features)
                metadata = {'method': 'heuristic_fallback'}
        else:
            # Use single model (prefer random forest)
            model_priority = ['random_forest', 'xgboost', 'logistic']
            model_name = None
            for name in model_priority:
                if name in self.models:
                    model_name = name
                    break
            
            if model_name:
                model = self.models[model_name]
                proba = model.predict_proba(X)[0]
                prob_p1, prob_p2 = float(proba[0]), float(proba[1])
                metadata = {
                    'method': 'single_model',
                    'model_used': model_name,
                    'features_used': len(feature_names),
                    'feature_values': features
                }
            else:
                prob_p1, prob_p2 = self._heuristic_prediction(features)
                metadata = {'method': 'heuristic_fallback'}
        
        return prob_p1, prob_p2, metadata
    
    def _heuristic_prediction(self, features: Dict[str, float]) -> Tuple[float, float]:
        """
        Simple heuristic prediction when no trained models available.
        
        Based on weighted factors similar to examples/ao2026_final_prediction.py
        """
        # Ranking factor (20% weight)
        p1_rank = features['p1_ranking']
        p2_rank = features['p2_ranking']
        if p1_rank < p2_rank:
            ranking_score = 0.65
        else:
            ranking_score = 0.35
        
        # Age/Experience balance (20% weight)
        # Younger players have energy, older have experience
        age_diff = features['age_diff']
        exp_diff = features['experience_diff']
        
        if exp_diff > 10:  # P1 much more experienced
            exp_score = 0.45
        elif exp_diff < -10:  # P2 much more experienced
            exp_score = 0.55
        else:
            exp_score = 0.50
        
        # Prize money (career success) (25% weight)
        prize_diff = features['prize_diff_log']
        if prize_diff > 1.0:  # P1 significantly more successful
            prize_score = 0.60
        elif prize_diff < -1.0:  # P2 significantly more successful
            prize_score = 0.40
        else:
            prize_score = 0.50
        
        # Physical attributes (10% weight)
        height_diff = features['height_diff']
        physical_score = 0.50 + (height_diff * 0.05)  # Slight advantage to taller player
        physical_score = max(0.4, min(0.6, physical_score))  # Clamp
        
        # Grand Slam experience (25% weight)
        is_gs = features['is_grand_slam']
        if is_gs:
            # In Grand Slams, experience matters more
            if exp_diff > 5:
                gs_score = 0.40
            else:
                gs_score = 0.55
        else:
            gs_score = 0.50
        
        # Weighted average
        weights = {
            'ranking': 0.20,
            'experience': 0.20,
            'prize': 0.25,
            'physical': 0.10,
            'gs': 0.25
        }
        
        prob_p1 = (
            ranking_score * weights['ranking'] +
            exp_score * weights['experience'] +
            prize_score * weights['prize'] +
            physical_score * weights['physical'] +
            gs_score * weights['gs']
        )
        
        prob_p2 = 1.0 - prob_p1
        
        return prob_p1, prob_p2
    
    def train_logistic_regression(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Train Logistic Regression model.
        
        Args:
            X_train: Training features
            y_train: Training labels (0 for player2 wins, 1 for player1 wins)
            X_val: Validation features
            y_val: Validation labels
            
        Returns:
            Training metrics
        """
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, log_loss
        
        logger.info("Training Logistic Regression model...")
        
        model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            class_weight='balanced'
        )
        
        model.fit(X_train, y_train)
        
        # Save model
        model_path = self.model_dir / 'logistic_regression.joblib'
        joblib.dump(model, model_path)
        self.models['logistic'] = model
        logger.info(f"Saved Logistic Regression model to {model_path}")
        
        # Evaluate
        train_acc = accuracy_score(y_train, model.predict(X_train))
        metrics = {'train_accuracy': train_acc}
        
        if X_val is not None and y_val is not None:
            val_pred = model.predict(X_val)
            val_proba = model.predict_proba(X_val)
            val_acc = accuracy_score(y_val, val_pred)
            val_logloss = log_loss(y_val, val_proba)
            metrics.update({
                'val_accuracy': val_acc,
                'val_log_loss': val_logloss
            })
            logger.info(f"Logistic Regression - Train Acc: {train_acc:.3f}, Val Acc: {val_acc:.3f}")
        
        return metrics
    
    def train_random_forest(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        n_estimators: int = 100
    ) -> Dict[str, Any]:
        """Train Random Forest model."""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import accuracy_score, log_loss
        
        logger.info("Training Random Forest model...")
        
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # Save model
        model_path = self.model_dir / 'random_forest.joblib'
        joblib.dump(model, model_path)
        self.models['random_forest'] = model
        logger.info(f"Saved Random Forest model to {model_path}")
        
        # Evaluate
        train_acc = accuracy_score(y_train, model.predict(X_train))
        metrics = {'train_accuracy': train_acc}
        
        if X_val is not None and y_val is not None:
            val_pred = model.predict(X_val)
            val_proba = model.predict_proba(X_val)
            val_acc = accuracy_score(y_val, val_pred)
            val_logloss = log_loss(y_val, val_proba)
            metrics.update({
                'val_accuracy': val_acc,
                'val_log_loss': val_logloss
            })
            logger.info(f"Random Forest - Train Acc: {train_acc:.3f}, Val Acc: {val_acc:.3f}")
        
        return metrics
    
    def train_xgboost(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Train XGBoost model."""
        import xgboost as xgb
        from sklearn.metrics import accuracy_score, log_loss
        
        logger.info("Training XGBoost model...")
        
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss',
            use_label_encoder=False
        )
        
        model.fit(X_train, y_train)
        
        # Save model
        model_path = self.model_dir / 'xgboost.joblib'
        joblib.dump(model, model_path)
        self.models['xgboost'] = model
        logger.info(f"Saved XGBoost model to {model_path}")
        
        # Evaluate
        train_acc = accuracy_score(y_train, model.predict(X_train))
        metrics = {'train_accuracy': train_acc}
        
        if X_val is not None and y_val is not None:
            val_pred = model.predict(X_val)
            val_proba = model.predict_proba(X_val)
            val_acc = accuracy_score(y_val, val_pred)
            val_logloss = log_loss(y_val, val_proba)
            metrics.update({
                'val_accuracy': val_acc,
                'val_log_loss': val_logloss
            })
            logger.info(f"XGBoost - Train Acc: {train_acc:.3f}, Val Acc: {val_acc:.3f}")
        
        return metrics

"""
Attack type classifier using XGBoost.
Trained on CICIDS2017 dataset to classify traffic into attack categories.
"""

import os
import logging
import numpy as np
from typing import Tuple, Optional

import joblib

from ..config import config

logger = logging.getLogger(__name__)


class AttackClassifier:
    """
    XGBoost-based attack classifier.
    Classifies network flows into: Benign, DoS, DDoS, PortScan,
    BruteForce, WebAttack, Botnet, Infiltration.
    """

    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self._loaded = False

    def load(self) -> bool:
        """Load pre-trained model from disk."""
        model_dir = config.model_dir

        try:
            model_path = os.path.join(model_dir, "xgboost_classifier.joblib")
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                logger.info("XGBoost classifier loaded")

            scaler_path = os.path.join(model_dir, "classifier_scaler.joblib")
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)

            encoder_path = os.path.join(model_dir, "label_encoder.joblib")
            if os.path.exists(encoder_path):
                self.label_encoder = joblib.load(encoder_path)

            self._loaded = self.model is not None
            return self._loaded

        except Exception as e:
            logger.error(f"Failed to load attack classifier: {e}")
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def predict(self, features: np.ndarray) -> Tuple[str, float]:
        """
        Classify a flow's attack type.

        Returns:
            (attack_type, confidence) e.g. ("DDoS", 0.92)
        """
        if not self._loaded:
            return "Benign", 1.0

        features_2d = features.reshape(1, -1)

        # Scale features
        if self.scaler is not None:
            features_2d = self.scaler.transform(features_2d)

        # Predict probabilities
        probabilities = self.model.predict_proba(features_2d)[0]
        predicted_idx = np.argmax(probabilities)
        confidence = float(probabilities[predicted_idx])

        # Decode label
        if self.label_encoder is not None:
            attack_type = self.label_encoder.inverse_transform([predicted_idx])[0]
        else:
            attack_type = config.attack_labels[predicted_idx] if predicted_idx < len(config.attack_labels) else "Unknown"

        return attack_type, confidence

    def predict_batch(self, features: np.ndarray) -> list:
        """Classify multiple flows at once."""
        if not self._loaded:
            return [("Benign", 1.0)] * len(features)

        if self.scaler is not None:
            features = self.scaler.transform(features)

        probabilities = self.model.predict_proba(features)
        results = []
        for probs in probabilities:
            idx = np.argmax(probs)
            confidence = float(probs[idx])
            if self.label_encoder is not None:
                label = self.label_encoder.inverse_transform([idx])[0]
            else:
                label = config.attack_labels[idx] if idx < len(config.attack_labels) else "Unknown"
            results.append((label, confidence))

        return results

    def save(self, model_dir: str = ""):
        """Save trained model to disk."""
        save_dir = model_dir or config.model_dir
        os.makedirs(save_dir, exist_ok=True)

        if self.model:
            joblib.dump(self.model, os.path.join(save_dir, "xgboost_classifier.joblib"))
        if self.scaler:
            joblib.dump(self.scaler, os.path.join(save_dir, "classifier_scaler.joblib"))
        if self.label_encoder:
            joblib.dump(self.label_encoder, os.path.join(save_dir, "label_encoder.joblib"))

        logger.info(f"Attack classifier saved to {save_dir}")

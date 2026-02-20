"""
Model training pipeline.
Trains anomaly detector and attack classifier on CICIDS2017 dataset.

Usage:
    python -m ml.pipeline.training --model all
    python -m ml.pipeline.training --model anomaly
    python -m ml.pipeline.training --model classifier
"""

import os
import logging
import argparse
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import joblib

from ..config import config
from ..models.anomaly_detector import Autoencoder, AnomalyDetector
from ..models.attack_classifier import AttackClassifier
from ..models.lstm_cnn import LSTMCNNModel

logger = logging.getLogger(__name__)


def load_cicids_data(data_path: str) -> pd.DataFrame:
    """Load and preprocess CICIDS2017 dataset."""
    logger.info(f"Loading data from {data_path}")

    # CICIDS2017 comes as multiple CSV files
    dfs = []
    for f in os.listdir(data_path):
        if f.endswith(".csv"):
            df = pd.read_csv(os.path.join(data_path, f), low_memory=False)
            dfs.append(df)

    if not dfs:
        raise FileNotFoundError(f"No CSV files found in {data_path}")

    data = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {len(data)} samples")

    # Clean column names
    data.columns = data.columns.str.strip()

    # Handle infinities and NaN
    data.replace([np.inf, -np.inf], np.nan, inplace=True)
    data.dropna(inplace=True)

    return data


def train_anomaly_detector(data: pd.DataFrame, save_dir: str):
    """Train Isolation Forest + Autoencoder on normal traffic."""
    logger.info("Training anomaly detector...")

    # Extract features (exclude label column)
    label_col = "Label" if "Label" in data.columns else data.columns[-1]
    normal_data = data[data[label_col].str.strip().str.upper() == "BENIGN"]

    feature_cols = [c for c in data.columns if c != label_col]
    X_normal = normal_data[feature_cols].values.astype(np.float32)

    # Pad/trim to expected feature count
    if X_normal.shape[1] < config.total_features:
        padding = np.zeros((X_normal.shape[0], config.total_features - X_normal.shape[1]))
        X_normal = np.hstack([X_normal, padding])
    else:
        X_normal = X_normal[:, :config.total_features]

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_normal)

    # Train/val split
    X_train, X_val = train_test_split(X_scaled, test_size=0.2, random_state=42)

    # 1. Isolation Forest
    logger.info("Training Isolation Forest...")
    iso_forest = IsolationForest(
        n_estimators=200,
        contamination=0.01,
        random_state=42,
        n_jobs=-1,
    )
    iso_forest.fit(X_train)

    # 2. Autoencoder
    logger.info("Training Autoencoder...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    autoencoder = Autoencoder(input_dim=config.total_features).to(device)

    train_tensor = torch.FloatTensor(X_train).to(device)
    val_tensor = torch.FloatTensor(X_val).to(device)

    train_loader = DataLoader(TensorDataset(train_tensor, train_tensor), batch_size=256, shuffle=True)

    optimizer = torch.optim.Adam(autoencoder.parameters(), lr=config.learning_rate)
    criterion = nn.MSELoss()

    autoencoder.train()
    for epoch in range(config.epochs):
        total_loss = 0
        for batch_x, _ in train_loader:
            optimizer.zero_grad()
            output = autoencoder(batch_x)
            loss = criterion(output, batch_x)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        if (epoch + 1) % 10 == 0:
            avg_loss = total_loss / len(train_loader)
            logger.info(f"Epoch {epoch+1}/{config.epochs}, Loss: {avg_loss:.6f}")

    # Calculate threshold (95th percentile of validation reconstruction error)
    autoencoder.eval()
    val_errors = autoencoder.reconstruction_error(val_tensor).cpu().numpy()
    threshold = float(np.percentile(val_errors, 95))
    logger.info(f"Autoencoder threshold: {threshold:.6f}")

    # Save
    detector = AnomalyDetector()
    detector.isolation_forest = iso_forest
    detector.autoencoder = autoencoder
    detector.scaler = scaler
    detector.ae_threshold = threshold
    detector.save(save_dir)

    logger.info("Anomaly detector training complete")


def train_attack_classifier(data: pd.DataFrame, save_dir: str):
    """Train XGBoost classifier on labeled attack data."""
    logger.info("Training attack classifier...")

    label_col = "Label" if "Label" in data.columns else data.columns[-1]
    feature_cols = [c for c in data.columns if c != label_col]

    X = data[feature_cols].values.astype(np.float32)
    y = data[label_col].str.strip().values

    # Pad/trim features
    if X.shape[1] < config.total_features:
        padding = np.zeros((X.shape[0], config.total_features - X.shape[1]))
        X = np.hstack([X, padding])
    else:
        X = X[:, :config.total_features]

    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    # Train XGBoost
    try:
        from xgboost import XGBClassifier
    except ImportError:
        logger.error("xgboost not installed. Run: pip install xgboost")
        return

    model = XGBClassifier(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric="mlogloss",
        n_jobs=-1,
        random_state=42,
    )

    logger.info("Fitting XGBoost...")
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    # Evaluate
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, target_names=le.classes_)
    f1 = f1_score(y_test, y_pred, average="weighted")
    logger.info(f"\nClassification Report:\n{report}")
    logger.info(f"Weighted F1: {f1:.4f}")

    # Save
    classifier = AttackClassifier()
    classifier.model = model
    classifier.scaler = scaler
    classifier.label_encoder = le
    classifier.save(save_dir)

    logger.info("Attack classifier training complete")


def train_lstm_cnn(data: pd.DataFrame, save_dir: str):
    """Train LSTM+CNN hybrid model."""
    logger.info("Training LSTM+CNN model...")

    label_col = "Label" if "Label" in data.columns else data.columns[-1]
    feature_cols = [c for c in data.columns if c != label_col]

    X = data[feature_cols].values.astype(np.float32)
    y_raw = data[label_col].str.strip().str.upper().values
    y = (y_raw != "BENIGN").astype(np.float32)  # binary: 0=normal, 1=anomalous

    # Pad/trim
    if X.shape[1] < config.total_features:
        padding = np.zeros((X.shape[0], config.total_features - X.shape[1]))
        X = np.hstack([X, padding])
    else:
        X = X[:, :config.total_features]

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    # Train
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = LSTMCNNModel(input_dim=config.total_features).to(device)

    train_dataset = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train))
    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)

    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    criterion = nn.BCELoss()

    model.train()
    for epoch in range(config.epochs):
        total_loss = 0
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            output = model(batch_x)
            loss = criterion(output, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch+1}/{config.epochs}, Loss: {total_loss/len(train_loader):.4f}")

    # Evaluate
    model.eval()
    with torch.no_grad():
        test_x = torch.FloatTensor(X_test).to(device)
        preds = (model(test_x).cpu().numpy() > 0.5).astype(int)
        accuracy = (preds == y_test).mean()
        logger.info(f"LSTM+CNN Accuracy: {accuracy:.4f}")

    # Save
    os.makedirs(save_dir, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(save_dir, "lstm_cnn.pth"))
    logger.info("LSTM+CNN training complete")


def main():
    parser = argparse.ArgumentParser(description="Train ML models")
    parser.add_argument("--model", choices=["all", "anomaly", "classifier", "lstm_cnn"], default="all")
    parser.add_argument("--data", default=config.training_data_path)
    parser.add_argument("--output", default=config.model_dir)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    data = load_cicids_data(args.data)
    os.makedirs(args.output, exist_ok=True)

    if args.model in ("all", "anomaly"):
        train_anomaly_detector(data, args.output)

    if args.model in ("all", "classifier"):
        train_attack_classifier(data, args.output)

    if args.model in ("all", "lstm_cnn"):
        train_lstm_cnn(data, args.output)

    logger.info("All training complete!")


if __name__ == "__main__":
    main()

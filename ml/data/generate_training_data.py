"""
Generate synthetic training data in CICIDS2017 format.
Creates realistic network flow data for training ML models.

This serves as bootstrap training data. For best results,
replace with the real CICIDS2017 dataset when available.

Usage:
    python -m ml.data.generate_training_data
"""

import os
import numpy as np
import pandas as pd

np.random.seed(42)

# CICIDS2017-compatible feature columns
FEATURE_COLUMNS = [
    "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
    "Total Length of Fwd Packets", "Total Length of Bwd Packets",
    "Fwd Packet Length Max", "Fwd Packet Length Min", "Fwd Packet Length Mean", "Fwd Packet Length Std",
    "Bwd Packet Length Max", "Bwd Packet Length Min", "Bwd Packet Length Mean", "Bwd Packet Length Std",
    "Flow Bytes/s", "Flow Packets/s",
    "Flow IAT Mean", "Flow IAT Std", "Flow IAT Max", "Flow IAT Min",
    "Fwd IAT Mean", "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min",
    "Bwd IAT Mean", "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min",
    "Fwd Header Length", "Bwd Header Length",
    "Fwd Packets/s", "Bwd Packets/s",
    "Packet Length Mean", "Packet Length Std", "Packet Length Variance",
    "FIN Flag Count", "SYN Flag Count", "RST Flag Count",
    "PSH Flag Count", "ACK Flag Count", "URG Flag Count",
]


def generate_benign(n: int) -> pd.DataFrame:
    """Generate normal/benign traffic patterns."""
    data = {
        "Flow Duration": np.random.exponential(5000, n),
        "Total Fwd Packets": np.random.poisson(15, n) + 1,
        "Total Backward Packets": np.random.poisson(12, n) + 1,
        "Total Length of Fwd Packets": np.random.exponential(2000, n),
        "Total Length of Bwd Packets": np.random.exponential(5000, n),
        "Fwd Packet Length Max": np.random.exponential(800, n),
        "Fwd Packet Length Min": np.random.exponential(40, n),
        "Fwd Packet Length Mean": np.random.exponential(200, n),
        "Fwd Packet Length Std": np.random.exponential(100, n),
        "Bwd Packet Length Max": np.random.exponential(1200, n),
        "Bwd Packet Length Min": np.random.exponential(40, n),
        "Bwd Packet Length Mean": np.random.exponential(400, n),
        "Bwd Packet Length Std": np.random.exponential(200, n),
        "Flow Bytes/s": np.random.exponential(50000, n),
        "Flow Packets/s": np.random.exponential(100, n),
        "Flow IAT Mean": np.random.exponential(500, n),
        "Flow IAT Std": np.random.exponential(300, n),
        "Flow IAT Max": np.random.exponential(2000, n),
        "Flow IAT Min": np.random.exponential(10, n),
        "Fwd IAT Mean": np.random.exponential(600, n),
        "Fwd IAT Std": np.random.exponential(400, n),
        "Fwd IAT Max": np.random.exponential(3000, n),
        "Fwd IAT Min": np.random.exponential(20, n),
        "Bwd IAT Mean": np.random.exponential(700, n),
        "Bwd IAT Std": np.random.exponential(500, n),
        "Bwd IAT Max": np.random.exponential(4000, n),
        "Bwd IAT Min": np.random.exponential(30, n),
        "Fwd Header Length": np.random.poisson(320, n),
        "Bwd Header Length": np.random.poisson(280, n),
        "Fwd Packets/s": np.random.exponential(50, n),
        "Bwd Packets/s": np.random.exponential(40, n),
        "Packet Length Mean": np.random.exponential(300, n),
        "Packet Length Std": np.random.exponential(150, n),
        "Packet Length Variance": np.random.exponential(25000, n),
        "FIN Flag Count": np.random.binomial(1, 0.3, n),
        "SYN Flag Count": np.random.binomial(1, 0.2, n),
        "RST Flag Count": np.random.binomial(1, 0.02, n),
        "PSH Flag Count": np.random.binomial(3, 0.5, n),
        "ACK Flag Count": np.random.poisson(10, n),
        "URG Flag Count": np.zeros(n),
    }
    df = pd.DataFrame(data)
    df["Label"] = "BENIGN"
    return df


def generate_dos(n: int) -> pd.DataFrame:
    """Generate DoS attack patterns — high packet rate, small packets."""
    data = {
        "Flow Duration": np.random.exponential(100, n),  # short bursts
        "Total Fwd Packets": np.random.poisson(500, n) + 100,  # many packets
        "Total Backward Packets": np.random.poisson(5, n),  # few responses
        "Total Length of Fwd Packets": np.random.exponential(50000, n),
        "Total Length of Bwd Packets": np.random.exponential(200, n),
        "Fwd Packet Length Max": np.random.exponential(200, n),
        "Fwd Packet Length Min": np.random.exponential(60, n) + 40,
        "Fwd Packet Length Mean": np.random.exponential(80, n) + 40,
        "Fwd Packet Length Std": np.random.exponential(20, n),  # low variance = uniform
        "Bwd Packet Length Max": np.random.exponential(100, n),
        "Bwd Packet Length Min": np.random.exponential(20, n),
        "Bwd Packet Length Mean": np.random.exponential(50, n),
        "Bwd Packet Length Std": np.random.exponential(30, n),
        "Flow Bytes/s": np.random.exponential(500000, n),  # very high
        "Flow Packets/s": np.random.exponential(5000, n),  # very high
        "Flow IAT Mean": np.random.exponential(1, n),  # very low IAT
        "Flow IAT Std": np.random.exponential(0.5, n),
        "Flow IAT Max": np.random.exponential(10, n),
        "Flow IAT Min": np.random.exponential(0.1, n),
        "Fwd IAT Mean": np.random.exponential(1, n),
        "Fwd IAT Std": np.random.exponential(0.5, n),
        "Fwd IAT Max": np.random.exponential(5, n),
        "Fwd IAT Min": np.random.exponential(0.05, n),
        "Bwd IAT Mean": np.random.exponential(100, n),
        "Bwd IAT Std": np.random.exponential(50, n),
        "Bwd IAT Max": np.random.exponential(500, n),
        "Bwd IAT Min": np.random.exponential(10, n),
        "Fwd Header Length": np.random.poisson(200, n),
        "Bwd Header Length": np.random.poisson(40, n),
        "Fwd Packets/s": np.random.exponential(5000, n),
        "Bwd Packets/s": np.random.exponential(10, n),
        "Packet Length Mean": np.random.exponential(80, n) + 40,
        "Packet Length Std": np.random.exponential(20, n),
        "Packet Length Variance": np.random.exponential(500, n),
        "FIN Flag Count": np.random.binomial(1, 0.05, n),
        "SYN Flag Count": np.random.binomial(10, 0.8, n),  # SYN flood
        "RST Flag Count": np.random.binomial(1, 0.1, n),
        "PSH Flag Count": np.random.binomial(1, 0.1, n),
        "ACK Flag Count": np.random.poisson(2, n),
        "URG Flag Count": np.zeros(n),
    }
    df = pd.DataFrame(data)
    df["Label"] = "DoS"
    return df


def generate_ddos(n: int) -> pd.DataFrame:
    """Generate DDoS patterns — similar to DoS but with distributed source characteristics."""
    df = generate_dos(n)
    df["Label"] = "DDoS"
    # DDoS has even higher packet rates and more uniform patterns
    df["Flow Packets/s"] *= 2
    df["Flow Bytes/s"] *= 1.5
    df["Fwd Packet Length Std"] *= 0.5  # more uniform
    return df


def generate_portscan(n: int) -> pd.DataFrame:
    """Generate port scan patterns — many short connections, SYN packets."""
    data = {
        "Flow Duration": np.random.exponential(50, n),  # very short
        "Total Fwd Packets": np.ones(n) + np.random.binomial(2, 0.3, n),  # 1-3 packets
        "Total Backward Packets": np.random.binomial(1, 0.5, n),  # 0-1 response
        "Total Length of Fwd Packets": np.random.exponential(60, n) + 40,
        "Total Length of Bwd Packets": np.random.exponential(40, n),
        "Fwd Packet Length Max": np.random.exponential(60, n) + 40,
        "Fwd Packet Length Min": np.random.exponential(40, n) + 40,
        "Fwd Packet Length Mean": np.random.exponential(50, n) + 40,
        "Fwd Packet Length Std": np.random.exponential(5, n),
        "Bwd Packet Length Max": np.random.exponential(60, n),
        "Bwd Packet Length Min": np.random.exponential(40, n),
        "Bwd Packet Length Mean": np.random.exponential(50, n),
        "Bwd Packet Length Std": np.random.exponential(10, n),
        "Flow Bytes/s": np.random.exponential(10000, n),
        "Flow Packets/s": np.random.exponential(200, n),
        "Flow IAT Mean": np.random.exponential(5, n),
        "Flow IAT Std": np.random.exponential(2, n),
        "Flow IAT Max": np.random.exponential(20, n),
        "Flow IAT Min": np.random.exponential(0.5, n),
        "Fwd IAT Mean": np.random.exponential(5, n),
        "Fwd IAT Std": np.random.exponential(2, n),
        "Fwd IAT Max": np.random.exponential(10, n),
        "Fwd IAT Min": np.random.exponential(0.5, n),
        "Bwd IAT Mean": np.random.exponential(10, n),
        "Bwd IAT Std": np.random.exponential(5, n),
        "Bwd IAT Max": np.random.exponential(20, n),
        "Bwd IAT Min": np.random.exponential(1, n),
        "Fwd Header Length": np.random.poisson(40, n),
        "Bwd Header Length": np.random.poisson(20, n),
        "Fwd Packets/s": np.random.exponential(200, n),
        "Bwd Packets/s": np.random.exponential(50, n),
        "Packet Length Mean": np.random.exponential(50, n) + 40,
        "Packet Length Std": np.random.exponential(10, n),
        "Packet Length Variance": np.random.exponential(100, n),
        "FIN Flag Count": np.zeros(n),
        "SYN Flag Count": np.ones(n),  # always SYN
        "RST Flag Count": np.random.binomial(1, 0.6, n),  # often RST response
        "PSH Flag Count": np.zeros(n),
        "ACK Flag Count": np.random.binomial(1, 0.3, n),
        "URG Flag Count": np.zeros(n),
    }
    df = pd.DataFrame(data)
    df["Label"] = "PortScan"
    return df


def generate_bruteforce(n: int) -> pd.DataFrame:
    """Generate brute force patterns — repeated auth attempts."""
    data = {
        "Flow Duration": np.random.exponential(3000, n),
        "Total Fwd Packets": np.random.poisson(8, n) + 3,
        "Total Backward Packets": np.random.poisson(6, n) + 2,
        "Total Length of Fwd Packets": np.random.exponential(500, n) + 100,
        "Total Length of Bwd Packets": np.random.exponential(300, n) + 50,
        "Fwd Packet Length Max": np.random.exponential(200, n) + 50,
        "Fwd Packet Length Min": np.random.exponential(50, n) + 20,
        "Fwd Packet Length Mean": np.random.exponential(80, n) + 30,
        "Fwd Packet Length Std": np.random.exponential(30, n),
        "Bwd Packet Length Max": np.random.exponential(150, n) + 40,
        "Bwd Packet Length Min": np.random.exponential(30, n) + 20,
        "Bwd Packet Length Mean": np.random.exponential(60, n) + 30,
        "Bwd Packet Length Std": np.random.exponential(25, n),
        "Flow Bytes/s": np.random.exponential(5000, n),
        "Flow Packets/s": np.random.exponential(20, n),
        "Flow IAT Mean": np.random.exponential(200, n) + 50,  # regular intervals
        "Flow IAT Std": np.random.exponential(30, n),  # low variance = automated
        "Flow IAT Max": np.random.exponential(500, n),
        "Flow IAT Min": np.random.exponential(50, n) + 20,
        "Fwd IAT Mean": np.random.exponential(300, n) + 50,
        "Fwd IAT Std": np.random.exponential(40, n),
        "Fwd IAT Max": np.random.exponential(600, n),
        "Fwd IAT Min": np.random.exponential(50, n) + 20,
        "Bwd IAT Mean": np.random.exponential(400, n) + 100,
        "Bwd IAT Std": np.random.exponential(100, n),
        "Bwd IAT Max": np.random.exponential(1000, n),
        "Bwd IAT Min": np.random.exponential(50, n),
        "Fwd Header Length": np.random.poisson(160, n),
        "Bwd Header Length": np.random.poisson(120, n),
        "Fwd Packets/s": np.random.exponential(10, n),
        "Bwd Packets/s": np.random.exponential(8, n),
        "Packet Length Mean": np.random.exponential(70, n) + 30,
        "Packet Length Std": np.random.exponential(30, n),
        "Packet Length Variance": np.random.exponential(1000, n),
        "FIN Flag Count": np.random.binomial(1, 0.3, n),
        "SYN Flag Count": np.random.binomial(1, 0.3, n),
        "RST Flag Count": np.random.binomial(1, 0.4, n),  # many resets (failed auth)
        "PSH Flag Count": np.random.binomial(3, 0.6, n),
        "ACK Flag Count": np.random.poisson(5, n),
        "URG Flag Count": np.zeros(n),
    }
    df = pd.DataFrame(data)
    df["Label"] = "BruteForce"
    return df


def generate_webattack(n: int) -> pd.DataFrame:
    """Generate web attack patterns — SQL injection, XSS."""
    data = {
        "Flow Duration": np.random.exponential(8000, n),
        "Total Fwd Packets": np.random.poisson(20, n) + 5,
        "Total Backward Packets": np.random.poisson(15, n) + 3,
        "Total Length of Fwd Packets": np.random.exponential(3000, n) + 500,  # larger payloads
        "Total Length of Bwd Packets": np.random.exponential(8000, n),
        "Fwd Packet Length Max": np.random.exponential(1500, n) + 200,  # large payload for injection
        "Fwd Packet Length Min": np.random.exponential(40, n),
        "Fwd Packet Length Mean": np.random.exponential(300, n) + 50,
        "Fwd Packet Length Std": np.random.exponential(200, n),  # high variance
        "Bwd Packet Length Max": np.random.exponential(2000, n),
        "Bwd Packet Length Min": np.random.exponential(40, n),
        "Bwd Packet Length Mean": np.random.exponential(500, n),
        "Bwd Packet Length Std": np.random.exponential(300, n),
        "Flow Bytes/s": np.random.exponential(20000, n),
        "Flow Packets/s": np.random.exponential(50, n),
        "Flow IAT Mean": np.random.exponential(400, n),
        "Flow IAT Std": np.random.exponential(300, n),
        "Flow IAT Max": np.random.exponential(3000, n),
        "Flow IAT Min": np.random.exponential(10, n),
        "Fwd IAT Mean": np.random.exponential(500, n),
        "Fwd IAT Std": np.random.exponential(400, n),
        "Fwd IAT Max": np.random.exponential(3000, n),
        "Fwd IAT Min": np.random.exponential(20, n),
        "Bwd IAT Mean": np.random.exponential(600, n),
        "Bwd IAT Std": np.random.exponential(400, n),
        "Bwd IAT Max": np.random.exponential(4000, n),
        "Bwd IAT Min": np.random.exponential(30, n),
        "Fwd Header Length": np.random.poisson(400, n),  # more headers
        "Bwd Header Length": np.random.poisson(300, n),
        "Fwd Packets/s": np.random.exponential(30, n),
        "Bwd Packets/s": np.random.exponential(20, n),
        "Packet Length Mean": np.random.exponential(350, n),
        "Packet Length Std": np.random.exponential(250, n),
        "Packet Length Variance": np.random.exponential(60000, n),
        "FIN Flag Count": np.random.binomial(1, 0.2, n),
        "SYN Flag Count": np.random.binomial(1, 0.15, n),
        "RST Flag Count": np.random.binomial(1, 0.05, n),
        "PSH Flag Count": np.random.binomial(5, 0.7, n),  # lots of PSH (data transfer)
        "ACK Flag Count": np.random.poisson(12, n),
        "URG Flag Count": np.random.binomial(1, 0.05, n),
    }
    df = pd.DataFrame(data)
    df["Label"] = "WebAttack"
    return df


def generate_botnet(n: int) -> pd.DataFrame:
    """Generate botnet C&C communication patterns."""
    data = {
        "Flow Duration": np.random.exponential(30000, n) + 5000,  # long-lived
        "Total Fwd Packets": np.random.poisson(5, n) + 1,  # periodic beacons
        "Total Backward Packets": np.random.poisson(3, n) + 1,
        "Total Length of Fwd Packets": np.random.exponential(200, n) + 50,
        "Total Length of Bwd Packets": np.random.exponential(500, n),
        "Fwd Packet Length Max": np.random.exponential(150, n) + 50,
        "Fwd Packet Length Min": np.random.exponential(40, n) + 20,
        "Fwd Packet Length Mean": np.random.exponential(70, n) + 30,
        "Fwd Packet Length Std": np.random.exponential(15, n),  # very uniform = beacon
        "Bwd Packet Length Max": np.random.exponential(300, n),
        "Bwd Packet Length Min": np.random.exponential(40, n),
        "Bwd Packet Length Mean": np.random.exponential(100, n),
        "Bwd Packet Length Std": np.random.exponential(50, n),
        "Flow Bytes/s": np.random.exponential(500, n),  # low bandwidth
        "Flow Packets/s": np.random.exponential(2, n),  # low rate
        "Flow IAT Mean": np.random.exponential(10000, n) + 5000,  # regular intervals
        "Flow IAT Std": np.random.exponential(500, n),  # very low variance = beacon
        "Flow IAT Max": np.random.exponential(15000, n),
        "Flow IAT Min": np.random.exponential(5000, n),
        "Fwd IAT Mean": np.random.exponential(15000, n) + 5000,
        "Fwd IAT Std": np.random.exponential(1000, n),
        "Fwd IAT Max": np.random.exponential(20000, n),
        "Fwd IAT Min": np.random.exponential(5000, n),
        "Bwd IAT Mean": np.random.exponential(20000, n),
        "Bwd IAT Std": np.random.exponential(5000, n),
        "Bwd IAT Max": np.random.exponential(30000, n),
        "Bwd IAT Min": np.random.exponential(5000, n),
        "Fwd Header Length": np.random.poisson(100, n),
        "Bwd Header Length": np.random.poisson(80, n),
        "Fwd Packets/s": np.random.exponential(1, n),
        "Bwd Packets/s": np.random.exponential(0.5, n),
        "Packet Length Mean": np.random.exponential(70, n) + 30,
        "Packet Length Std": np.random.exponential(20, n),
        "Packet Length Variance": np.random.exponential(500, n),
        "FIN Flag Count": np.random.binomial(1, 0.1, n),
        "SYN Flag Count": np.random.binomial(1, 0.1, n),
        "RST Flag Count": np.random.binomial(1, 0.02, n),
        "PSH Flag Count": np.random.binomial(2, 0.5, n),
        "ACK Flag Count": np.random.poisson(3, n),
        "URG Flag Count": np.zeros(n),
    }
    df = pd.DataFrame(data)
    df["Label"] = "Botnet"
    return df


def generate_infiltration(n: int) -> pd.DataFrame:
    """Generate infiltration/data exfiltration patterns."""
    data = {
        "Flow Duration": np.random.exponential(20000, n) + 3000,
        "Total Fwd Packets": np.random.poisson(30, n) + 5,  # bulk data transfer
        "Total Backward Packets": np.random.poisson(8, n) + 1,
        "Total Length of Fwd Packets": np.random.exponential(50000, n) + 5000,  # large outbound
        "Total Length of Bwd Packets": np.random.exponential(1000, n),
        "Fwd Packet Length Max": np.random.exponential(1460, n) + 500,  # near MTU
        "Fwd Packet Length Min": np.random.exponential(100, n),
        "Fwd Packet Length Mean": np.random.exponential(1000, n) + 200,
        "Fwd Packet Length Std": np.random.exponential(300, n),
        "Bwd Packet Length Max": np.random.exponential(200, n),
        "Bwd Packet Length Min": np.random.exponential(40, n),
        "Bwd Packet Length Mean": np.random.exponential(80, n),
        "Bwd Packet Length Std": np.random.exponential(40, n),
        "Flow Bytes/s": np.random.exponential(100000, n),
        "Flow Packets/s": np.random.exponential(30, n),
        "Flow IAT Mean": np.random.exponential(500, n),
        "Flow IAT Std": np.random.exponential(200, n),
        "Flow IAT Max": np.random.exponential(3000, n),
        "Flow IAT Min": np.random.exponential(5, n),
        "Fwd IAT Mean": np.random.exponential(400, n),
        "Fwd IAT Std": np.random.exponential(150, n),
        "Fwd IAT Max": np.random.exponential(2000, n),
        "Fwd IAT Min": np.random.exponential(2, n),
        "Bwd IAT Mean": np.random.exponential(2000, n),
        "Bwd IAT Std": np.random.exponential(1000, n),
        "Bwd IAT Max": np.random.exponential(5000, n),
        "Bwd IAT Min": np.random.exponential(100, n),
        "Fwd Header Length": np.random.poisson(600, n),
        "Bwd Header Length": np.random.poisson(160, n),
        "Fwd Packets/s": np.random.exponential(25, n),
        "Bwd Packets/s": np.random.exponential(5, n),
        "Packet Length Mean": np.random.exponential(800, n) + 100,
        "Packet Length Std": np.random.exponential(400, n),
        "Packet Length Variance": np.random.exponential(150000, n),
        "FIN Flag Count": np.random.binomial(1, 0.15, n),
        "SYN Flag Count": np.random.binomial(1, 0.1, n),
        "RST Flag Count": np.random.binomial(1, 0.03, n),
        "PSH Flag Count": np.random.binomial(4, 0.7, n),
        "ACK Flag Count": np.random.poisson(15, n),
        "URG Flag Count": np.random.binomial(1, 0.02, n),
    }
    df = pd.DataFrame(data)
    df["Label"] = "Infiltration"
    return df


def main():
    output_dir = os.path.join(os.path.dirname(__file__), "cicids2017")
    os.makedirs(output_dir, exist_ok=True)

    print("Generating synthetic CICIDS2017 training data...")

    # Class distribution (similar to real CICIDS2017 ratios)
    samples = {
        "BENIGN": 50000,
        "DoS": 8000,
        "DDoS": 5000,
        "PortScan": 5000,
        "BruteForce": 3000,
        "WebAttack": 2000,
        "Botnet": 1500,
        "Infiltration": 1000,
    }

    generators = {
        "BENIGN": generate_benign,
        "DoS": generate_dos,
        "DDoS": generate_ddos,
        "PortScan": generate_portscan,
        "BruteForce": generate_bruteforce,
        "WebAttack": generate_webattack,
        "Botnet": generate_botnet,
        "Infiltration": generate_infiltration,
    }

    all_data = []
    for label, n in samples.items():
        print(f"  Generating {n:>6} {label} samples...")
        df = generators[label](n)
        all_data.append(df)

    combined = pd.concat(all_data, ignore_index=True)
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle

    # Ensure no negative values
    for col in FEATURE_COLUMNS:
        combined[col] = combined[col].clip(lower=0)

    output_path = os.path.join(output_dir, "training_data.csv")
    combined.to_csv(output_path, index=False)

    print(f"\nGenerated {len(combined)} total samples")
    print(f"Saved to: {output_path}")
    print(f"\nClass distribution:")
    print(combined["Label"].value_counts().to_string())


if __name__ == "__main__":
    main()

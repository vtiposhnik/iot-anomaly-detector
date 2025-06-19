"""Model Evaluation Script

Loads a sample of traffic data from the local SQLite database and runs the
anomaly detection models to evaluate them. Detected anomalies along with the
methods that flagged them and relevant information are printed to the console.
"""

import os
import sys

# Ensure the server2 package is on the path when running directly
CURRENT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import pandas as pd
from ml.anomaly_detector import detect_anomalies
from utils.database import get_db_connection


def evaluate(limit: int = 200, threshold: float = 0.7, model: str = "both") -> None:
    """Evaluate the anomaly detection models.

    Parameters
    ----------
    limit : int
        Number of traffic records to analyse.
    threshold : float
        Threshold to use when determining anomalies.
    model : str
        Which model to use: 'isolation_forest', 'lof', or 'both'.
    """
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM traffic LIMIT ?", conn, params=(limit,))
    conn.close()

    anomalies = detect_anomalies(df.to_dict(orient="records"))

    if not anomalies:
        print("No anomalies detected.")
        return

    print(f"Detected {len(anomalies)} anomalies:\n")
    for row in anomalies:
        methods = []
        if model in ("isolation_forest", "both") and any(
            algo == "Isolation Forest" for algo in row.get("anomaly_type", [])
        ):
            methods.append("Isolation Forest")
        if model in ("lof", "both") and any(
            algo == "Local Outlier Factor" for algo in row.get("anomaly_type", [])
        ):
            methods.append("Local Outlier Factor")
        score = row.get("confidence", 0.0)
        print(
            f"[{row['timestamp']}] Device {row['device_id']} src={row.get('src_ip','N/A')} -> {row.get('dst_ip','N/A')} | "
            f"Score: {score:.3f} | Methods: {', '.join(methods)}"
        )


if __name__ == "__main__":
    evaluate()

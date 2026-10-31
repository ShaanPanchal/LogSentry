"""The feature transform the A2 anomaly clusters were fitted on.

In A2, K-means grouped the anomalous sessions into kinds of failure. The fitted scaler, K-means model and a
plain English description of each cluster are saved in models/<SOURCE>_clusters.joblib. The training code
that produced them is kept on the a2-backup branch; A3 only applies the saved model to new sessions.
"""
import mkl_setup  # noqa: F401  (Windows MKL fix, must come before numpy)
import numpy as np


# Counts and durations have a few huge values. log1p shrinks them, and np.sign keeps negative values
# (replica_deficit can be negative). The saved cluster scaler was fitted on this transform.
def signed_log(X):
    """log1p that keeps the sign, so very large values are shrunk."""
    return np.sign(X) * np.log1p(np.abs(X))

"""The one place that imports the Assignment 2 pipeline from src/.

The A2 modules use flat imports (`from features import ...`), so src/ goes on sys.path. src/ keeps only
the parts of the A2 pipeline used here, unchanged in behaviour; the A2 training code is on the a2-backup
branch. `mkl_setup` has to be imported before numpy (it is a no-op off Windows/conda).
"""
import sys

from .config import A2_SRC

if str(A2_SRC) not in sys.path:
    sys.path.insert(0, str(A2_SRC))

import mkl_setup  # noqa: F401,E402  (must come before numpy)
from clustering import signed_log  # noqa: E402  (feature transform the cluster scaler was fitted on)
from features import STRUCTURAL_COLS  # noqa: E402  (the 20 non-bucket feature names)
from processing import process  # noqa: E402  (parse -> sessions -> 52 features, same code as training)

__all__ = ['process', 'signed_log', 'STRUCTURAL_COLS']

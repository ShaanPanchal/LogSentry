# Import the A2 bridge first: it puts a2_pipeline/ on sys.path and applies the MKL setting before numpy is imported.
from . import a2  # noqa: F401

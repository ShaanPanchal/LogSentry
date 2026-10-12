# Import the A2 bridge first: it puts src/ on sys.path and applies the MKL setting before numpy is imported.
from . import a2  # noqa: F401

"""Windows fix for the conda-forge MKL crash. Import this before numpy, pandas or scikit-learn.

On Windows, the conda-forge build of NumPy uses Intel MKL. MKL's default threading layer needs
libiomp5md.dll, but in this environment that file comes from the llvm-openmp package, which is
missing functions MKL expects. The first MKL call (for example K-Means or logistic regression)
then crashes with "OSError 0xc06d007f".

MKL's TBB threading layer does not use that file and works, so we select it here. The variable
is read when MKL is first loaded, so this module must be imported before numpy.
An existing MKL_THREADING_LAYER value is never overwritten. Other systems are left unchanged.
"""
import os
import sys
import warnings

if sys.platform == 'win32':
    if 'numpy' in sys.modules and 'MKL_THREADING_LAYER' not in os.environ:
        warnings.warn('mkl_setup was imported after numpy, so the MKL fix may be too late.')
    os.environ.setdefault('MKL_THREADING_LAYER', 'TBB')

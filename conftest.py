import os
import sys

# Make sure the eval_harness package is importable regardless of how/where
# pytest is invoked from.
sys.path.insert(0, os.path.dirname(__file__))

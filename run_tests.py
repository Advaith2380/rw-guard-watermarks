"""Automated Test Suite Runner for RW-Guard (Review Requirement REQ-X).

Discovers and executes all unit tests under tests/ directory.
Produces human-readable summary and exits with code 0 on pass, 1 on fail.
"""

import unittest
import sys
import os

if __name__ == "__main__":
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), "tests")
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    sys.exit(0 if result.wasSuccessful() else 1)

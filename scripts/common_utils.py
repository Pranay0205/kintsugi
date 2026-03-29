"""Common utilities and constants for annotation data scripts."""

import os

# Default output directory for all annotation-related files
DEFAULT_OUTPUT_DIR = "results/annotation_tool"


def ensure_output_dir(data_dir=DEFAULT_OUTPUT_DIR):
    """Ensure the output directory exists."""
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

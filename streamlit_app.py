import sys
from pathlib import Path

# Add src to path so Streamlit Cloud can import the package
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pdf_converse.web_app import *

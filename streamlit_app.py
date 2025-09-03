"""
Redirect file for Streamlit Cloud deployment
Points to the actual main app file
"""

import sys
from pathlib import Path

# Add streamlit_app directory to path
sys.path.append(str(Path(__file__).parent / "streamlit_app"))

# Import and run the main app
from streamlit_app.main import main

if __name__ == "__main__":
    main()
# IHRGV Project

This project is a data analysis and visualization dashboard built with Streamlit and Python. It processes and visualizes census data for various Indian states and union territories, with a focus on social and demographic insights.

## Project Structure


```
streamlit_dashboard.py           # Main Streamlit dashboard script
modules/
   utils.py                    # Utility functions
   __pycache__/                # Python cache files
   *.csv                       # Census data files for various states
```

## Getting Started

- Python 3.8+
- pip
- (Recommended) Virtual environment
### Installation
1. Clone the repository:
   ```sh
   git clone <repo-url>
   cd IHRGV
2. Create and activate a virtual environment:
   ```sh
   python -m venv venv
   venv\Scripts\activate
   # On Unix/Mac
   source venv/bin/activate
   ```
   ```sh
   pip install -r requirements.txt
   ```


### Running the Dashboard
To start the Streamlit dashboard:
```sh
streamlit run streamlit_dashboard.py
```

## Data
The `data/` folder contains census CSV files for different Indian states and union territories. These are used for analysis and visualization in the dashboard.

## License
[MIT](LICENSE)

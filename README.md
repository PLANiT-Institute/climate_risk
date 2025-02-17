Overview
This repository hosts a Python-based tool for assessing climate-related financial risks. The tool calculates:

Transition Risk:

Models a linear reduction of emission allowances (2025–2050).
Calculates carbon costs under different scenarios (e.g., NDC).
Net-Zero Pathway:

Creates emission reduction trajectories (linear or absolute contraction) from a baseline year to net-zero by 2050.
Physical Risk (Placeholder):

Intended to integrate with CLIMADA for hazard-based damage estimates.
Currently not producing outputs.
Climate Value at Risk (VaR):

Performs a simplified Monte Carlo simulation combining transition and net-zero data.
Outputs a 95% (or chosen percentile) VaR estimate based on uncertain carbon prices and penalty factors.
Features
Excel-based Inputs: Reads baseline emissions, carbon prices, and optional allowance rates directly from .xlsx files.
Configurable: Easily switch between scenarios (NDC, Below2, etc.).
Modular Code: Each risk model has its own class within util/ (transition_risk, net_zero, climate_var, physical_risk).
Extendable: You can plug in real hazard data to the physical_risk module once CLIMADA integration is set up.
Folder Structure
sql
Copy
Edit
climate_risk/
  ├─ data/
  │   └─ input_facilities.xlsx          <-- Example file with baseline emissions
  ├─ outputs/                           <-- Model outputs (CSV, XLSX) get saved here
  ├─ util/
  │   ├─ climate_var.py                <-- Climate VaR class
  │   ├─ net_zero.py                   <-- Net-zero calculation class
  │   ├─ physical_risk.py              <-- Placeholder for CLIMADA integration
  │   └─ transition_risk.py            <-- Transition risk (ETS logic)
  ├─ LICENSE
  ├─ main.py                           <-- Orchestrator script
  └─ README.md                         <-- This file
Key Files
util/transition_risk.py

Loads facility data and computes carbon costs based on linear allowance reduction.
util/net_zero.py

Models emission reduction targets from baseline to net-zero by 2050.
util/climate_var.py

Runs a Monte Carlo simulation to estimate the potential tail risk (VaR).
util/physical_risk.py

Placeholder class for physical risk. Future integration with CLIMADA is planned.
main.py

Orchestrates the workflow. Calls the above modules in sequence and saves results to outputs/.
Installation
Clone this repository:
bash
Copy
Edit
git clone https://github.com/username/climate_risk.git
Change into the directory:
bash
Copy
Edit
cd climate_risk
Install required Python libraries:
bash
Copy
Edit
pip install -r requirements.txt
This should include packages like pandas, numpy, openpyxl (for Excel files), and possibly scipy if you use advanced Monte Carlo distributions.
Note: If you plan on eventually integrating CLIMADA, you will also need:

bash
Copy
Edit
pip install git+https://github.com/CLIMADA-project/climada_python.git
Usage
Prepare Data

By default, the tool looks for data/input_facilities.xlsx.
Make sure you have the necessary columns (e.g., facility_id, baseline_emissions_2024).
Optionally add carbon_prices.xlsx or other scenario data if you customize the code.
Run the Main Script

bash
Copy
Edit
python main.py
This will execute transition_risk, physical_risk (placeholder), net_zero, and climate_var in sequence.
Results are saved in the outputs/ folder:
transition_risk_results.csv
netzero_pathway_results.csv
climate_var_distribution.csv (distribution from Monte Carlo)

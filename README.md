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

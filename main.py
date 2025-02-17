# main.py

import os
from util.transition_risk import TransitionRisk
from util.net_zero import NetZeroPathway
from util.climate_var import ClimateVaR
from util.physical_risk import PhysicalRisk

def main():
    # 1. Transition
    tr = TransitionRisk(facilities_path="data/input_facilities.xlsx", scenario="NDC")
    transition_df = tr.run()
    tr.save_results("outputs/transition_risk_results.csv")

    # 2. Physical (placeholder)
    pr = PhysicalRisk()
    phys_results = pr.run()
    # No results to save yet

    # 3. Net-zero
    nz = NetZeroPathway(facilities_path="data/input_facilities.xlsx", approach='linear')
    netzero_df = nz.run()
    nz.save_results("outputs/netzero_pathway_results.csv")

    # 4. VaR
    cvar = ClimateVaR(transition_df, netzero_df)
    var_95, sim_dist = cvar.run_monte_carlo(n_sim=1000, percentile=0.95)
    print(f"Climate VaR (95%): {var_95}")

    # For example, save the distribution:
    import pandas as pd
    df_sims = pd.DataFrame({"simulation_total_cost": sim_dist})
    df_sims.to_csv("outputs/climate_var_distribution.csv", index=False)

if __name__ == "__main__":
    main()

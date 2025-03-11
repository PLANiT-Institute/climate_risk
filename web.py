import streamlit as st
import pandas as pd
from climate_risk_tool.transition_risk import TransitionRisk
import matplotlib.pyplot as plt

st.title("Climate Financial Risk Tool: Transition Risk Analysis")

# File upload
st.header("Upload Input Files")
facilities_file = st.file_uploader("Facilities Data (Excel)", type=["xlsx"])
carbon_price_file = st.file_uploader("Carbon Price Data (Excel)", type=["xlsx"])

# Scenario selection
scenario = st.selectbox("Select Scenario", ["NDC", "Below 2", "Net-zero"], index=0)

if facilities_file and carbon_price_file:
    # Load uploaded files into DataFrames
    facilities_df = pd.read_excel(facilities_file)
    carbon_price_df = pd.read_excel(carbon_price_file)

    # Validate required columns
    required_cols_fac = ['facility_id', 'baseline_emissions_2024']
    required_cols_price = ['year', 'scenario', 'price_usd_per_tCO2e']
    if not all(col in facilities_df.columns for col in required_cols_fac):
        st.error("Facilities file missing required columns: " + ", ".join(required_cols_fac))
    elif not all(col in carbon_price_df.columns for col in required_cols_price):
        st.error("Carbon price file missing required columns: " + ", ".join(required_cols_price))
    else:
        # Run Transition Risk analysis
        tr = TransitionRisk(facilities_file, carbon_price_file, scenario)
        results = tr.run()

        # Display results
        st.header("Transition Risk Results")
        st.dataframe(results)

        # Visualization
        st.header("Cost Over Time")
        fig, ax = plt.subplots()
        for fac_id in results['facility_id'].unique():
            fac_data = results[results['facility_id'] == fac_id]
            ax.plot(fac_data['year'], fac_data['ets_cost'], label=fac_id)
        ax.set_xlabel("Year")
        ax.set_ylabel("ETS Cost (USD)")
        ax.legend()
        st.pyplot(fig)

else:
    st.warning("Please upload both facilities and carbon price files to proceed.")
import streamlit as st
import pandas as pd

# -------------------------------
# Sow Rotation Simulator
# -------------------------------
def sow_rotation_simulator(
    total_sows=30,
    piglets_per_cycle=8,
    piglet_mortality=0.03,
    abortion_rate=0.00,
    sow_feed_price=32,
    sow_feed_intake=2.8,
    grower_feed_price=28,
    fcr=3.1,
    sale_price=130,
    sow_cost=25000,
    shed_cost=500000,
    medicines_cost=5000,
    simulation_months=12
):
    monthly_records = []
    cumulative_cash_flow = 0

    for month in range(1, simulation_months + 1):
        # --- Breeding & Piglet production ---
        sows_crossed = int(round(total_sows / 5.5))   # approx monthly cycles
        piglets_born = sows_crossed * piglets_per_cycle
        piglets_born_alive = int(round(piglets_born * (1 - abortion_rate)))
        growers = int(round(piglets_born_alive * (1 - piglet_mortality)))
        sold_pigs = int(round(growers * 0.9))  # assume 90% reach sale stage

        # --- Economics ---
        revenue = sold_pigs * 100 * sale_price   # assume 100 kg market weight
        feed_cost_sow = total_sows * sow_feed_intake * 30 * sow_feed_price
        feed_cost_grower = sold_pigs * fcr * 100 * grower_feed_price
        other_costs = medicines_cost  # only medicines, no land/electricity
        total_operating_cost = feed_cost_sow + feed_cost_grower + other_costs

        monthly_profit = revenue - total_operating_cost
        cumulative_cash_flow += monthly_profit

        monthly_records.append({
            "Month": month,
            "Sows_Crossed": sows_crossed,
            "Piglets_Born_Alive": piglets_born_alive,
            "Growers": growers,
            "Sold_Pigs": sold_pigs,
            "Revenue": revenue,
            "Total_Operating_Cost": total_operating_cost,
            "Monthly_Profit": monthly_profit,
            "Cumulative_Cash_Flow": cumulative_cash_flow
        })

    # Build DataFrames
    df_month = pd.DataFrame(monthly_records)

    df_year = pd.DataFrame([{
        "Total_Crossings": df_month["Sows_Crossed"].sum(),
        "Piglets_Born_Alive": df_month["Piglets_Born_Alive"].sum(),
        "Sold_Pigs": df_month["Sold_Pigs"].sum(),
        "Revenue": df_month["Revenue"].sum(),
        "Total_Operating_Cost": df_month["Total_Operating_Cost"].sum(),
        "Profit": df_month["Monthly_Profit"].sum()   # plain profit, no dep
    }])

    return df_month, df_year

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("🐷 House of Supreme Ham Farm Simulator")

st.sidebar.header("Simulation Parameters")
total_sows = st.sidebar.number_input("Total Sows", 10, 1000, 30)
piglets_per_cycle = st.sidebar.number_input("Piglets per Cycle", 5, 20, 8)
piglet_mortality = st.sidebar.slider("Piglet Mortality (%)", 0, 100, 3) / 100
sow_feed_price = st.sidebar.number_input("Sow Feed Price (₹/kg)", 1, 100, 32)
sow_feed_intake = st.sidebar.number_input("Sow Feed Intake (kg/day)", 1.0, 10.0, 2.8)
grower_feed_price = st.sidebar.number_input("Grower Feed Price (₹/kg)", 1, 100, 28)
sale_price = st.sidebar.number_input("Sale Price (₹/kg)", 50, 500, 130)
shed_cost = st.sidebar.number_input("Shed Cost", 0, 5000000, 500000)
sow_cost = st.sidebar.number_input("Sow Cost (per sow)", 0, 100000, 25000)
medicines_cost = st.sidebar.number_input("Medicine Cost (Monthly)", 0, 50000, 5000)
simulation_months = st.sidebar.number_input("Simulation Duration (Months)", 1, 60, 12)

# Run simulation
df_month, df_year = sow_rotation_simulator(
    total_sows=total_sows,
    piglets_per_cycle=piglets_per_cycle,
    piglet_mortality=piglet_mortality,
    sow_feed_price=sow_feed_price,
    sow_feed_intake=sow_feed_intake,
    grower_feed_price=grower_feed_price,
    sale_price=sale_price,
    sow_cost=sow_cost,
    shed_cost=shed_cost,
    medicines_cost=medicines_cost,
    simulation_months=simulation_months
)

# Ensure whole numbers for pig counts
for col in ['Sows_Crossed', 'Piglets_Born_Alive', 'Growers', 'Sold_Pigs']:
    if col in df_month.columns:
        df_month[col] = df_month[col].round(0).astype(int)
    if col in df_year.columns:
        df_year[col] = df_year[col].round(0).astype(int)

# --- Monthly Summary ---
st.subheader("Monthly Summary")
cols_to_show = [
    'Month',
    'Sows_Crossed',
    'Piglets_Born_Alive',
    'Sold_Pigs',
    'Revenue',
    'Total_Operating_Cost',
    'Monthly_Profit',
    'Cumulative_Cash_Flow'
]
st.dataframe(df_month[[c for c in cols_to_show if c in df_month.columns]])

# --- Yearly Summary ---
st.subheader("Yearly Summary")
cols_to_show_year = [
    'Total_Crossings',
    'Piglets_Born_Alive',
    'Sold_Pigs',
    'Revenue',
    'Total_Operating_Cost',
    'Profit'
]
st.dataframe(df_year[[c for c in cols_to_show_year if c in df_year.columns]])


# -------------------------------
# House of Supreme Ham Simulator
# Complete Streamlit App
# -------------------------------

import streamlit as st
import pandas as pd
import math
import altair as alt

# -------------------------------
# Sow Rotation Simulator Function
# -------------------------------
def sow_rotation_simulator(
    total_sows=30,
    piglets_per_cycle=10,
    piglet_mortality=0.07,
    abortion_rate=0.0,
    sow_feed_price=30,
    sow_feed_intake=2.8,
    grower_feed_price=30,
    fcr=3.1,
    final_weight=105,
    sale_price=180,
    management_fee=0,
    management_commission=0.0,
    supervisor_salary=25000,
    worker_salary=18000,
    n_workers=2,
    shed_cost=1_500_000,
    shed_life_years=10,
    sow_cost=35000,
    sow_life_years=4,
    loan_amount=4_000_000,
    interest_rate=0.121,
    loan_tenure_years=5,
    moratorium_months=0,
    medicine_cost=10000,
    electricity_cost=5000,
    land_lease=10000,
    months=60
):
    # ----- Setup -----
    current_sows = total_sows
    monthly_data = []
    total_months = loan_tenure_years * 12
    monthly_rate = interest_rate / 12
    emi = loan_amount * monthly_rate * (1 + monthly_rate) ** total_months / ((1 + monthly_rate) ** total_months - 1) if loan_amount > 0 else 0
    loan_balance = loan_amount

    shed_dep_rate = 1 / (shed_life_years * 12)
    sow_dep_rate = 1 / (sow_life_years * 12)

    average_cycle_length = 3.8 + 1.3 + 0.33
    sows_to_mate_per_month = total_sows / average_cycle_length

    batches = []
    ready_for_sale_batches = []

    total_sow_cost = sow_cost * total_sows
    total_pigs_born = 0
    total_pigs_sold = 0
    first_sale_cash_needed = 0
    first_sale_done = False

    # ----- Monthly Simulation -----
    for month in range(1, months + 1):
        sow_feed_cost = current_sows * sow_feed_intake * 30 * sow_feed_price
        staff_cost = supervisor_salary + n_workers * worker_salary
        mgmt_fixed = management_fee

        sows_crossed = 0
        if month >= 2:
            sows_to_mate = sows_to_mate_per_month
            sows_pregnant = sows_to_mate * (1 - abortion_rate)
            sows_crossed = sows_to_mate
            if sows_pregnant > 0:
                farrow_month = month + 4
                wean_month = farrow_month + 1
                grower_start_month = wean_month
                grower_end_month = grower_start_month + 6
                piglets = sows_pregnant * piglets_per_cycle * (1 - piglet_mortality)
                total_pigs_born += piglets
                batches.append({
                    'batch_id': len(batches) + 1,
                    'farrow_month': farrow_month,
                    'wean_month': wean_month,
                    'grower_start_month': grower_start_month,
                    'grower_end_month': grower_end_month,
                    'piglets': piglets,
                    'grower_feed_per_month': (piglets * fcr * final_weight) / 6,
                    'sold': False
                })

        piglets_with_sow = sum(batch['piglets'] for batch in batches if batch['farrow_month'] <= month < batch['wean_month'])
        current_growers = sum(batch['piglets'] for batch in batches if batch['grower_start_month'] <= month < batch['grower_end_month'])
        grower_feed_cost = sum(batch['grower_feed_per_month'] * grower_feed_price for batch in batches if batch['grower_start_month'] <= month < batch['grower_end_month'])

        # Sale ready batches
        for batch in batches:
            if batch['grower_end_month'] <= month and not batch['sold'] and batch not in ready_for_sale_batches:
                ready_for_sale_batches.append(batch)

        sold_pigs = 0
        revenue = 0
        if ready_for_sale_batches:
            pigs_sold_this_month = sum(batch['piglets'] for batch in ready_for_sale_batches)
            revenue += pigs_sold_this_month * final_weight * sale_price
            sold_pigs = pigs_sold_this_month
            total_pigs_sold += sold_pigs
            current_growers -= sold_pigs
            for batch in ready_for_sale_batches:
                batch['sold'] = True
            ready_for_sale_batches = []

        # First sale working capital
        if not first_sale_done:
            first_sale_cash_needed += sow_feed_cost + grower_feed_cost + staff_cost + mgmt_fixed + medicine_cost + electricity_cost + land_lease
        if sold_pigs > 0 and not first_sale_done:
            first_sale_done = True

        mgmt_comm_cost = revenue * management_commission
        other_fixed = medicine_cost + electricity_cost + land_lease
        total_operating_cost = sow_feed_cost + grower_feed_cost + staff_cost + mgmt_fixed + mgmt_comm_cost + other_fixed
        dep = shed_cost * shed_dep_rate + total_sow_cost * sow_dep_rate

        if month <= moratorium_months:
            loan_payment = loan_balance * monthly_rate
        elif month <= total_months:
            interest = loan_balance * monthly_rate
            principal = emi - interest
            loan_balance -= principal
            loan_payment = emi
        else:
            loan_payment = 0

        monthly_profit = revenue - total_operating_cost
        monthly_cash_flow = revenue - total_operating_cost - loan_payment

        monthly_data.append({
            'Month': month,
            'Sows_Crossed': round(sows_crossed),
            'Piglets_Born_Alive': round(piglets_with_sow),
            'Growers': round(current_growers),
            'Sold_Pigs': round(sold_pigs),
            'Sow_Feed_Cost': round(sow_feed_cost),
            'Grower_Feed_Cost': round(grower_feed_cost),
            'Staff_Cost': round(staff_cost),
            'Other_Fixed_Costs': round(other_fixed),
            'Mgmt_Fee': round(mgmt_fixed),
            'Mgmt_Comm': round(mgmt_comm_cost),
            'Total_Operating_Cost': round(total_operating_cost),
            'Revenue': round(revenue),
            'Monthly_Profit': round(monthly_profit),
            'Loan_EMI': round(loan_payment),
            'Monthly_Cash_Flow': round(monthly_cash_flow),
            'Depreciation': round(dep)
        })

    df_month = pd.DataFrame(monthly_data)
    df_year = df_month.groupby(((df_month['Month']-1)//12)*12).sum()
    df_year.index = [f"Year {i+1}" for i in range(len(df_year))]

    animals_left = int(sum(batch['piglets'] for batch in batches if not batch['sold'] and batch['grower_end_month'] > months))

    # ----- Cumulative Cash Flow (corrected) -----
    initial_investment = shed_cost + total_sow_cost + first_sale_cash_needed
    cumulative_cash_flow = [-initial_investment]
    for val in df_month["Monthly_Cash_Flow"]:
        cumulative_cash_flow.append(cumulative_cash_flow[-1] + val)
    cumulative_cash_flow = cumulative_cash_flow[1:]
    df_month["Cumulative_Cash_Flow"] = cumulative_cash_flow

    # ----- ROI & CAGR -----
    total_cash_returned = df_month["Monthly_Cash_Flow"].sum() + initial_investment
    roi_cash_pct = (total_cash_returned / initial_investment - 1) * 100
    years = months / 12
    realized_cagr = ((total_cash_returned) / initial_investment) ** (1 / years) - 1

    # ROI including assets
    piglet_price = sale_price * final_weight
    roi_with_assets_pct = (
        df_month['Cumulative_Cash_Flow'].iloc[-1]
        + shed_cost * (1 - months / (shed_life_years * 12))
        + total_sow_cost * (1 - months / (sow_life_years * 12))
        + animals_left * piglet_price
    ) / initial_investment * 100

    # ----- Break-even & Profit -----
    break_even_month = None
    running_cash = -initial_investment
    for i, cash in enumerate(df_month["Monthly_Cash_Flow"]):
        running_cash += cash
        if running_cash >= 0:
            break_even_month = i + 1
            break

    profit_after_break_even = df_month["Monthly_Cash_Flow"].iloc[break_even_month:].sum() if break_even_month else 0
    
    average_monthly_profit = df_month["Monthly_Cash_Flow"].mean()

    # Average Profit After Break-even
    if break_even_month and break_even_month < len(df_month):
        profit_after_breakeven = df_month.loc[break_even_month:, "Monthly_Profit"].sum()
        months_after_breakeven = len(df_month) - break_even_month
        avg_profit_after_breakeven = profit_after_breakeven / months_after_breakeven if months_after_breakeven > 0 else 0
    else:
        avg_profit_after_breakeven = 0

    total_crossings = df_month["Sows_Crossed"].sum() if "Sows_Crossed" in df_month.columns else 0

    # Total Interest Paid
    total_interest_paid = df_month["Loan_EMI"].sum() - loan_amount if loan_amount > 0 else 0

    return (
        df_month,
        df_year,
        total_sow_cost,
        shed_cost,
        first_sale_cash_needed,
        total_pigs_sold,
        total_pigs_born,
        animals_left,
        cumulative_cash_flow[-1],
        total_interest_paid,
        break_even_month,
        profit_after_break_even,
        average_monthly_profit,
        avg_profit_after_breakeven,
        total_crossings,
        roi_with_assets_pct,
        roi_cash_pct,
        realized_cagr
    )

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(layout="wide", page_title="House of Supreme Ham Simulator")
st.title("🐷 House of Supreme Ham Simulator")

st.sidebar.header("Adjust Simulation Parameters")

# Sow & Piglet
st.sidebar.subheader("Sow & Piglet Parameters")
total_sows = st.sidebar.slider("Total Sows", 10, 200, 30, 1)
piglets_per_cycle = st.sidebar.slider("Piglets per Cycle", 5, 30, 10, 1)
piglet_mortality_pct = st.sidebar.slider("Piglet Mortality (%)", 0, 50, 7, 1)
abortion_rate_pct = st.sidebar.slider("Abortion Rate (%)", 0, 50, 0, 1)

# Feed & Sale
st.sidebar.subheader("Feed & Sale Parameters")
sow_feed_price = st.sidebar.slider("Sow Feed Price (₹/kg)", 0, 50, 30, 1)
sow_feed_intake = st.sidebar.slider("Sow Feed Intake (kg/day)", 0.0, 8.0, 2.8, 0.1)
grower_feed_price = st.sidebar.slider("Grower Feed Price (₹/kg)", 0, 50, 30, 1)
fcr = st.sidebar.slider("Feed Conversion Ratio (FCR)", 2.0, 4.0, 3.1, 0.1)
final_weight = st.sidebar.slider("Final Weight (kg)", 80, 250, 105, 5)
sale_price = st.sidebar.slider("Sale Price (₹/kg)", 100, 600, 180, 10)

# Management
st.sidebar.subheader("Management Parameters")
management_fee = st.sidebar.slider("Management Fee (Monthly)", 0, 500000, 0, 5000)
management_commission_pct = st.sidebar.slider("Management Commission (%)", 0, 50, 0, 1)
supervisor_salary = st.sidebar.slider("Supervisor Salary", 0, 200000, 25000, 5000)
worker_salary = st.sidebar.slider("Worker Salary", 0, 35000, 18000, 1000)
n_workers = st.sidebar.slider("Number of Workers", 0, 50, 2, 1)

# Capital Costs
st.sidebar.subheader("Capital Costs")
shed_cost = st.sidebar.slider("Shed Cost", 500000, 20000000, 1500000, 100000)
shed_life_years = st.sidebar.slider("Shed Life (Years)", 1, 30, 10, 1)
sow_cost = st.sidebar.slider("Sow Cost (per sow)", 20000, 200000, 35000, 1000)
sow_life_years = st.sidebar.slider("Sow Life (Years)", 1, 12, 4, 1)

# Loan
st.sidebar.subheader("Loan Parameters")
loan_amount = st.sidebar.slider("Loan Amount", 0, 20000000, 4000000, 100000)
interest_rate_pct = st.sidebar.slider("Interest Rate (%)", 0.0, 30.0, 12.1, 0.1)
loan_tenure_years = st.sidebar.slider("Loan Tenure (Years)", 1, 20, 5, 1)
moratorium_months = st.sidebar.slider("Moratorium Period (Months)", 0, 24, 0, 1)

# Other Fixed Costs
st.sidebar.subheader("Other Fixed Costs")
medicine_cost = st.sidebar.slider("Medicine Cost (Monthly)", 0, 100000, 10000, 1000)
electricity_cost = st.sidebar.slider("Electricity Cost (Monthly)", 0, 100000, 5000, 1000)
land_lease = st.sidebar.slider("Land Lease (Monthly)", 0, 100000, 10000, 1000)

# Simulation Duration
st.sidebar.subheader("Simulation Duration")
months = st.sidebar.slider("Simulation Duration (Months)", 12, 120, 60, 12)

# -------------------------------
# Run Simulation
# -------------------------------
df_month, df_year, total_sow_cost, shed_cost_val, first_sale_cash_needed, total_pigs_sold, total_pigs_born, animals_left, cumulative_cash_flow_scalar, total_interest_paid, break_even_month, profit_after_break_even, average_monthly_profit, avg_profit_after_breakeven, total_crossings, roi_with_assets_pct, roi_cash_pct, realized_cagr = sow_rotation_simulator(
    total_sows,
    piglets_per_cycle,
    piglet_mortality_pct / 100.0,
    abortion_rate_pct / 100.0,
    sow_feed_price,
    sow_feed_intake,
    grower_feed_price,
    fcr,
    final_weight,
    sale_price,
    management_fee,
    management_commission_pct / 100.0,
    supervisor_salary,
    worker_salary,
    n_workers,
    shed_cost,
    shed_life_years,
    sow_cost,
    sow_life_years,
    loan_amount,
    interest_rate_pct / 100.0,
    loan_tenure_years,
    moratorium_months,
    medicine_cost,
    electricity_cost,
    land_lease,
    months
)

# -------------------------------
# Display Summaries
# -------------------------------
st.subheader("Simulation Results")

st.write("Monthly Summary")
st.dataframe(df_month.head(120))

st.write("Yearly Summary")
st.dataframe(df_year)

st.subheader("Financial Summary")
initial_capital = shed_cost_val + total_sow_cost
initial_investment = initial_capital + first_sale_cash_needed
st.write(f"Total Crossings Done: {total_crossings:,}")
st.write(f"Total Pigs Born: {total_pigs_born:,}")
st.write(f"Total Pigs Sold: {total_pigs_sold:,}")
st.write(f"Animals Remaining in Shed: {animals_left:,}")
st.write(f"Initial Capital (Shed + Sows): ₹{initial_capital:,.0f}")
st.write(f"Working Capital till First Sale (estimated): ₹{first_sale_cash_needed:,.0f}")
st.write(f"Initial Investment (Capital + Working Capital): ₹{initial_investment:,.0f}")

if break_even_month:
    st.write(f"Break-even Month (incl. capital): {break_even_month}")
else:
    st.write("Break-even: Not achieved within simulation period")

st.write(f"Profit After Break-even (cumulative of monthly profit): ₹{profit_after_break_even:,.0f}")
st.write(f"Average Monthly Profit: ₹{average_monthly_profit:,.0f}")
st.write(f"Average Monthly Profit after Break-even: ₹{avg_profit_after_breakeven:,.0f}")
st.write(f"Total Interest Paid Over Loan Tenure (approx): ₹{total_interest_paid:,.0f}")

# ROI & CAGR outputs
st.write("---")
st.write(f"ROI (Cash Only): {roi_cash_pct:.2f}%")
st.write(f"ROI (Including asset liquidation): {roi_with_assets_pct:.2f}%")
if math.isnan(realized_cagr):
    st.write("Realized CAGR: Not meaningful / NaN for these numbers")
else:
    st.write(f"Realized CAGR (annualized): {realized_cagr*100:.2f}%")
st.write("---")

# -------------------------------
# Plots
# -------------------------------
st.subheader("Simulation Plots")

# 1) Revenue vs Total Costs
cost_components = ["Sow_Feed_Cost", "Grower_Feed_Cost", "Staff_Cost", "Other_Fixed_Costs", "Mgmt_Fee", "Mgmt_Comm", "Loan_EMI"]
df_plot1 = df_month.loc[df_month['Month'] <= 24, ["Month"] + cost_components + ["Revenue"]].copy()
df_costs_melt = df_plot1[["Month"] + cost_components].melt(id_vars="Month", var_name="Cost Component", value_name="Value")
area_chart = alt.Chart(df_costs_melt).mark_area(opacity=0.7).encode(
    x="Month:O",
    y="Value:Q",
    color="Cost Component:N",
    tooltip

    Perfect — here’s the continuation with all 4 plots included, exactly as before:

# -------------------------------
# Plot 1: Revenue vs Total Costs (Stacked Area)
# -------------------------------
area_chart = alt.Chart(df_costs_melt).mark_area(opacity=0.7).encode(
    x="Month:O",
    y="Value:Q",
    color="Cost Component:N",
    tooltip=["Month", "Cost Component", "Value"]
).properties(
    width=700,
    height=400,
    title="Monthly Cost Components (Stacked) vs Revenue"
)

revenue_line = alt.Chart(df_plot1).mark_line(color="black", strokeWidth=2).encode(
    x="Month:O",
    y="Revenue:Q",
    tooltip=["Month", "Revenue"]
)

st.altair_chart(area_chart + revenue_line, use_container_width=True)

# -------------------------------
# Plot 2: Monthly Profit
# -------------------------------
st.subheader("Monthly Profit")
profit_chart = alt.Chart(df_month).mark_bar(color="green").encode(
    x="Month:O",
    y="Monthly_Profit:Q",
    tooltip=["Month", "Monthly_Profit"]
).properties(width=700, height=400, title="Monthly Profit (Revenue - Total Costs)")
st.altair_chart(profit_chart, use_container_width=True)

# -------------------------------
# Plot 3: Cumulative Cash Flow
# -------------------------------
st.subheader("Cumulative Cash Flow")
cum_cash_chart = alt.Chart(df_month).mark_line(color="blue", strokeWidth=3).encode(
    x="Month:O",
    y="Cumulative_Cash_Flow:Q",
    tooltip=["Month", "Cumulative_Cash_Flow"]
).properties(width=700, height=400, title="Cumulative Cash Flow (Including Initial Capital + Working Capital)")
st.altair_chart(cum_cash_chart, use_container_width=True)

# -------------------------------
# Plot 4: Total Costs by Component (Stacked) over Simulation
# -------------------------------
st.subheader("Cost Breakdown Over Time")
df_costs_total_melt = df_month[["Month"] + cost_components].melt(id_vars="Month", var_name="Cost Component", value_name="Value")
cost_chart = alt.Chart(df_costs_total_melt).mark_area(opacity=0.6).encode(
    x="Month:O",
    y="Value:Q",
    color="Cost Component:N",
    tooltip=["Month", "Cost Component", "Value"]
).properties(width=700, height=400, title="Cost Components Over Time")
st.altair_chart(cost_chart, use_container_width=True)


    

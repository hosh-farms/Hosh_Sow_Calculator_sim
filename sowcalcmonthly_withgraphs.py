
# -------------------------------
# House of Supreme Ham Simulator
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
    # ----- Initialize -----
    current_sows = total_sows
    monthly_data = []

    shed_dep_rate = 1 / (shed_life_years * 12)
    sow_dep_rate = 1 / (sow_life_years * 12)
    total_months = loan_tenure_years * 12
    monthly_rate = interest_rate / 12

    # EMI calculation
    emi = 0
    if loan_amount > 0 and total_months > 0:
        emi = loan_amount * monthly_rate * (1 + monthly_rate)**total_months / ((1 + monthly_rate)**total_months - 1)
    loan_balance = loan_amount

    # Sow mating logic
    average_cycle_length = 3.8 + 1.3 + 0.33
    sows_to_mate_per_month = total_sows / average_cycle_length

    batches = []
    ready_for_sale_batches = []
    total_sow_cost = sow_cost * total_sows
    total_capital = shed_cost + total_sow_cost  # initial capital
    total_pigs_born = 0
    total_pigs_sold = 0

    first_sale_cash_needed = 0
    first_sale_done = False

    # ----- Monthly Simulation -----
    for month in range(1, months + 1):
        # Costs
        sow_feed_cost = current_sows * sow_feed_intake * 30 * sow_feed_price
        staff_cost = supervisor_salary + n_workers * worker_salary
        mgmt_fixed = management_fee
        other_fixed = medicine_cost + electricity_cost + land_lease

        # Mating & Piglets
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

        # Lactating piglets
        piglets_with_sow = sum(batch['piglets'] for batch in batches if batch['farrow_month'] <= month < batch['wean_month'])
        current_growers = sum(batch['piglets'] for batch in batches if batch['grower_start_month'] <= month < batch['grower_end_month'])
        grower_feed_cost = sum(batch['grower_feed_per_month'] * grower_feed_price for batch in batches if batch['grower_start_month'] <= month < batch['grower_end_month'])

        # Ready for sale
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
            for batch in ready_for_sale_batches:
                batch['sold'] = True
            ready_for_sale_batches = []

        # Track first sale working capital
        if not first_sale_done:
            first_sale_cash_needed += sow_feed_cost + grower_feed_cost + staff_cost + mgmt_fixed + other_fixed
        if sold_pigs > 0 and not first_sale_done:
            first_sale_done = True

        mgmt_comm_cost = revenue * management_commission
        total_operating_cost = sow_feed_cost + grower_feed_cost + staff_cost + mgmt_fixed + mgmt_comm_cost + other_fixed
        dep = shed_cost * shed_dep_rate + total_sow_cost * sow_dep_rate

        # Loan Payment
        if month <= moratorium_months:
            loan_payment = 0
            loan_balance += loan_balance * monthly_rate
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
            'Piglets_Born_Alive': piglets_with_sow,
            'Growers': current_growers,
            'Sold_Pigs': sold_pigs,
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

    # Animals left
    animals_left = int(sum(batch['piglets'] for batch in batches if not batch['sold'] and batch['grower_end_month'] > months))

    # Initial Investment
    total_sow_cost = total_sows * sow_cost
    shed_cost_val = shed_cost
    initial_investment = shed_cost + total_sow_cost 

    # ----- Cumulative Cash Flow (month by month) -----
    cumulative_cash_flow = [-initial_investment]
    for val in df_month['Monthly_Cash_Flow']:
        cumulative_cash_flow.append(cumulative_cash_flow[-1] + val)
    cumulative_cash_flow = cumulative_cash_flow[1:]
    df_month['Cumulative_Cash_Flow'] = cumulative_cash_flow

    # Break-even
    break_even_month = None
    running_cash = -initial_investment
    for i, val in enumerate(df_month['Monthly_Cash_Flow']):
        running_cash += val
        if running_cash >= 0:
            break_even_month = i + 1
            break

    # Profit After Break-even
    if break_even_month:
        profit_after_break_even = df_month['Monthly_Profit'].iloc[break_even_month:].sum()
        months_after_breakeven = len(df_month) - break_even_month
        avg_profit_after_breakeven = df_month['Monthly_Profit'].iloc[break_even_month:].mean()
    else:
        profit_after_break_even = 0
        avg_profit_after_breakeven = 0

    average_monthly_profit = df_month['Monthly_Profit'].mean()

    # Cash-only CAGR
    years = months / 12
    final_cash = cumulative_cash_flow[-1] + initial_investment  # net cash returned
    realized_cagr = (final_cash / (first_sale_cash_needed + initial_investment)) ** (1 / years) - 1

    # ROI / CAGR
    final_cumulative_cash_flow = cumulative_cash_flow[-1]
    roi_cash_pct = (final_cumulative_cash_flow) / (first_sale_cash_needed + initial_investment)) * 100
    years = months / 12
    # realized_cagr = (final_cumulative_cash_flow) / first_sale_cash_needed + initial_investment ** (1/years) - 1

        # ROI including remaining assets
    remaining_shed_value = shed_cost * (1 - months / (shed_life_years * 12))
    remaining_sow_value = total_sow_cost * (1 - months / (sow_life_years * 12))
    remaining_animals_value = animals_left * 12000  # approximate value of remaining pigs
    roi_with_assets_pct = ((final_cumulative_cash_flow + remaining_shed_value + remaining_sow_value + remaining_animals_value) / (first_sale_cash_needed + initial_investment - 1)) * 100

    # Total crossings (optional)
    total_crossings = df_month['Sows_Crossed'].sum() if 'Sows_Crossed' in df_month.columns else 0

    # Total interest paid
    loan_balance = loan_amount
    total_interest_paid = 0
    for m in range(1, months + 1):
        monthly_interest = loan_balance * monthly_rate
        if m <= moratorium_months:
            loan_balance += monthly_interest
            loan_payment = 0
        elif m <= total_months:
            principal = emi - monthly_interest
            loan_balance -= principal
            loan_payment = emi
        else:
            monthly_interest = 0
        total_interest_paid += monthly_interest

    return (
        df_month,
        df_year,
        total_sow_cost,
        shed_cost_val,
        first_sale_cash_needed,
        total_pigs_sold,
        total_pigs_born,
        animals_left,
        cumulative_cash_flow,
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
st.write(f"ROI : {roi_cash_pct:.2f}%")
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

# -------------------------------
# Prepare cost data for plots
# -------------------------------
cost_components = ["Sow_Feed_Cost", "Grower_Feed_Cost", "Staff_Cost",
                   "Other_Fixed_Costs", "Mgmt_Fee", "Mgmt_Comm", "Loan_EMI"]

# Plot 1: Revenue vs Total Costs (Stacked Area)
df_plot1 = df_month[["Month"] + cost_components + ["Revenue"]].copy()
df_costs_melt = df_plot1.melt(id_vars="Month", value_vars=cost_components, 
                              var_name="Cost Component", value_name="Value")

area_chart = alt.Chart(df_costs_melt).mark_area(opacity=0.7).encode(
    x=alt.X("Month:O", title="Month"),
    y=alt.Y("Value:Q", title="Amount (₹)"),
    color=alt.Color("Cost Component:N"),
    tooltip=["Month", "Cost Component", "Value"]
).properties(height=360)

revenue_line = alt.Chart(df_plot1).mark_line(color="black", strokeWidth=2).encode(
    x=alt.X("Month:O"),
    y=alt.Y("Revenue:Q"),
    tooltip=["Month", "Revenue"]
)

st.subheader("1) Revenue vs Total Costs (Stacked Area)")
st.altair_chart(area_chart + revenue_line, use_container_width=True)

# Plot 2: Monthly Profit
st.subheader("2) Monthly Profit")
profit_chart = alt.Chart(df_month).mark_bar(color="green").encode(
    x=alt.X("Month:O", title="Month"),
    y=alt.Y("Monthly_Profit:Q", title="Profit (₹)"),
    tooltip=["Month", "Monthly_Profit"]
).properties(height=360)
st.altair_chart(profit_chart, use_container_width=True)

# Plot 3: Cumulative Cash Flow
st.subheader("3) Cumulative Cash Flow")
cum_cash_chart = alt.Chart(df_month).mark_line(color="blue", strokeWidth=3).encode(
    x=alt.X("Month:O", title="Month"),
    y=alt.Y("Cumulative_Cash_Flow:Q", title="Cumulative Cash Flow (₹)"),
    tooltip=["Month", "Cumulative_Cash_Flow"]
).properties(height=360)
st.altair_chart(cum_cash_chart, use_container_width=True)

# Plot 4: Total Costs by Component over Simulation
st.subheader("4) Total Costs by Component Over Time")
df_costs_total_melt = df_month[["Month"] + cost_components].melt(
    id_vars="Month", var_name="Cost Component", value_name="Value"
)
cost_chart = alt.Chart(df_costs_total_melt).mark_area(opacity=0.6).encode(
    x=alt.X("Month:O"),
    y=alt.Y("Value:Q"),
    color=alt.Color("Cost Component:N"),
    tooltip=["Month", "Cost Component", "Value"]
).properties(height=360)
st.altair_chart(cost_chart, use_container_width=True)

# Save this file and run with:
# streamlit run sowcalc_streamlit_final.py

import streamlit as st
import pandas as pd
import math
import altair as alt

# -------------------------------
# Sow Rotation Simulator with realistic monthly sales
# (kept your logic; added cumulative columns, ROI/CAGR and plotting)
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
    loan_amount=4000000,
    interest_rate=0.121,           # decimal (UI will pass %/100)
    loan_tenure_years=5,
    moratorium_months=0,
    medicine_cost=10000,
    electricity_cost=5000,
    land_lease=10000,
    months=60
):
    current_sows = total_sows
    monthly_data = []

    shed_dep_rate = 1 / (shed_life_years * 12)
    sow_dep_rate = 1 / (sow_life_years * 12)

    total_months = loan_tenure_years * 12
    monthly_rate = interest_rate / 12
    emi = 0
    if loan_amount > 0 and total_months > 0:
        emi = loan_amount * monthly_rate * (1 + monthly_rate)**total_months / ((1 + monthly_rate)**total_months - 1)
    loan_balance = loan_amount

    average_cycle_length = 3.8 + 1.3 + 0.33
    sows_to_mate_per_month = total_sows / average_cycle_length

    batches = []
    ready_for_sale_batches = []
    total_sow_cost = sow_cost * total_sows
    total_capital = shed_cost + total_sow_cost            # initial capital (shed + sows)
    total_pigs_born = 0
    total_pigs_sold = 0

    first_sale_cash_needed = 0         # working capital required until first sale (running sum)
    first_sale_done = False

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

        # Count piglets in lactation
        piglets_with_sow = sum(batch['piglets'] for batch in batches if batch['farrow_month'] <= month < batch['wean_month'])
        # Count growers
        current_growers = sum(batch['piglets'] for batch in batches if batch['grower_start_month'] <= month < batch['grower_end_month'])
        # Calculate grower feed
        grower_feed_cost = sum(batch['grower_feed_per_month'] * grower_feed_price for batch in batches if batch['grower_start_month'] <= month < batch['grower_end_month'])

        # Identify batches ready for sale
        for batch in batches:
            if batch['grower_end_month'] <= month and not batch['sold'] and batch not in ready_for_sale_batches:
                ready_for_sale_batches.append(batch)

        sold_pigs = 0
        revenue = 0
        # Monthly sale logic (sell all ready batches)
        if ready_for_sale_batches:
            pigs_sold_this_month = 0
            batches_sold_ids = []
            for batch in ready_for_sale_batches:
                pigs_sold_batch = batch['piglets']
                pigs_sold_this_month += pigs_sold_batch
                batch['sold'] = True
                batches_sold_ids.append(batch['batch_id'])
            revenue += pigs_sold_this_month * final_weight * sale_price
            sold_pigs = pigs_sold_this_month
            total_pigs_sold += sold_pigs
            current_growers -= sold_pigs

            # Remove sold batches from ready list
            ready_for_sale_batches = [b for b in ready_for_sale_batches if b['batch_id'] not in batches_sold_ids]

        # Track first sale working capital
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

    # Yearly summary
    df_year = df_month.groupby(((df_month['Month']-1)//12)*12).sum()
    df_year.index = [f"Year {i+1}" for i in range(len(df_year))]

    # Total animals left in shed
    animals_left = int(sum(batch['piglets'] for batch in batches if not batch['sold'] and batch['grower_end_month'] > months))
    total_interest_paid = 0.0

    # recompute interest paid over simulated months
    loan_balance = loan_amount
    total_interest_paid = 0.0
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
            loan_payment = 0
        total_interest_paid += monthly_interest

    # -------------------------
    # CUMULATIVE columns and ROI/CAGR
    # -------------------------
    # -------------------------
# CUMULATIVE Cash Flow (fixed)
   # -------------------------
# CUMULATIVE Cash Flow (fixed)
# -------------------------
    initial_capital = total_capital                       # shed + sows
    initial_working_capital = first_sale_cash_needed      # working capital required up front
    initial_investment = initial_capital + initial_working_capital
    
    # Cash series: monthly cash flow (revenue - operating costs - loan payment)
    cash_series = df_month['Monthly_Cash_Flow'].astype(float).fillna(0.0)
    
    # Cumulative Cash Flow starts at negative total investment
    cumulative_cash_flow = -initial_investment + cash_series.cumsum()
    
    # Add to dataframe (rounded)
    df_month['Cumulative_Cash_Flow'] = cumulative_cash_flow.round(0)

    df_month['Cumulative_Profit'] = cumulative_profit_excl_capital.round(0)

    final_cumulative_cash_flow = float(cumulative_cash_flow.iloc[-1])
    # final_cumulative_working_cap = float(cumulative_working_cap.iloc[-1])
    final_cumulative_profit = float(cumulative_profit_excl_capital.iloc[-1])

    # Final asset liquidation (estimate)
    shed_remaining_value = shed_cost * max(0.0, (shed_life_years*12 - months)/(shed_life_years*12))
    sows_remaining_value = current_sows * sow_cost * max(0.0, (sow_life_years*12 - months)/(sow_life_years*12))
    growers_remaining_value = animals_left * final_weight * sale_price   # rough market value

    final_assets_value = shed_remaining_value + sows_remaining_value + growers_remaining_value

    # ROI (cash only) = total cash returned / initial investment *100
    total_cash_returned = cash_series.sum()
    roi_cash_pct = (total_cash_returned / initial_investment) * 100 if initial_investment > 0 else float('nan')

    # ROI including assets (liquidation)
    roi_with_assets_pct = ((total_cash_returned + final_assets_value) / initial_investment) * 100 if initial_investment > 0 else float('nan')

    # Realized CAGR on cash-only flows: money_multiple = total_cash_returned / initial_investment
    years = months / 12.0
    realized_cagr = float('nan')
    if initial_investment > 0 and total_cash_returned > 0 and years > 0:
        money_multiple = total_cash_returned / initial_investment
        if money_multiple > 0:
            realized_cagr = (money_multiple ** (1.0/years) - 1.0) * 100.0
        else:
            realized_cagr = float('nan')

    # legacy total ROI (final cumulative cash with capital / initial_investment)
    total_roi_pct_legacy = (final_cumulative_cash_flow / initial_investment) * 100 if initial_investment > 0 else float('nan')

    # Break-even month (first month cumulative cash with capital >= 0)
    be_idx = df_month[df_month['Cumulative_Cash_Flow'] >= 0].index
    be_month = int(df_month.loc[be_idx[0], 'Month']) if len(be_idx) > 0 else None

    total_crossings = int(df_month['Sows_Crossed'].sum()) if 'Sows_Crossed' in df_month.columns else 0
    average_monthly_profit = df_month['Monthly_Profit'].mean() if len(df_month) > 0 else 0.0
    avg_profit_after_breakeven = 0.0
    if be_month:
        rem = df_month.loc[df_month['Month'] >= be_month, 'Monthly_Profit']
        avg_profit_after_breakeven = rem.mean() if not rem.empty else 0.0

    return (
        df_month,
        df_year,
        total_sow_cost,
        shed_cost,
        first_sale_cash_needed,
        total_pigs_sold,
        total_pigs_born,
        animals_left,
        final_cumulative_cash_flow,
        total_interest_paid,
        be_month,
        profit_after_break_even if 'profit_after_break_even' in locals() else 0,
        average_monthly_profit,
        avg_profit_after_breakeven,
        total_crossings,
        roi_with_assets_pct,
        realized_cagr,
        roi_cash_pct
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
# Run Simulation and get results
# -------------------------------
df_month, df_year, total_sow_cost, shed_cost_val, first_sale_wc, total_pigs_sold, total_pigs_born, animals_left, cumulative_cash_flow_scalar, total_interest_paid, break_even_month, profit_after_break_even, average_monthly_profit, avg_profit_after_breakeven, total_crossings, roi_with_assets_pct, realized_cagr, roi_cash_pct = sow_rotation_simulator(
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
# Display Summaries in Streamlit
# -------------------------------
st.subheader("Simulation Results")

st.write("Monthly Summary")
st.dataframe(df_month.head(120))

st.write("Yearly Summary")
st.dataframe(df_year)

st.subheader("Financial Summary")
initial_capital = shed_cost_val + total_sow_cost
initial_investment = initial_capital + first_sale_wc
st.write(f"Total Crossings Done: {total_crossings:,}")
st.write(f"Total Pigs Born: {total_pigs_born:,}")
st.write(f"Total Pigs Sold: {total_pigs_sold:,}")
st.write(f"Animals Remaining in Shed: {animals_left:,}")
st.write(f"Initial Capital (Shed + Sows): ₹{initial_capital:,.0f}")
st.write(f"Working Capital till First Sale (estimated): ₹{first_sale_wc:,.0f}")
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
st.write(f"ROI: {roi_cash_pct:.2f}%")
st.write(f"ROI (Including asset liquidation): {roi_with_assets_pct:.2f}%")
if math.isnan(realized_cagr):
    st.write("Realized CAGR: Not meaningful / NaN for these numbers")
else:
    st.write(f"Realized CAGR: {realized_cagr:.2f}%")
st.write("---")

# -------------------------------
# Generate and Display Plots (Altair)
# -------------------------------
st.subheader("Simulation Plots")

# Plot 1: Revenue vs Total Costs (stacked) - first 24 months
st.write("1) Revenue vs Total Costs (stacked) — first 24 months")
cost_components = ["Sow_Feed_Cost", "Grower_Feed_Cost", "Staff_Cost", "Other_Fixed_Costs", "Mgmt_Fee", "Mgmt_Comm", "Loan_EMI"]
df_plot1 = df_month.loc[df_month['Month'] <= 24, ["Month"] + cost_components + ["Revenue"]].copy()

df_costs_melt = df_plot1[["Month"] + cost_components].melt(id_vars="Month", var_name="Cost Component", value_name="Value")
area_chart = alt.Chart(df_costs_melt).mark_area(opacity=0.7).encode(
    x=alt.X("Month:O", title="Month (months)"),
    y=alt.Y("Value:Q", title="Amount (₹)"),
    color=alt.Color("Cost Component:N", legend=alt.Legend(title="Cost Component")),
    tooltip=["Month", "Cost Component", "Value"]
)
revenue_line = alt.Chart(df_plot1).mark_line(strokeWidth=3).encode(
    x=alt.X("Month:O"),
    y=alt.Y("Revenue:Q"),
    tooltip=["Month", "Revenue"]
)
chart1 = (area_chart + revenue_line).properties(height=360)
st.altair_chart(chart1, use_container_width=True)

# Plot 2: Monthly Profit - first 24 months zoomed
st.write("2) Monthly Profit (first 24 months zoom)")
df_profit_24 = df_month.loc[df_month['Month'] <= 24, ['Month', 'Monthly_Profit']].copy()
profit_chart = alt.Chart(df_profit_24).mark_line(point=True).encode(
    x=alt.X("Month:O", title="Month"),
    y=alt.Y("Monthly_Profit:Q", title="Profit (₹)"),
    tooltip=["Month", "Monthly_Profit"]
).properties(height=300)
st.altair_chart(profit_chart, use_container_width=True)

# Plot 3: Cumulative Cash Flow (includes capital) + Cumulative Profit + Cumulative Working Capital
st.write("3) Cumulative Cash Flow (includes capital) & Cumulative Profit & Working-Capital Flow (₹ Lakhs)")
df_cum_plot = pd.DataFrame({
    "Month": df_month["Month"],
    "Cumulative Cash Flow (₹ Lakhs)": df_month["Cumulative_Cash_Flow"] / 1e5,
    "Cumulative Profit (₹ Lakhs)": df_month["Cumulative_Profit"] / 1e5
    # "Cumulative Working Capital Flow (₹ Lakhs)": df_month["Cumulative_Working_Capital_Flow"] / 1e5
})
df_cum_melt = df_cum_plot.melt(id_vars=["Month"], var_name="Metric", value_name="Value")

line_chart = alt.Chart(df_cum_melt).mark_line(point=True).encode(
    x=alt.X("Month:O", title="Month"),
    y=alt.Y("Value:Q", title="Amount (₹ Lakhs)"),
    color=alt.Color("Metric:N"),
    tooltip=["Month", "Metric", "Value"]
).properties(height=420)

rule = None
if break_even_month:
    rule = alt.Chart(pd.DataFrame({"Month":[break_even_month]})).mark_rule(color="red", strokeDash=[6,2]).encode(x="Month:O")

if rule is not None:
    st.altair_chart(line_chart + rule, use_container_width=True)
else:
    st.altair_chart(line_chart, use_container_width=True)

# Plot 4: Total Costs by Component (bars)
st.write("4) Total Costs by Component (over full simulation)")
total_costs = df_month[cost_components].sum().reset_index()
total_costs.columns = ["Cost Component", "Total"]
bar_chart = alt.Chart(total_costs).mark_bar().encode(
    x=alt.X("Cost Component:N", sort="-y", title="Cost Component"),
    y=alt.Y("Total:Q", title="Total (₹)"),
    color=alt.Color("Cost Component:N", legend=None),
    tooltip=["Cost Component", "Total"]
).properties(height=360)
st.altair_chart(bar_chart, use_container_width=True)

# Plot 5: ROI & Realized CAGR Comparison
st.write("5) ROI & Realized CAGR Comparison")
df_roi_cagr = pd.DataFrame({
    "Metric": ["ROI (cash only)", "ROI (incl. assets)", "Realized CAGR (ann.)"],
    "Value": [roi_cash_pct, roi_with_assets_pct, realized_cagr if not math.isnan(realized_cagr) else None]
})
roi_chart = alt.Chart(df_roi_cagr).mark_bar().encode(
    x=alt.X("Metric:N"),
    y=alt.Y("Value:Q", title="Percentage"),
    color=alt.Color("Metric:N", legend=None),
    tooltip=["Metric", "Value"]
).properties(height=320)
st.altair_chart(roi_chart, use_container_width=True)

# Plot 6: ROI & CAGR over time
st.write("6) Cumulative ROI (cash only) & Realized CAGR (over time)")
initial_capital_main = initial_capital
months_arr = df_month['Month']
cumulative_roi_pct_over_time = ((df_month['Cumulative_Cash_Flow'] / initial_investment) * 100).fillna(0)

cumulative_cash_only = ((-initial_investment) + df_month['Monthly_Cash_Flow'].cumsum())
realized_cagr_over_time = []
for i, m in enumerate(months_arr):
    yrs = (m / 12.0)
    final_cash = df_month.loc[:i, 'Monthly_Cash_Flow'].sum()
    if initial_investment > 0 and final_cash > 0 and yrs > 0:
        mult = final_cash / initial_investment
        if mult > 0:
            realized_cagr_over_time.append((mult ** (1.0/yrs) - 1.0) * 100.0)
        else:
            realized_cagr_over_time.append(None)
    else:
        realized_cagr_over_time.append(None)

df_time_viz = pd.DataFrame({
    "Month": months_arr,
    "Cumulative ROI (%)": cumulative_roi_pct_over_time,
    "Realized CAGR (%)": realized_cagr_over_time
}).melt(id_vars=["Month"], var_name="Metric", value_name="Value")

time_chart = alt.Chart(df_time_viz).mark_line(point=True).encode(
    x=alt.X("Month:O", title="Month"),
    y=alt.Y("Value:Q", title="Percentage"),
    color="Metric:N",
    tooltip=["Month", "Metric", "Value"]
).properties(height=350)

st.altair_chart(time_chart, use_container_width=True)

st.write("Done — if any numbers look off (NaN or unexpected) tell me the input values and I'll explain or adjust formulas.")

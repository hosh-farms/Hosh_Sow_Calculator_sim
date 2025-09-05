import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# -------------------------------
# Simulation Function
# -------------------------------
def sow_rotation_simulator(
    total_sows,
    piglets_per_cycle,
    piglet_mortality,
    abortion_rate,
    sow_feed_price,
    sow_feed_intake,
    grower_feed_price,
    fcr,
    final_weight,
    sale_price,
    management_fee,
    management_commission,
    supervisor_salary,
    worker_salary,
    num_workers,
    shed_cost,
    shed_life,
    sow_cost,
    sow_life,
    loan_amount,
    interest_rate,
    loan_years,
    moratorium_months,
    medicine_cost,
    electricity_cost,
    land_lease,
    months
):
    # ---- Capital Costs ----
    total_sow_cost = total_sows * sow_cost
    shed_cost_val = shed_cost
    initial_capital = total_sow_cost + shed_cost_val
    first_sale_cash_needed = initial_capital + (sow_feed_price * sow_feed_intake * total_sows * 4)

    # ---- Setup DataFrame ----
    df_month = pd.DataFrame({"Month": range(1, months + 1)})
    df_month["Monthly_Cash_Flow"] = 0.0

    # ---- Piglet Production & Sales ----
    piglets_born = []
    pigs_sold = []
    for m in range(1, months + 1):
        if m % 4 == 0:  # farrowing cycle
            born = total_sows * piglets_per_cycle
            born = born * (1 - piglet_mortality) * (1 - abortion_rate)
            piglets_born.append(born)
        else:
            piglets_born.append(0)

        if m % 6 == 0:  # selling cycle
            sold = total_sows * piglets_per_cycle * (1 - piglet_mortality) * (1 - abortion_rate)
            pigs_sold.append(sold)
        else:
            pigs_sold.append(0)

    df_month["Piglets_Born"] = piglets_born
    df_month["Pigs_Sold"] = pigs_sold

    # ---- Revenue ----
    df_month["Revenue"] = df_month["Pigs_Sold"] * final_weight * sale_price

    # ---- Costs ----
    df_month["Sow_Feed_Cost"] = sow_feed_intake * sow_feed_price * total_sows * 30
    df_month["Grower_Feed_Cost"] = df_month["Piglets_Born"] * fcr * grower_feed_price
    df_month["Management_Cost"] = management_fee + (df_month["Revenue"] * management_commission / 100)
    df_month["Salary_Cost"] = supervisor_salary + (worker_salary * num_workers)
    df_month["Fixed_Costs"] = medicine_cost + electricity_cost + land_lease

    df_month["Total_Costs"] = (
        df_month["Sow_Feed_Cost"] +
        df_month["Grower_Feed_Cost"] +
        df_month["Management_Cost"] +
        df_month["Salary_Cost"] +
        df_month["Fixed_Costs"]
    )

    # ---- Cash Flow ----
    df_month["Monthly_Cash_Flow"] = df_month["Revenue"] - df_month["Total_Costs"]

    # ---- Cumulative Metrics ----
    df_month["Cumulative_Cash_Flow"] = -initial_capital  # start negative with assets
    df_month["Cumulative_Cash_Flow"] += df_month["Monthly_Cash_Flow"].cumsum()

    df_month["Cumulative_Profit"] = df_month["Monthly_Cash_Flow"].cumsum()

    # ---- Totals ----
    cumulative_cash_flow = df_month["Cumulative_Cash_Flow"].iloc[-1]
    animals_left = 0  # assume no residual animals for now

    total_investment_with_assets = initial_capital + first_sale_cash_needed
    total_investment_without_assets = first_sale_cash_needed

    roi_with_assets = ((cumulative_cash_flow + animals_left + shed_cost_val + total_sow_cost) / total_investment_with_assets) * 100
    total_roi_pct = (cumulative_cash_flow / total_investment_without_assets) * 100

    years = months / 12
    if years > 0 and total_investment_without_assets > 0 and (cumulative_cash_flow + total_investment_without_assets) > 0:
        realized_cagr = ((cumulative_cash_flow + total_investment_without_assets) / total_investment_without_assets) ** (1 / years) - 1
    else:
        realized_cagr = 0

    return (
        df_month,
        roi_with_assets,
        total_roi_pct,
        realized_cagr,
        total_sow_cost,
        shed_cost_val,
        first_sale_cash_needed,
        animals_left,
        cumulative_cash_flow
    )

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("🐷 House of Supreme Ham Simulator")

st.sidebar.header("Adjust Simulation Parameters")

# Sow & Piglet Parameters
total_sows = st.sidebar.number_input("Total Sows", 10, 500, 30)
piglets_per_cycle = st.sidebar.number_input("Piglets per Cycle", 5, 20, 10)
piglet_mortality_pct = st.sidebar.slider("Piglet Mortality (%)", 0.0, 20.0, 7.0)
abortion_rate_pct = st.sidebar.slider("Abortion Rate (%)", 0.0, 10.0, 0.0)

# Feed & Sale Parameters
sow_feed_price = st.sidebar.number_input("Sow Feed Price (₹/kg)", 10, 100, 30)
sow_feed_intake = st.sidebar.number_input("Sow Feed Intake (kg/day)", 1, 10, 3)
grower_feed_price = st.sidebar.number_input("Grower Feed Price (₹/kg)", 10, 100, 25)
fcr = st.sidebar.number_input("Feed Conversion Ratio (FCR)", 1.0, 5.0, 2.5)
final_weight = st.sidebar.number_input("Final Weight (kg)", 50, 200, 100)
sale_price = st.sidebar.number_input("Sale Price (₹/kg)", 50, 300, 120)

# Management Parameters
management_fee = st.sidebar.number_input("Management Fee (Monthly)", 0, 50000, 5000)
management_commission = st.sidebar.slider("Management Commission (%)", 0.0, 20.0, 5.0)
supervisor_salary = st.sidebar.number_input("Supervisor Salary", 0, 50000, 15000)
worker_salary = st.sidebar.number_input("Worker Salary", 0, 30000, 10000)
num_workers = st.sidebar.number_input("Number of Workers", 0, 50, 5)

# Capital Costs
shed_cost = st.sidebar.number_input("Shed Cost", 100000, 5000000, 1000000)
shed_life = st.sidebar.number_input("Shed Life (Years)", 1, 30, 10)
sow_cost = st.sidebar.number_input("Sow Cost (per sow)", 5000, 50000, 15000)
sow_life = st.sidebar.number_input("Sow Life (Years)", 1, 10, 3)

# Loan Parameters
loan_amount = st.sidebar.number_input("Loan Amount", 0, 10000000, 0)
interest_rate = st.sidebar.slider("Interest Rate (%)", 0.0, 30.0, 12.0)
loan_years = st.sidebar.number_input("Loan Tenure (Years)", 1, 20, 5)
moratorium_months = st.sidebar.number_input("Moratorium Period (Months)", 0, 24, 0)

# Other Fixed Costs
medicine_cost = st.sidebar.number_input("Medicine Cost (Monthly)", 0, 50000, 2000)
electricity_cost = st.sidebar.number_input("Electricity Cost (Monthly)", 0, 50000, 3000)
land_lease = st.sidebar.number_input("Land Lease (Monthly)", 0, 100000, 5000)

# Simulation Duration
months = st.sidebar.number_input("Simulation Duration (Months)", 12, 240, 84)

# -------------------------------
# Run Simulation
# -------------------------------
(
    df_month,
    roi_with_assets,
    total_roi_pct,
    realized_cagr,
    total_sow_cost,
    shed_cost_val,
    first_sale_cash_needed,
    animals_left,
    cumulative_cash_flow
) = sow_rotation_simulator(
    total_sows, piglets_per_cycle, piglet_mortality_pct / 100, abortion_rate_pct / 100,
    sow_feed_price, sow_feed_intake, grower_feed_price, fcr, final_weight, sale_price,
    management_fee, management_commission, supervisor_salary, worker_salary, num_workers,
    shed_cost, shed_life, sow_cost, sow_life,
    loan_amount, interest_rate, loan_years, moratorium_months,
    medicine_cost, electricity_cost, land_lease, months
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


# # -------------------------------
# # Output Metrics
# # -------------------------------
# st.subheader("Simulation Results")
# st.write(f"ROI (with Assets): {roi_with_assets:.2f}%")
# st.write(f"ROI (without Assets): {total_roi_pct:.2f}%")
# st.write(f"Realized CAGR (on cash flows): {realized_cagr*100:.2f}%")
# st.write(f"Total Investment (Capital + WC till first sale): ₹{first_sale_cash_needed:,.0f}")
# st.write(f"Cumulative Cash Flow: ₹{cumulative_cash_flow:,.0f}")



# # ROI & CAGR outputs
# st.write("---")
# st.write(f"ROI: {roi_cash_pct:.2f}%")
# st.write(f"ROI (Including asset liquidation): {roi_with_assets_pct:.2f}%")
# if math.isnan(realized_cagr):
#     st.write("Realized CAGR: Not meaningful / NaN for these numbers")
# else:
#     st.write(f"Realized CAGR: {realized_cagr:.2f}%")
# st.write("---")

# -------------------------------
# Generate and Display Plots (Altair)
# -------------------------------
st.subheader("Simulation Plots")

# -------------------------------
# Graphs
# -------------------------------
st.write("Cumulative Cash Flow & Profit Over Time")

df_cumulative = pd.DataFrame({
    "Month": df_month["Month"],
    "Cumulative Cash Flow": df_month["Cumulative_Cash_Flow"]/1e5,
    "Cumulative Profit": df_month["Cumulative_Profit"]/1e5,
})

df_cum_melt = df_cumulative.melt(id_vars=["Month"], var_name="Metric", value_name="Value")

line_chart = alt.Chart(df_cum_melt).mark_line().encode(
    x=alt.X("Month:O", title="Time (Months)"),
    y=alt.Y("Value:Q", title="Amount (₹ Lakhs)"),
    color="Metric",
    tooltip=["Month", "Metric", "Value"]
)

st.altair_chart(line_chart, use_container_width=True)


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
    "Cumulative Profit (₹ Lakhs)": df_month["Cumulative_Profit"] / 1e5,
    "Cumulative Working Capital Flow (₹ Lakhs)": df_month["Cumulative_Working_Capital_Flow"] / 1e5
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

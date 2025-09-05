
import streamlit as st
import pandas as pd
# import numpy_financial as npf

# Sow Rotation Simulator with realistic monthly sales
# -------------------------------
def sow_rotation_simulator(
    total_sows=30,
    piglets_per_cycle=10,
    piglet_mortality=0.07,
    abortion_rate=0.0,
    sow_feed_price=32,
    sow_feed_intake=2.7,
    grower_feed_price=32,
    fcr=3.0,
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
    interest_rate=12.1,
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
    total_capital_invested = shed_cost + total_sow_cost
    cumulative_cash_flow = -(total_capital_invested)
    total_pigs_born = 0
    total_pigs_sold = 0

    first_sale_cash_needed = 0
    first_sale_done = False

    for month in range(1, months + 1):
        sow_feed_cost = current_sows * sow_feed_intake * 30 * sow_feed_price
        staff_cost = supervisor_salary + n_workers * worker_salary
        mgmt_fixed = management_fee

        sows_crossed = 0
        if month >= 2:
            sows_to_mate = sows_to_mate_per_month
            sows_pregnant = sows_to_mate * (1 - abortion_rate)
            sows_crossed = sows_to_mate  # track how many sows were crossed this month
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
        current_growers = sum(batch['piglets'] for batch in batches if batch['grower_start_month'] < month < batch['grower_end_month'])
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
        cumulative_cash_flow = cumulative_cash_flow + monthly_cash_flow 

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
            'Cumulative_Cash_Flow': round(cumulative_cash_flow),
            'Depreciation': round(dep)
        })

    df_month = pd.DataFrame(monthly_data)

    # Yearly summary
    df_year = df_month.groupby(((df_month['Month']-1)//12)*12).sum()
    df_year.index = [f"Year {i+1}" for i in range(len(df_year))]

    # df_year['Cash_Yearly_Profit'] = df_year['Revenue'] - df_year['Total_Operating_Cost']
    # df_year['Profit_After_Loan'] = df_year['Cash_Yearly_Profit'] - df_year['Loan_EMI']

    # df_year['Total_Crossings'] = df_month.groupby(((df_month['Month']-1)//12)*12)['Sows_Crossed'].sum().values

    # Total animals left in shed
    animals_left = sum(batch['piglets'] for batch in batches if not batch['sold'] and batch['grower_end_month'] > months)
    total_interest_paid = 0

    loan_balance = loan_amount
    total_interest_paid = 0

    for month in range(1, months + 1):
        monthly_interest = loan_balance * monthly_rate

        if month <= moratorium_months:
            # Interest accrues but no EMI paid
            loan_balance += monthly_interest  # capitalize interest
            loan_payment = 0
        elif month <= total_months:
            # EMI payment starts
            principal = emi - monthly_interest
            loan_balance -= principal
            loan_payment = emi
        else:
            loan_payment = 0
            monthly_interest = 0

        total_interest_paid += monthly_interest


    # Define total capital for financial calculations
    total_capital = total_sow_cost + shed_cost

    # Use the per-month cumulative series from df_month (not the scalar)
    cum_series = df_month['Cumulative_Cash_Flow']

    # Find first month where cumulative cash flow >= 0
    breakeven_indices = cum_series[cum_series >= 0].index
    if len(breakeven_indices) > 0:
        first_idx = breakeven_indices[0]
        break_even_month = int(df_month.at[first_idx, 'Month'])
        # profits after break-even (monthly profit values)
        remaining_profits = df_month.loc[df_month['Month'] >= break_even_month, 'Monthly_Profit']
        avg_profit_after_breakeven = round(remaining_profits.mean(), 2) if not remaining_profits.empty else 0
        profit_after_break_even = remaining_profits.sum() if not remaining_profits.empty else 0
    else:
        break_even_month = None
        avg_profit_after_breakeven = 0
        profit_after_break_even = 0

    # Totals
    total_crossings = int(df_month['Sows_Crossed'].sum()) if 'Sows_Crossed' in df_month.columns else 0
    total_pigs_born = int(total_pigs_born)
    total_pigs_sold = int(total_pigs_sold)
    animals_left = int(animals_left)
    total_interest_paid = float(total_interest_paid) if 'total_interest_paid' in locals() or 'total_interest_paid' in globals() else 0.0

    # Total ROI (over simulation)
    total_roi_pct = (cumulative_cash_flow / (total_capital + first_sale_cash_needed)) * 100 if total_capital > 0 else 0

    # Average monthly profit (overall)
    average_monthly_profit  = df_month['Monthly_Profit'].mean()
    average_monthly_profit_after_loan  = df_month['Monthly_Cash_Flow'].mean()
   # Total ROI based on cash flow only
    # total_roi_pct = (cumulative_cash_flow / total_capital) * 100 if total_capital > 0 else 0

    # Calculate final asset value
    shed_remaining_value = shed_cost * max(0, (shed_life_years*12 - months)/(shed_life_years*12))
    sows_remaining_value = current_sows * sow_cost * max(0, (sow_life_years*12 - months)/(sow_life_years*12))
    growers_remaining_value = animals_left * 12000  # market value
    
    final_assets_value = shed_remaining_value + sows_remaining_value + growers_remaining_value
    
    # ROI including final assets
    roi_with_assets = ((cumulative_cash_flow + final_assets_value) / total_capital - 1) * 100 if total_capital > 0 else 0
    
    # Identify first and last cash flow (realized)
    realized_cash = df_month['Cumulative_Cash_Flow']
    first_idx = realized_cash.ne(0).idxmax()  # first non-zero cash flow
    last_idx = realized_cash.last_valid_index()  # last available month
    
    # Calculate number of years over realized period
    years_realized = (df_month.at[last_idx, 'Month'] - df_month.at[first_idx, 'Month'] + 1) / 12
    years = months / 12
    realized_cagr = ((cumulative_cash_flow + total_capital_invested/ total_capital_invested + first_sale_cash_needed) ** (1 / years)) - 1


    
    # CAGR on realized cash flows
    # --- Realized CAGR on cash flows ---
    # initial_outflow = first_sale_cash_needed if first_sale_cash_needed > 0 else 1  # avoid zero
    # final_inflow = cumulative_cash_flow + initial_outflow  # total cash in hand including initial outflow
    # years = months / 12
    # realized_cagr = ((final_inflow / initial_outflow + total_capital) ** (1/years) - 1) * 100 if initial_outflow > 0 else 0
    return df_month, df_year, total_sow_cost, shed_cost, first_sale_cash_needed, total_pigs_sold, total_pigs_born, animals_left, cumulative_cash_flow, total_interest_paid, break_even_month, profit_after_break_even, average_monthly_profit, avg_profit_after_breakeven, total_crossings, roi_with_assets, realized_cagr, total_roi_pct
# -------------------------------
# Streamlit UI
# -------------------------------
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
interest_rate_pct = st.sidebar.slider("Interest Rate (%)", 0, 20, 10, 1)
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
df_month, df_year, total_sow_cost, shed_cost_val, first_sale_wc, total_pigs_sold, total_pigs_born, animals_left, cumulative_cash_flow, total_interest_paid, break_even_month, profit_after_break_even, average_monthly_profit, avg_profit_after_breakeven, total_crossings, roi_with_assets, realized_cagr, total_roi_pct = sow_rotation_simulator(
    total_sows, piglets_per_cycle, piglet_mortality_pct / 100, abortion_rate_pct / 100,
    sow_feed_price, sow_feed_intake, grower_feed_price, fcr,
    final_weight, sale_price, management_fee, management_commission_pct / 100,
    supervisor_salary, worker_salary, n_workers, shed_cost, shed_life_years,
    sow_cost, sow_life_years, loan_amount, interest_rate_pct / 100, loan_tenure_years,
    moratorium_months, medicine_cost, electricity_cost, land_lease, months
)

# -------------------------------
# Display Summaries in Streamlit
# -------------------------------
st.subheader("Simulation Results")

st.write("Monthly Summary")
st.dataframe(df_month.drop(columns=['Month']))

st.write("Yearly Summary")
st.dataframe(df_year)

st.subheader("Financial Summary")
total_capital = total_sow_cost + shed_cost_val
st.write(f"Total Crossings Done: {total_crossings:,}")
st.write(f"Total Pigs Born: {total_pigs_born:,}")
st.write(f"Total Pigs Sold: {total_pigs_sold:,}")
st.write(f"Animals Remaining in Shed: {animals_left:,}")
st.write(f"Total Capital Invested (Shed + Sows): ₹{total_capital:,.2f}")
st.write(f"Working Capital till First Sale: ₹{first_sale_wc:,.2f}")

if break_even_month:
    st.write(f"Break-even Month: {break_even_month}")
else:
    st.write("Break-even: Not achieved within simulation period")

st.write(f"Profit After Break-even (cumulative): ₹{profit_after_break_even:,.0f}")
# st.write(f"Average Monthly Profit_after_dep: ₹{average_monthly_profit_after_dep:,.0f}")
st.write(f"average_monthly_profit: ₹{average_monthly_profit:,.0f}")
st.write(f"Average Monthly Profit after Break-even: ₹{avg_profit_after_breakeven:,.2f}")
st.write(f"Total Interest Paid Over Loan Tenure: ₹{total_interest_paid:,.0f}")
st.write(f"Total ROI: {total_roi_pct:.2f}%")   # if you still return total_roi_pct
st.write(f"Realized CAGR : {realized_cagr:.2f}%")
st.write(f"Total ROI after Asset liquidation): {roi_with_assets:.2f}%")




# -------------------------------
# Generate and Display Plots in Streamlit (Altair only)
# -------------------------------

import altair as alt

st.subheader("Simulation Plots")

# ---- Plot 1: Revenue vs Total Costs (Stacked Breakdown) ----
st.write("Revenue vs Total Costs (Stacked Breakdown)")
cost_components = ["Sow_Feed_Cost", "Grower_Feed_Cost", "Staff_Cost", 
                   "Other_Fixed_Costs", "Mgmt_Fee", "Mgmt_Comm", "Loan_EMI"]

# Melt cost data
df_costs_melt = df_month[["Month"] + cost_components].melt(
    id_vars="Month", var_name="Cost Component", value_name="Value"
)

# Stacked area chart for costs
area_chart = alt.Chart(df_costs_melt).mark_area(opacity=0.7).encode(
    x="Month:O",
    y="Value:Q",
    color=alt.Color("Cost Component", scale=alt.Scale(scheme="category20b")),
    tooltip=["Month", "Cost Component", "Value"]
)

# Revenue line
revenue_line = alt.Chart(df_month).mark_line(color="green", strokeWidth=2).encode(
    x="Month:O",
    y="Revenue:Q",
    tooltip=["Month", "Revenue"]
)

st.altair_chart(area_chart + revenue_line, use_container_width=True)


# ---- Plot 2: Monthly Profit ----
st.write("Monthly Profit Over Time")
profit_chart = alt.Chart(df_month).mark_line(color="blue").encode(
    x="Month:O",
    y="Monthly_Profit:Q",
    tooltip=["Month", "Monthly_Profit"]
).properties(height=400)

st.altair_chart(profit_chart, use_container_width=True)


# ---- Plot 3: Cumulative Cash Flow + Profit with Milestones ----
st.write("Cumulative Cash Flow & Profit Over Time (Milestones)")

df_cumulative = pd.DataFrame({
    "Month": df_month["Month"],
    "Month_Label": df_month["Month"],  # replace with Year-Month if available
    "Cumulative Cash Flow": df_month["Cumulative_Cash_Flow"]/1e5,
    "Cumulative Profit": (df_month["Monthly_Cash_Flow"].cumsum())/1e5,
})

df_cum_melt = df_cumulative.melt(id_vars=["Month", "Month_Label"], 
                                 var_name="Metric", value_name="Value")

# Base line chart
line_chart = alt.Chart(df_cum_melt).mark_line().encode(
    x=alt.X("Month_Label:O", title="Time (Months)"),
    y=alt.Y("Value:Q", title="Amount (₹ Lakhs)"),
    color="Metric",
    tooltip=["Month_Label", "Metric", "Value"]
)

# Break-even markers
rules = []
if break_even_month:
    rules.append(
        alt.Chart(pd.DataFrame({"Month_Label": [break_even_month]})).mark_rule(
            color="red", strokeDash=[6,2]
        ).encode(x="Month_Label:O")
    )

profit_break_even = next((i for i, val in enumerate(df_cumulative["Cumulative Profit"]) if val >= 0), None)
if profit_break_even is not None:
    rules.append(
        alt.Chart(pd.DataFrame({"Month_Label": [df_cumulative["Month"].iloc[profit_break_even]]})).mark_rule(
            color="orange", strokeDash=[6,2]
        ).encode(x="Month_Label:O")
    )

# Highlight max points
max_cf_idx = df_cumulative["Cumulative Cash Flow"].idxmax()
max_profit_idx = df_cumulative["Cumulative Profit"].idxmax()

points = alt.Chart(pd.DataFrame({
    "Month_Label": [
        df_cumulative["Month"].iloc[max_cf_idx],
        df_cumulative["Month"].iloc[max_profit_idx]
    ],
    "Value": [
        df_cumulative["Cumulative Cash Flow"].iloc[max_cf_idx],
        df_cumulative["Cumulative Profit"].iloc[max_profit_idx]
    ],
    "Metric": ["Max Cash Flow", "Max Profit"]
})).mark_point(size=100).encode(
    x="Month_Label:O",
    y="Value:Q",
    color="Metric",
    shape="Metric"
)

st.altair_chart(line_chart + sum(rules, alt.LayerChart()) + points, use_container_width=True)


# ---- Plot 4: Total Costs by Component ----
st.write("Total Costs by Component Over Simulation Period")
total_costs = df_month[cost_components].sum().reset_index()
total_costs.columns = ["Cost Component", "Total"]

bar_chart = alt.Chart(total_costs).mark_bar().encode(
    x=alt.X("Cost Component", sort="-y"),
    y="Total:Q",
    color=alt.Color("Cost Component", scale=alt.Scale(scheme="category20b")),
    tooltip=["Cost Component", "Total"]
).properties(height=500)

st.altair_chart(bar_chart, use_container_width=True)

# ROI & CAGR Comparison Graph
st.subheader("ROI & Realized CAGR Comparison")

df_roi_cagr = pd.DataFrame({
    "Metric": ["ROI (Cash Flow)", "ROI with Assets", "Realized CAGR"],
    "Value": [total_roi_pct, roi_with_assets, realized_cagr]
})

roi_chart = alt.Chart(df_roi_cagr).mark_bar(color='teal').encode(
    x=alt.X("Metric", sort=None),
    y=alt.Y("Value", title="Percentage (%)"),
    tooltip=["Metric", "Value"]
).properties(height=400)

st.altair_chart(roi_chart, use_container_width=True)

import altair as alt
import pandas as pd

# Prepare data
df_cumulative = pd.DataFrame({
    "Month": df_month["Month"],
    "Cumulative_Cash_Flow": df_month["Cumulative_Cash_Flow"],
    "Cumulative_Profit": df_month["Monthly_Cash_Flow"].cumsum(),
})

# Add ROI and CAGR as horizontal lines (percentages)
roi_line = pd.DataFrame({
    "Metric": ["ROI with Assets"]*len(df_cumulative),
    "Month": df_cumulative["Month"],
    "Value": [roi_with_assets]*len(df_cumulative)
})

cagr_line = pd.DataFrame({
    "Metric": ["Realized CAGR"]*len(df_cumulative),
    "Month": df_cumulative["Month"],
    "Value": [realized_cagr]*len(df_cumulative)
})

# Melt cash/ profit for line chart
df_melt = df_cumulative.melt(id_vars=["Month"], 
                             value_vars=["Cumulative_Cash_Flow", "Cumulative_Profit"],
                             var_name="Metric", value_name="Value")

# Combine all lines
df_all_lines = pd.concat([df_melt, roi_line, cagr_line], ignore_index=True)

# Chart
chart = alt.Chart(df_all_lines).mark_line(point=True).encode(
    x=alt.X("Month:Q", title="Month"),
    y=alt.Y("Value:Q", title="Amount / %"),
    color="Metric:N",
    tooltip=["Month", "Metric", "Value"]
).properties(
    height=400,
    width=800,
    title="Cumulative Cash Flow, Profit, ROI, and Realized CAGR"
)

st.altair_chart(chart, use_container_width=True)

st.subheader("ROI & Realized CAGR Over Time")

# Compute cumulative ROI and realized CAGR over time
cumulative_cash = df_month['Cumulative_Cash_Flow']
total_capital = total_sow_cost + shed_cost_val
months_array = df_month['Month']

# Cumulative ROI at each month
cumulative_roi = (cumulative_cash / total_capital) * 100

# Realized CAGR at each month (avoid first zero division)
initial_outflow = first_sale_wc if first_sale_wc > 0 else 1
years_elapsed = months_array / 12
realized_cagr_over_time = ((cumulative_cash + initial_outflow) / initial_outflow) ** (1/years_elapsed) - 1
realized_cagr_over_time = realized_cagr_over_time * 100  # convert to %

# Build dataframe for plotting
df_roi_cagr = pd.DataFrame({
    'Month': months_array,
    'Cumulative ROI (%)': cumulative_roi,
    'Realized CAGR (%)': realized_cagr_over_time
})

# Melt for Altair
df_roi_melt = df_roi_cagr.melt(id_vars='Month', var_name='Metric', value_name='Value')

# Plot
roi_cagr_chart = alt.Chart(df_roi_melt).mark_line(point=True).encode(
    x=alt.X('Month:O', title='Month'),
    y=alt.Y('Value:Q', title='Percentage'),
    color='Metric',
    tooltip=['Month', 'Metric', 'Value']
).properties(height=400)

st.altair_chart(roi_cagr_chart, use_container_width=True)

# # ---- Plot 5: ROI and CAGR Over Time ----
# st.write("ROI & Realized CAGR Over Time")

# # Cumulative ROI (including final assets proportionally by month)
# shed_remaining_series = shed_cost * (1 - (df_month['Month'] / (shed_life_years*12))).clip(lower=0)
# sows_remaining_series = total_sow_cost * (1 - (df_month['Month'] / (sow_life_years*12))).clip(lower=0)
# growers_remaining_series = df_month['Growers'] * final_weight * sale_price

# final_assets_series = shed_remaining_series + sows_remaining_series + growers_remaining_series
# cumulative_roi_with_assets = ((df_month['Cumulative_Cash_Flow'] + final_assets_series) / total_capital) * 100
# cumulative_roi_cash_only = (df_month['Cumulative_Cash_Flow'] / total_capital) * 100

# # Realized CAGR series (from first sale)
# initial_outflow_series = first_sale_wc if first_sale_wc > 0 else 1
# months_elapsed = df_month['Month']
# realized_cagr_series = ((df_month['Cumulative_Cash_Flow'] + initial_outflow_series) / initial_outflow_series) ** (1 / (months_elapsed / 12)) - 1
# realized_cagr_series = realized_cagr_series * 100

# df_roi_cagr_time = pd.DataFrame({
#     "Month": df_month['Month'],
#     "ROI_Cash": cumulative_roi_cash_only,
#     "ROI_with_Assets": cumulative_roi_with_assets,
#     "Realized_CAGR": realized_cagr_series
# })

# df_roi_cagr_melt = df_roi_cagr_time.melt(id_vars=["Month"], var_name="Metric", value_name="Value")

# roi_cagr_line = alt.Chart(df_roi_cagr_melt).mark_line(point=True).encode(
#     x="Month:O",
#     y=alt.Y("Value", title="Percentage (%)"),
#     color="Metric",
#     tooltip=["Month", "Metric", "Value"]
# ).properties(height=400)

# st.altair_chart(roi_cagr_line, use_container_width=True)

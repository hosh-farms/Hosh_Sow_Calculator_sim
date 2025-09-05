Got it — we can make everything as sliders, remove the “Run Simulation” button, and fix the cumulative cash flow so it correctly starts with -(initial capital + working capital) and then adds monthly cash flow.

Here’s the updated full code:

import streamlit as st
import pandas as pd
import altair as alt

# -------------------------------
# Sow Rotation Simulator
# -------------------------------
def sow_rotation_simulator(total_sows, piglets_per_cycle, piglet_mortality, abortion_rate,
                           sow_feed_price, sow_feed_intake, grower_feed_price, fcr,
                           final_weight, sale_price, management_fee, management_commission,
                           supervisor_salary, worker_salary, n_workers, shed_cost,
                           shed_life_years, sow_cost, sow_life_years, loan_amount,
                           interest_rate, loan_tenure_years, moratorium_months,
                           medicine_cost, electricity_cost, land_lease, months):
    
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
    total_capital = shed_cost + total_sow_cost
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

        for batch in batches:
            if batch['grower_end_month'] <= month and not batch['sold'] and batch not in ready_for_sale_batches:
                ready_for_sale_batches.append(batch)

        sold_pigs = 0
        revenue = 0
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
            ready_for_sale_batches = [b for b in ready_for_sale_batches if b['batch_id'] not in batches_sold_ids]

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
        monthly_cash_flow = monthly_profit - loan_payment

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

    initial_investment = shed_cost + total_sow_cost + first_sale_cash_needed
    # Fix cumulative cash flow correctly
    cumulative_cash_flow = []
    running_cash = -initial_investment
    for val in df_month["Monthly_Profit"] - df_month["Loan_EMI"]:
        running_cash += val
        cumulative_cash_flow.append(running_cash)
    df_month["Cumulative_Cash_Flow"] = cumulative_cash_flow

    # Summary
    total_cash_returned = df_month["Monthly_Profit"].sum()
    roi_pct = (total_cash_returned / initial_investment) * 100
    years = months / 12
    cagr = ((total_cash_returned + initial_investment)/initial_investment)**(1/years) - 1
    total_pigs_left = int(sum(batch['piglets'] for batch in batches if not batch['sold'] and batch['grower_end_month'] > months))
    total_crossings = df_month["Sows_Crossed"].sum()
    total_interest_paid = df_month["Loan_EMI"].sum() - loan_amount if loan_amount>0 else 0

    break_even_month = None
    running_cash_temp = -initial_investment
    for i, val in enumerate(df_month["Monthly_Profit"] - df_month["Loan_EMI"]):
        running_cash_temp += val
        if running_cash_temp >= 0:
            break_even_month = i + 1
            break

    summary = {
        "Initial Investment (INR)": initial_investment,
        "Total Pigs Born": total_pigs_born,
        "Total Pigs Sold": total_pigs_sold,
        "Pigs Remaining": total_pigs_left,
        "Total Sows Crossed": total_crossings,
        "Total Cash Returned (INR)": total_cash_returned,
        "ROI (%)": roi_pct,
        "CAGR (%)": cagr*100,
        "Break-even Month": break_even_month,
        "Total Interest Paid": total_interest_paid
    }

    return df_month, summary

# -------------------------------
# Streamlit Interface
# -------------------------------
st.title("Sow Farm Monthly Simulator")

# --- Sliders Only ---
total_sows = st.slider("Total Sows", 1, 100, 30)
piglets_per_cycle = st.slider("Piglets per Cycle", 5, 20, 10)
piglet_mortality = st.slider("Piglet Mortality (%)", 0.0, 0.5, 0.07)
abortion_rate = st.slider("Abortion Rate (%)", 0.0, 0.3, 0.0)
sow_feed_price = st.slider("Sow Feed Price per kg", 1, 100, 30)
sow_feed_intake = st.slider("Sow Feed Intake kg/day", 0.5, 10.0, 2.8)
grower_feed_price = st.slider("Grower Feed Price per kg", 1, 100, 30)
fcr = st.slider("FCR", 1.0, 5.0, 3.1)
final_weight = st.slider("Final Weight (kg)", 50, 150, 105)
sale_price = st.slider("Sale Price per kg", 50, 500, 180)
supervisor_salary = st.slider("Supervisor Salary", 0, 100000, 25000)
worker_salary = st.slider("Worker Salary", 0, 50000, 18000)
n_workers = st.slider("Number of Workers", 0, 10, 2)
shed_cost = st.slider("Shed Cost", 100000, 5000000, 1500000)
shed_life_years = st.slider("Shed Life (Years)", 1, 20, 10)
sow_cost = st.slider("Sow Cost", 1000, 100000, 35000)
sow_life_years = st.slider("Sow Life (Years)", 1, 10, 4)
loan_amount = st.slider("Loan Amount", 0, 5000000, 4000000)
interest_rate = st.slider("Loan Interest Rate", 0.0, 0.5, 0.121)
loan_tenure_years = st.slider("Loan Tenure (Years)", 1, 20, 5)
moratorium_months = st.slider("Moratorium (Months)", 0, 12, 0)
medicine_cost = st.slider("Medicine Cost per Month", 0, 50000, 10000)
electricity_cost = st.slider("Electricity Cost per Month", 0, 50000, 5000)
land_lease = st.slider("Land Lease per Month", 0, 50000, 10000)
management_fee = st.slider("Management Fee per Month", 0, 100000, 0)
management_commission = st.slider("Management Commission (%)", 0.0, 1.0, 0.0)
months = st.slider("Simulation Months", 12, 120, 60)

# --- Auto Run Simulation ---
df_month, summary = sow_rotation_simulator(total_sows, piglets_per_cycle, piglet_mortality, abortion_rate,
                                           sow_feed_price, sow_feed_intake, grower_feed_price, fcr,
                                           final_weight, sale_price, management_fee, management_commission,
                                           supervisor_salary, worker_salary, n_workers, shed_cost,
                                           shed_life_years, sow_cost, sow_life_years, loan_amount,
                                           interest_rate, loan_tenure_years, moratorium_months,
                                           medicine_cost, electricity_cost, land_lease, months)

st.subheader("Monthly Data")
st.dataframe(df_month)

st.subheader("Summary")
for k, v in summary.items():
    st.write(f"**{k}:** {v}")

st.subheader("Plots")
chart_cf = alt.Chart(df_month).mark_line().encode(
    x='Month',
    y='Cumulative_Cash_Flow'
).properties(title='Cumulative Cash Flow Over Months')
st.altair_chart(chart_cf, use_container_width=True)

chart_profit = alt.Chart(df_month).mark_line(color='green').encode(
    x='Month',
    y='Monthly_Profit'
).properties(title='Monthly Profit')
st.altair_chart(chart_profit, use_container_width=True)

chart_revenue = alt.Chart(df_month).mark_line(color='orange').encode(
    x='Month',
    y='Revenue'
).properties(title='Monthly Revenue')
st.altair_chart(chart_revenue, use_container_width=True)

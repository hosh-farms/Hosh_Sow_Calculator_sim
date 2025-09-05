# Save this file and run with:
# streamlit run sowcalc_streamlit_final.py

import streamlit as st
import pandas as pd
import math
import altair as alt

# -------------------------------
# Sow Rotation Simulator with realistic monthly sales
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
    interest_rate=0.121,
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

    df_year = df_month.groupby(((df_month['Month']-1)//12)*12).sum()
    df_year.index = [f"Year {i+1}" for i in range(len(df_year))]

    animals_left = int(sum(batch['piglets'] for batch in batches if not batch['sold'] and batch['grower_end_month'] > months))

    # Recalculate interest paid
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

    total_sow_cost = total_sows * sow_cost
    shed_cost_val = shed_cost
    initial_investment = shed_cost_val + total_sow_cost + first_sale_cash_needed

    # ----------------- CORRECT CUMULATIVE CASH FLOW -----------------
    cumulative_cash_flow = [initial_investment]
    for idx, row in df_month.iterrows():
        cumulative_cash_flow.append(cumulative_cash_flow[-1] + row['Monthly_Profit'] - row['Loan_EMI'])
    cumulative_cash_flow = cumulative_cash_flow[1:]
    df_month["Cumulative_Cash_Flow"] = cumulative_cash_flow

    # ----------------- BREAK-EVEN & PROFIT -----------------
    break_even_month = None
    running_cash = initial_investment
    for i, cash in enumerate(df_month["Monthly_Cash_Flow"]):
        running_cash += cash
        if running_cash >= initial_investment:
            break_even_month = i + 1
            break

    if break_even_month:
        profit_after_break_even = df_month["Monthly_Profit"].iloc[break_even_month:].sum()
        months_after_breakeven = len(df_month) - break_even_month
        avg_profit_after_breakeven = profit_after_break_even / months_after_breakeven if months_after_breakeven > 0 else 0
    else:
        profit_after_break_even = 0
        avg_profit_after_breakeven = 0

    average_monthly_profit = df_month["Monthly_Profit"].mean()

    # ROI & CAGR
    total_cash_returned = df_month["Monthly_Cash_Flow"].sum() + initial_investment
    roi_cash_pct = (total_cash_returned - initial_investment) / initial_investment * 100
    years = months / 12
    realized_cagr = (total_cash_returned / initial_investment) ** (1/years) - 1

    roi_with_assets_pct = roi_cash_pct  # can include assets if needed

    total_crossings = df_month["Sows_Crossed"].sum()


    return (
        df_month,
        df_year,
        total_sow_cost,
        shed_cost,
        first_sale_cash_needed,
        total_pigs_sold,
        total_pigs_born,
        animals_left,
        df_month["Cumulative_Cash_Flow"].iloc[-1],
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
# (Add all sliders and UI controls here exactly as before...)

# -------------------------------
# Run Simulation
# -------------------------------
df_month, df_year, total_sow_cost, shed_cost_val, first_sale_cash_needed, total_pigs_sold, total_pigs_born, animals_left, cumulative_cash_flow_scalar, total_interest_paid, break_even_month, profit_after_break_even, average_monthly_profit, avg_profit_after_breakeven, total_crossings, roi_with_assets_pct, roi_cash_pct, realized_cagr = sow_rotation_simulator(
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
)

st.subheader("Monthly Summary")
st.dataframe(df_month.head(120))

st.subheader("Yearly Summary")
st.dataframe(df_year)

st.subheader("Financial Summary")
st.write(f"Total Crossings Done: {total_crossings:,}")
st.write(f"Total Pigs Born: {total_pigs_born:,}")
st.write(f"Total Pigs Sold: {total_pigs_sold:,}")
st.write(f"Animals Remaining in Shed: {animals_left:,}")
st.write(f"Initial Investment: ₹{shed_cost_val + total_sow_cost + first_sale_cash_needed:,.0f}")
st.write(f"Break-even Month: {break_even_month}")
st.write(f"Profit After Break-even: ₹{profit_after_break_even:,.0f}")
st.write(f"Average Monthly Profit: ₹{average_monthly_profit:,.0f}")
st.write(f"Average Monthly Profit After Break-even: ₹{avg_profit_after_breakeven:,.0f}")
st.write(f"Total Interest Paid: ₹{total_interest_paid:,.0f}")
st.write(f"ROI (Cash Only): {roi_cash_pct:.2f}%")
st.write(f"Realized CAGR: {realized_cagr*100:.2f}%")

import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------
# Sow Rotation Simulator Function
# -------------------------------
def sow_rotation_simulator(
    total_sows=30,
    piglets_per_cycle=8,
    sow_mortality=0.033,
    piglet_mortality=0.03,
    abortion_rate=0.03,
    sow_feed_price=32,
    sow_feed_intake=2.8,
    grower_feed_price=28,
    fcr=3.2,
    final_weight=105,
    sale_price=180,
    management_fee=50000,
    management_commission=0.05,
    supervisor_salary=25000,
    worker_salary=18000,
    n_workers=2,
    shed_cost=1_000_000,
    shed_life_years=10,
    sow_cost=1_050_000,
    sow_life_years=4,
    loan_amount=0,
    interest_rate=0.1,
    loan_tenure_years=5,
    moratorium_months=0,
    medicine_cost=10000,
    electricity_cost=5000,
    land_lease=10000,
    months=60
):
    """Run sow rotation simulation and return monthly and yearly summaries."""
    current_sows = total_sows
    monthly_data = []

    # Depreciation rates
    shed_dep_rate = 1 / (shed_life_years * 12)
    sow_dep_rate = 1 / (sow_life_years * 12)

    # Loan calculation
    total_months = loan_tenure_years * 12
    monthly_rate = interest_rate / 12
    emi = 0
    if loan_amount > 0 and total_months > 0:
        emi = loan_amount * monthly_rate * (1 + monthly_rate)**total_months / ((1 + monthly_rate)**total_months - 1)
    loan_balance = loan_amount

    # Average sow cycle (months)
    average_cycle_length = 3.8 + 1.3 + 0.33
    sows_to_mate_per_month = total_sows / average_cycle_length

    batches = []
    ready_for_sale_batches = []
    total_capital_invested = shed_cost + sow_cost
    cumulative_cash_flow = -total_capital_invested

    for month in range(1, months + 1):
        sow_feed_cost = current_sows * sow_feed_intake * 30 * sow_feed_price
        staff_cost = supervisor_salary + n_workers * worker_salary
        mgmt_fixed = management_fee

        sows_mated_this_month = 0
        sows_aborted_this_month = 0
        sow_mortality_this_month = 0

        # Mate sows starting month 2
        if month >= 2:
            sows_to_mate = sows_to_mate_per_month
            sows_mated_this_month = sows_to_mate
            sows_pregnant = sows_to_mate * (1 - abortion_rate)
            sows_aborted_this_month = sows_to_mate - sows_pregnant
            sow_mortality_this_month = current_sows * (sow_mortality / 12)
            current_sows -= sow_mortality_this_month

            if sows_pregnant > 0:
                farrow_month = month + 4
                wean_month = farrow_month + 1
                grower_start_month = wean_month
                grower_end_month = grower_start_month + 6
                piglets = sows_pregnant * piglets_per_cycle * (1 - piglet_mortality)
                batches.append({
                    'batch_id': len(batches) + 1,
                    'farrow_month': farrow_month,
                    'wean_month': wean_month,
                    'grower_start_month': grower_start_month,
                    'grower_end_month': grower_end_month,
                    'piglets': piglets,
                    'grower_feed_per_month': (piglets * fcr * final_weight) / 6
                })

        # Monthly counters
        piglets_with_sow = 0
        current_growers = 0
        sold_pigs = 0
        revenue = 0
        grower_feed_cost = 0
        batches_to_remove_permanently = []

        batches_this_month = batches.copy()
        for batch in batches_this_month:
            if batch['farrow_month'] <= month < batch['wean_month']:
                piglets_with_sow += batch['piglets']
            if batch['grower_start_month'] <= month < batch['grower_end_month']:
                current_growers += batch['piglets']
                grower_feed_cost += batch['grower_feed_per_month'] * grower_feed_price
            if batch['grower_end_month'] == month:
                ready_for_sale_batches.append(batch)

        # Bimonthly sales starting month 13
        if month >= 13 and (month - 13) % 2 == 0 and ready_for_sale_batches:
            pigs_sold_this_period = 0
            batches_sold_ids = []
            sale_period_start = month - 1
            sale_period_end = month
            batches_to_sell = [b for b in ready_for_sale_batches if sale_period_start <= b['grower_end_month'] <= sale_period_end]
            for b in batches_to_sell:
                pigs_sold_batch = b['piglets'] * 0.97
                pigs_sold_this_period += pigs_sold_batch
                batches_sold_ids.append(b['batch_id'])
            revenue += pigs_sold_this_period * final_weight * sale_price
            sold_pigs = pigs_sold_this_period
            ready_for_sale_batches = [b for b in ready_for_sale_batches if b['batch_id'] not in batches_sold_ids]
            for batch_id in batches_sold_ids:
                for batch in batches:
                    if batch['batch_id'] == batch_id:
                        batches_to_remove_permanently.append(batch)
                        break

       

        for batch in batches_to_remove_permanently:
            if batch in batches:
                batches.remove(batch)

        current_growers -= sold_pigs
        mgmt_comm_cost = revenue * management_commission
        other_fixed = medicine_cost + electricity_cost + land_lease
        total_operating_cost = sow_feed_cost + grower_feed_cost + staff_cost + mgmt_fixed + mgmt_comm_cost + other_fixed
        dep = shed_cost * shed_dep_rate + sow_cost * sow_dep_rate

        # Loan EMI
        if month <= moratorium_months:
            loan_payment = loan_balance * monthly_rate
        elif month <= total_months:
            interest = loan_balance * monthly_rate
            principal = emi - interest
            loan_balance -= principal
            loan_payment = emi
        else:
            loan_payment = 0

        monthly_profit = revenue - total_operating_cost - dep - loan_payment
        monthly_profit_percentage = (monthly_profit / revenue * 100) if revenue > 0 else 0
        monthly_cash_flow = revenue - total_operating_cost - loan_payment
        cumulative_cash_flow += monthly_cash_flow

        monthly_data.append({
            'Month': month,
            'Piglets_Born_Alive': piglets_with_sow,
            'Growers': current_growers,
            'Sold_Pigs': sold_pigs,
            'Sows_Mated': sows_mated_this_month,
            'Revenue': round(revenue),
            'Sow_Feed_Cost': round(sow_feed_cost),
            'Grower_Feed_Cost': round(grower_feed_cost),
            'Staff_Cost': round(staff_cost),
            'Mgmt_Fee': round(mgmt_fixed),
            'Mgmt_Comm': round(mgmt_comm_cost),
            'Other_Fixed_Costs': round(other_fixed),
            'Total_Operating_Cost': round(total_operating_cost),
            'Depreciation': round(dep),
            'Loan_EMI': round(loan_payment),
            'Monthly_Profit': round(monthly_profit),
            'Monthly_Profit_%': monthly_profit_percentage,
            'Monthly_Cash_Flow': round(monthly_cash_flow),
            'Cumulative_Cash_Flow': round(cumulative_cash_flow)
        })

    df_month = pd.DataFrame(monthly_data)
    df_month['Year'] = ((df_month['Month'] - 1) // 12) + 1
    df_year = df_month.groupby('Year').sum()
    df_year.index = [f"Year {i}" for i in df_year.index]
    df_year['Cash_Profit'] = df_year['Revenue'] - df_year['Total_Operating_Cost']
    df_year['Profit_After_Dep_Loan'] = df_year['Cash_Profit'] - df_year['Depreciation'] - df_year['Loan_EMI']
    df_year['Total_Capital_Invested'] = total_capital_invested
    cumulative_cash_flow_with_assets = cumulative_cash_flow
    return df_month, df_year, total_capital_invested, cumulative_cash_flow_with_assets

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("🐷 House of Supreme Ham Simulator 50 sows")
st.sidebar.header("Simulation Parameters")

# Sow & Piglet
total_sows = st.sidebar.slider("Total Sows", 10, 50, 30, 5)
piglets_per_cycle = st.sidebar.slider("Piglets per Cycle", 5, 20, 8)
sow_mortality = st.sidebar.slider("Sow Mortality Rate", 0.0, 0.5, 0.033, 0.001)
piglet_mortality = st.sidebar.slider("Piglet Mortality Rate", 0.0, 0.5, 0.03, 0.001)
abortion_rate = st.sidebar.slider("Abortion Rate", 0.0, 0.5, 0.03, 0.001)

# Feed & Sale
sow_feed_price = st.sidebar.number_input("Sow Feed Price (₹/kg)", 0, 50, 32)
sow_feed_intake = st.sidebar.slider("Sow Feed Intake (kg/day)", 0.0, 5.0, 2.8)
grower_feed_price = st.sidebar.number_input("Grower Feed Price (₹/kg)", 0, 50, 28)
fcr = st.sidebar.slider("Feed Conversion Ratio (FCR)", 2.0, 4.0, 3.2)
final_weight = st.sidebar.number_input("Final Weight (kg)", 80, 120, 105)
sale_price = st.sidebar.number_input("Sale Price (₹/kg)", 100, 300, 180)

# Management
management_fee = st.sidebar.number_input("Management Fee (Monthly)", 0, 200000, 50000)
management_commission = st.sidebar.slider("Management Commission Rate", 0.0, 0.2, 0.05, 0.001)
supervisor_salary = st.sidebar.number_input("Supervisor Salary", 0, 50000, 25000)
worker_salary = st.sidebar.number_input("Worker Salary", 0, 30000, 18000)
n_workers = st.sidebar.number_input("Number of Workers", 0, 10, 2)

# Capital
shed_cost = st.sidebar.number_input("Shed Cost", 500000, 5000000, 1000000)
shed_life_years = st.sidebar.number_input("Shed Life (Years)", 1, 30, 10)
sow_cost = st.sidebar.number_input("Sow Cost (per sow)", 500000, 3000000, 1050000)
sow_life_years = st.sidebar.number_input("Sow Life (Years)", 1, 10, 4)

# Loan
loan_amount = st.sidebar.number_input("Loan Amount", 0, 10000000, 0)
interest_rate = st.sidebar.slider("Interest Rate (Annual)", 0.0, 0.2, 0.1, 0.001)
loan_tenure_years = st.sidebar.number_input("Loan Tenure (Years)", 1, 20, 5)
moratorium_months = st.sidebar.number_input("Moratorium Period (Months)", 0, 24, 0)

# Other Fixed Costs
medicine_cost = st.sidebar.number_input("Medicine Cost", 0, 50000, 10000)
electricity_cost = st.sidebar.number_input("Electricity Cost", 0, 50000, 5000)
land_lease = st.sidebar.number_input("Land Lease", 0, 50000, 10000)

# Simulation Duration
months = st.sidebar.slider("Simulation Duration (Months)", 12, 120, 60, 12)

# Run Simulation
df_month, df_year, total_capital_invested, cumulative_cash_flow_with_assets = sow_rotation_simulator(
    total_sows, piglets_per_cycle, sow_mortality, piglet_mortality, abortion_rate,
    sow_feed_price, sow_feed_intake, grower_feed_price, fcr, final_weight, sale_price,
    management_fee, management_commission, supervisor_salary, worker_salary, n_workers,
    shed_cost, shed_life_years, sow_cost, sow_life_years,
    loan_amount, interest_rate, loan_tenure_years, moratorium_months,
    medicine_cost, electricity_cost, land_lease, months
)

# Display
st.header("📊 Monthly Summary")
st.dataframe(df_month)

st.header("📈 Yearly Summary")
st.dataframe(df_year)

st.header("💰 Financial Summary")
st.write(f"Total Capital Initially Invested: ₹{total_capital_invested:,.2f}")
st.write(f"Cumulative Cash Flow after {months} months: ₹{cumulative_cash_flow_with_assets:,.2f}")
roi = (cumulative_cash_flow_with_assets / total_capital_invested) * 100
st.write(f"Return on Investment (ROI): {roi:.2f}%")

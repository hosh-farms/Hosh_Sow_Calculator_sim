import streamlit as st
import pandas as pd

# -------------------------------
# Sow Rotation Simulator with realistic batch sales
# -------------------------------
def sow_rotation_simulator(
    total_sows=30,
    piglets_per_cycle=8,
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
    total_capital_invested = shed_cost + sow_cost
    cumulative_cash_flow = -total_capital_invested

    for month in range(1, months + 1):
        sow_feed_cost = current_sows * sow_feed_intake * 30 * sow_feed_price
        staff_cost = supervisor_salary + n_workers * worker_salary
        mgmt_fixed = management_fee

        sows_mated_this_month = 0

        # Mate sows starting month 2
        if month >= 2:
            sows_to_mate = sows_to_mate_per_month
            sows_mated_this_month = sows_to_mate
            sows_pregnant = sows_to_mate * (1 - abortion_rate)
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
                    'grower_feed_per_month': (piglets * fcr * final_weight) / 6,
                    'sold': False
                })

        # Count piglets in lactation
        piglets_with_sow = sum(batch['piglets'] for batch in batches if batch['farrow_month'] <= month < batch['wean_month'])
        # Count growers
        current_growers = sum(batch['piglets'] for batch in batches if batch['grower_start_month'] <= month < batch['grower_end_month'])
        # Calculate grower feed
        grower_feed_cost = sum(batch['grower_feed_per_month'] * grower_feed_price for batch in batches if batch['grower_start_month'] <= month < batch['grower_end_month'])

        # Identify batches ready for sale this month
        for batch in batches:
            if batch['grower_end_month'] <= month and not batch['sold'] and batch not in ready_for_sale_batches:
                ready_for_sale_batches.append(batch)

        sold_pigs = 0
        revenue = 0
        # Bimonthly sale logic
        if month >= 13 and (month - 13) % 2 == 0 and ready_for_sale_batches:
            pigs_sold_this_period = 0
            batches_sold_ids = []
            sale_period_start = month - 1
            sale_period_end = month

            # Find batches that became ready in last 2 months
            batches_to_sell = [b for b in ready_for_sale_batches if sale_period_start <= b['grower_end_month'] <= sale_period_end]

            for batch in batches_to_sell:
                pigs_sold_batch = batch['piglets']
                pigs_sold_this_period += pigs_sold_batch
                batch['sold'] = True
                batches_sold_ids.append(batch['batch_id'])

            revenue += pigs_sold_this_period * final_weight * sale_price
            sold_pigs = pigs_sold_this_period
            current_growers -= sold_pigs  # Deduct sold pigs from growers

        mgmt_comm_cost = revenue * management_commission
        other_fixed = medicine_cost + electricity_cost + land_lease
        total_operating_cost = sow_feed_cost + grower_feed_cost + staff_cost + mgmt_fixed + mgmt_comm_cost + other_fixed
        dep = shed_cost * shed_dep_rate + sow_cost * sow_dep_rate

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
st.title("🐷 House of Supreme Ham Simulator")
st.sidebar.header("Simulation Parameters")

# Sow & Piglet
total_sows = st.sidebar.slider("Total Sows", 10, 200, 30, 5)
piglets_per_cycle = st.sidebar.slider("Piglets per Cycle", 5, 15, 8)
piglet_mortality_pct = st.sidebar.slider("Piglet Mortality (%)", 0, 50, 3, 1)
piglet_mortality = piglet_mortality_pct / 100
abortion_rate_pct = st.sidebar.slider("Abortion Rate (%)", 0, 50, 3, 1)
abortion_rate = abortion_rate_pct / 100

# Feed & Sale
sow_feed_price = st.sidebar.number_input("Sow Feed Price (₹/kg)", 0, 50, 32)
sow_feed_intake = st.sidebar.slider("Sow Feed Intake (kg/day)", 0.0, 5.0, 2.8, 0.1)
grower_feed_price = st.sidebar.number_input("Grower Feed Price (₹/kg)", 0, 50, 28)
fcr = st.sidebar.slider("Feed Conversion Ratio (FCR)", 2.0, 4.0, 3.2, 0.1)
final_weight = st.sidebar.number_input("Final Weight (kg)", 80, 120, 105)
sale_price = st.sidebar.number_input("Sale Price (₹/kg)", 100, 300, 180)

# Management
management_fee = st.sidebar.number_input("Management Fee (Monthly)", 0, 200000, 50000)
management_commission_pct = st.sidebar.slider("Management Commission (%)", 0, 20, 5, 1)
management_commission = management_commission_pct / 100
supervisor_salary = st.sidebar.number_input("Supervisor Salary", 0, 50000, 25000)
worker_salary = st.sidebar.number_input("Worker Salary", 0, 30000, 18000)
n_workers = st.sidebar.slider("Number of Workers", 0, 10, 2, 1)

# Capital Costs
shed_cost = st.sidebar.number_input("Shed Cost", 500000, 5000000, 1000000, 100000)
shed_life_years = st.sidebar.number_input("Shed Life (Years)", 1, 30, 10)
sow_cost = st.sidebar.number_input("Sow Cost (per sow)", 500000, 3000000, 1050000, 100000)
sow_life_years = st.sidebar.number_input("Sow Life (Years)", 1, 10, 4)

# Loan
loan_amount = st.sidebar.number_input("Loan Amount", 0, 10000000, 0, 100000)
interest_rate_pct = st.sidebar.slider("Interest Rate (%)", 0, 20, 10, 1)
interest_rate = interest_rate_pct / 100
loan_tenure_years = st.sidebar.number_input("Loan Tenure (Years)", 1, 20, 5)
moratorium_months = st.sidebar.number_input("Moratorium Period (Months)", 0, 24, 0)

# Other Fixed Costs
medicine_cost = st.sidebar.number_input("Medicine Cost (Monthly)", 0, 50000, 10000, 1000)
electricity_cost = st.sidebar.number_input("Electricity Cost (Monthly)", 0, 50000, 5000, 1000)
land_lease = st.sidebar.number_input("Land Lease (Monthly)", 0, 50000, 10000, 1000)

# Simulation Duration
months = st.sidebar.slider("Simulation Duration (Months)", 12, 120, 60, 12)

# -------------------------------
# Run Simulator
# -------------------------------
df_month, df_year, total_capital, cumulative_cash_flow = sow_rotation_simulator(
    total_sows, piglets_per_cycle, piglet_mortality, abortion_rate,
    sow_feed_price, sow_feed_intake, grower_feed_price, fcr,
    final_weight, sale_price, management_fee, management_commission,
    supervisor_salary, worker_salary, n_workers, shed_cost, shed_life_years,
    sow_cost, sow_life_years, loan_amount, interest_rate, loan_tenure_years,
    moratorium_months, medicine_cost, electricity_cost, land_lease, months
)

st.subheader("Monthly Summary")
st.dataframe(df_month)

st.subheader("Yearly Summary")
st.dataframe(df_year)

st.subheader("Financial Summary")
st.write(f"Total Capital Invested: ₹{total_capital:,.2f}")
st.write(f"Cumulative Cash Flow: ₹{cumulative_cash_flow:,.2f}")

# Calculate ROI
roi = (cumulative_cash_flow / total_capital) * 100 if total_capital > 0 else 0
st.write(f"Return on Investment (ROI): {roi:.2f}%")

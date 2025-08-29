import streamlit as st
import pandas as pd

# -------------------------------
# Sow Rotation Simulator
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
    # -------------------------------
    # Depreciation & Loan setup
    # -------------------------------
    shed_dep_rate = 1 / (shed_life_years * 12)
    sow_dep_rate = 1 / (sow_life_years * 12)

    total_months = loan_tenure_years * 12
    monthly_rate = interest_rate / 12
    emi = 0
    if loan_amount > 0 and total_months > 0:
        emi = loan_amount * monthly_rate * (1 + monthly_rate)**total_months / ((1 + monthly_rate)**total_months - 1)
    loan_balance = loan_amount

    # -------------------------------
    # Sow cycle setup
    # -------------------------------
    average_cycle_length = 3.8 + 1.3 + 0.33
    sows_to_mate_per_month = total_sows / average_cycle_length

    batches = []
    ready_for_sale_batches = []
    cumulative_cash_flow = 0
    monthly_data = []

    # Sow & shed total cost
    total_sow_cost = sow_cost * total_sows
    total_capital_invested = total_sow_cost + shed_cost

    # Track cumulative pigs sold
    cumulative_sold_pigs = 0

    for month in range(1, months + 1):
        # -------------------------------
        # Monthly costs
        # -------------------------------
        sow_feed_cost = total_sows * sow_feed_intake * 30 * sow_feed_price
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
        # Grower feed cost
        grower_feed_cost = sum(batch['grower_feed_per_month'] * grower_feed_price for batch in batches if batch['grower_start_month'] <= month < batch['grower_end_month'])

        # Identify batches ready for sale
        for batch in batches:
            if batch['grower_end_month'] <= month and not batch['sold'] and batch not in ready_for_sale_batches:
                ready_for_sale_batches.append(batch)

        sold_pigs = 0
        revenue = 0

        # Bimonthly sale logic
        if month >= 13 and (month - 13) % 2 == 0 and ready_for_sale_batches:
            pigs_sold_this_period = 0
            sale_period_start = month - 1
            sale_period_end = month
            batches_to_sell = [b for b in ready_for_sale_batches if sale_period_start <= b['grower_end_month'] <= sale_period_end]

            for batch in batches_to_sell:
                pigs_sold_batch = batch['piglets']
                pigs_sold_this_period += pigs_sold_batch
                batch['sold'] = True

            revenue += pigs_sold_this_period * final_weight * sale_price
            sold_pigs = pigs_sold_this_period
            cumulative_sold_pigs += sold_pigs
            current_growers -= sold_pigs  # Deduct sold pigs

        # Operating costs
        mgmt_comm_cost = revenue * management_commission
        other_fixed = medicine_cost + electricity_cost + land_lease
        total_operating_cost = sow_feed_cost + grower_feed_cost + staff_cost + mgmt_fixed + mgmt_comm_cost + other_fixed
        dep = shed_cost * shed_dep_rate + total_sow_cost * sow_dep_rate

        # Loan
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

    # -------------------------------
    # Dataframes
    # -------------------------------
    df_month = pd.DataFrame(monthly_data)

    # Yearly summary
    df_year = df_month.groupby((df_month.index // 12) + 1).sum()
    df_year.index = [f"Year {i}" for i in df_year.index]
    df_year['Cash_Profit'] = df_year['Revenue'] - df_year['Total_Operating_Cost']
    df_year['Profit_After_Dep_Loan'] = df_year['Cash_Profit'] - df_year['Depreciation'] - df_year['Loan_EMI']

    # -------------------------------
    # Farm summary
    # -------------------------------
    # Working capital until first sale
    first_sale_month = min([m for m, v in enumerate(df_month['Sold_Pigs'], 1) if v > 0], default=0)
    working_capital = df_month.loc[df_month.index < first_sale_month, 'Total_Operating_Cost'].sum() if first_sale_month > 0 else df_month['Total_Operating_Cost'].sum()

    total_pigs_born = sum(batch['piglets'] for batch in batches)
    animals_left_in_shed = total_sows + sum(batch['piglets'] for batch in batches if not batch['sold'])

    return (df_month, df_year, total_capital_invested, cumulative_cash_flow,
            total_sow_cost, shed_cost, working_capital,
            cumulative_sold_pigs, total_pigs_born, animals_left_in_shed)

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("🐷 House of Supreme Ham Simulator")
st.sidebar.header("Simulation Parameters")

# Sow & Piglet
total_sows = st.sidebar.slider("Total Sows", 10, 200, 30, 5)
piglets_per_cycle = st.sidebar.slider("Piglets per Cycle", 5, 15, 8)
piglet_mortality_pct = st.sidebar.slider("Piglet Mortality (%)", 0, 50, 3, 1

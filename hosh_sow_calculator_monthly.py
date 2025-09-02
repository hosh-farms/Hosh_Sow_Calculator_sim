import streamlit as st
import pandas as pd

# -------------------------------
# Sow Rotation Simulator with realistic monthly sales
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
    total_sow_cost = sow_cost * total_sows
    total_capital_invested = shed_cost + total_sow_cost
    cumulative_cash_flow = -total_capital_invested
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

        monthly_profit = revenue - total_operating_cost - dep - loan_payment
        monthly_cash_flow = revenue - total_operating_cost - loan_payment
        cumulative_cash_flow += monthly_cash_flow

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
            'Loan_EMI': round(loan_payment),
            'Depreciation': round(dep),
            'Monthly_Cash_Flow': round(monthly_cash_flow),
            'Monthly_Profit': round(monthly_profit),
            'Cumulative_Cash_Flow': round(cumulative_cash_flow)
        })

    df_month = pd.DataFrame(monthly_data)

    # Yearly summary
    df_year = df_month.groupby(((df_month['Month']-1)//12)*12).sum()
    df_year.index = [f"Year {i+1}" for i in range(len(df_year))]

    df_year['Cash_Profit'] = df_year['Revenue'] - df_year['Total_Operating_Cost']
    df_year['Profit_After_Dep_Loan'] = df_year['Cash_Profit'] - df_year['Depreciation'] - df_year['Loan_EMI']

    df_year['Total_Crossings'] = df_month.groupby(((df_month['Month']-1)//12)*12)['Sows_Crossed'].sum().values

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
        
    return df_month, df_year, total_sow_cost, shed_cost, first_sale_cash_needed, total_pigs_sold, total_pigs_born, animals_left, cumulative_cash_flow, total_interest_paid

import streamlit as st
import pandas as pd

# (keep your sow_rotation_simulator function as-is above...)

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("🐷 House of Supreme Ham Simulator")
st.sidebar.header("Simulation Parameters")

# Sow & Piglet
total_sows = st.sidebar.slider("Total Sows", 10, 500, 30, 5)
piglets_per_cycle = st.sidebar.slider("Piglets per Cycle", 5, 30, 9, 1)
piglet_mortality_pct = st.sidebar.slider("Piglet Mortality (%)", 0, 50, 3, 1)
piglet_mortality = piglet_mortality_pct / 100
abortion_rate_pct = st.sidebar.slider("Abortion Rate (%)", 0, 50, 3, 1)
abortion_rate = abortion_rate_pct / 100

# Feed & Sale
sow_feed_price = st.sidebar.slider("Sow Feed Price (₹/kg)", 0, 50, 32, 1)
sow_feed_intake = st.sidebar.slider("Sow Feed Intake (kg/day)", 0.0, 8.0, 2.8, 0.1)
grower_feed_price = st.sidebar.slider("Grower Feed Price (₹/kg)", 0, 50, 28, 1)
fcr = st.sidebar.slider("Feed Conversion Ratio (FCR)", 2.0, 4.0, 3.2, 0.1)
final_weight = st.sidebar.slider("Final Weight (kg)", 80, 250, 105, 5)
sale_price = st.sidebar.slider("Sale Price (₹/kg)", 100, 600, 180, 10)

# Management
management_fee = st.sidebar.slider("Management Fee (Monthly)", 0, 1_000_000, 50_000, 1000)
management_commission_pct = st.sidebar.slider("Management Commission (%)", 0, 50, 5, 1)
management_commission = management_commission_pct / 100
supervisor_salary = st.sidebar.slider("Supervisor Salary", 0, 500_000, 25_000, 1000)
worker_salary = st.sidebar.slider("Worker Salary", 0, 100_000, 18_000, 500)
n_workers = st.sidebar.slider("Number of Workers", 0, 50, 2, 1)

# Capital Costs
shed_cost = st.sidebar.slider("Shed Cost", 500_000, 50_000_000, 1_000_000, 100_000)
shed_life_years = st.sidebar.slider("Shed Life (Years)", 1, 30, 10, 1)
sow_cost = st.sidebar.slider("Sow Cost (per sow)", 20_000, 500_000, 35_000, 1000)
sow_life_years = st.sidebar.slider("Sow Life (Years)", 1, 12, 4, 1)

# Loan
loan_amount = st.sidebar.slider("Loan Amount", 0, 100_000_000, 0, 100_000)
interest_rate_pct = st.sidebar.slider("Interest Rate (%)", 0, 20, 10, 1)
interest_rate = interest_rate_pct / 100
loan_tenure_years = st.sidebar.slider("Loan Tenure (Years)", 1, 20, 5, 1)
moratorium_months = st.sidebar.slider("Moratorium Period (Months)", 0, 24, 0, 1)

# Other Fixed Costs
medicine_cost = st.sidebar.slider("Medicine Cost (Monthly)", 0, 500_000, 10_000, 1000)
electricity_cost = st.sidebar.slider("Electricity Cost (Monthly)", 0, 500_000, 5_000, 500)
land_lease = st.sidebar.slider("Land Lease (Monthly)", 0, 5_000_000, 10_000, 1000)

# Simulation Duration
months = st.sidebar.slider("Simulation Duration (Months)", 12, 120, 60, 12)

# -------------------------------
# Run Simulator
# -------------------------------
df_month, df_year, total_sow_cost, shed_cost_val, first_sale_wc, total_pigs_sold, total_pigs_born, animals_left, cumulative_cash_flow, total_interest_paid = sow_rotation_simulator(
    total_sows, piglets_per_cycle, piglet_mortality, abortion_rate,
    sow_feed_price, sow_feed_intake, grower_feed_price, fcr,
    final_weight, sale_price, management_fee, management_commission,
    supervisor_salary, worker_salary, n_workers, shed_cost, shed_life_years,
    sow_cost, sow_life_years, loan_amount, interest_rate, loan_tenure_years,
    moratorium_months, medicine_cost, electricity_cost, land_lease, months
)

# (keep your display/financial summary code unchanged below…)

# Define total capital for financial calculations
total_capital = total_sow_cost + shed_cost_val
# -------------------------------
# Breakeven, average monthly profit, and ROI calculations
# -------------------------------
monthly_profit_series = df_month['Monthly_Profit']
cumulative_cash_flow_series = df_month['Cumulative_Cash_Flow']


# Break-even month
breakeven_month = next((m for m, c in zip(df_month['Month'], cumulative_cash_flow_series) if c >= 0), None)

# Average monthly profit after break-even
if breakeven_month:
    remaining_monthly_profit = monthly_profit_series[df_month['Month'] >= breakeven_month]
    avg_profit_after_breakeven = round(remaining_monthly_profit.mean(), 2)
else:
    avg_profit_after_breakeven = 0

# ROI per year
roi_per_year = []
for year in df_year.index:
    revenue = df_year.loc[year, 'Revenue']
    operating_cost = df_year.loc[year, 'Total_Operating_Cost']
    roi = ((revenue - operating_cost) / total_capital) * 100 if total_capital > 0 else 0
    roi_per_year.append(round(roi, 2))

# -------------------------------
# Display Monthly & Yearly Summaries
# -------------------------------
st.subheader("Monthly Summary")
st.dataframe(df_month.drop(columns=['Month']))

st.subheader("Yearly Summary")
st.dataframe(df_year)

# -------------------------------
# Financial Summary at the end
# -------------------------------
st.subheader("Financial Summary")

# Total capital
total_capital = total_sow_cost + shed_cost_val

# # ROI %
# roi_total = (cumulative_cash_flow / total_capital) * 100 if total_capital > 0 else 0


# Total ROI over simulation
total_roi_pct = (cumulative_cash_flow / total_capital) * 100 if total_capital > 0 else 0
# Average monthly profit
average_monthly_profit = df_month['Monthly_Profit'].mean()

# Break-even month (first month cumulative cash flow turns >= 0)
break_even_month = next((int(m) for m, c in zip(df_month['Month'], cum_cash_flow) if c >= 0), None)

if break_even_month is not None:
    # Filter rows after break-even
    remaining_profits = df_month.loc[df_month['Month'] >= break_even_month, 'Monthly_Profit']

    # Average profit after break-even
    avg_profit_after_breakeven = round(remaining_profits.mean(), 2)

    # Total profit earned after break-even
    profit_after_break_even = remaining_profits.sum()
else:
    avg_profit_after_breakeven = 0
    profit_after_break_even = 0



# Display summary

st.subheader("📊 Final Financial Summary")
st.write(f"Total Crossings Done: {df_month['Sows_Crossed'].sum():,.0f}")
st.write(f"Total Pigs Born: {total_pigs_born:.0f}")
st.write(f"Total Pigs Sold: {total_pigs_sold:.0f}")
st.write(f"Animals Remaining in Shed: {animals_left:.0f}")
st.write(f"Total Capital Invested: ₹{total_capital:,.2f}")
st.write(f"Working Capital till First Sale: ₹{first_sale_wc:,.2f}")
st.write(f"Break-even Month: {break_even_month if break_even_month else 'Not achieved'}")
st.write(f"Profit After Break-even (cumulative): ₹{profit_after_break_even:,.0f}")
st.write(f"Average Monthly Profit: ₹{average_monthly_profit:,.0f}")
st.write(f"Average Monthly Profit after Break-even: ₹{avg_profit_after_breakeven:,.2f}")
st.write(f"Total Interest Paid Over Loan Tenure: ₹{total_interest_paid:,.0f}")
st.write(f"Total ROI: {total_roi_pct:.2f}%")
# st.write("ROI per Year:")
# for year_label, roi_val in zip(df_year.index, roi_per_year):
#     st.write(f"{year_label}: {roi_val}%")

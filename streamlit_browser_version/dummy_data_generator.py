# dummy_data_generator.py

# Bora's ShinyJar CRM Suite - Dummy Data Generator
# The following python script generates realistic sample data for the Expense Tracker (shinyjar_data.xlsx with Expenses + Budgets sheets)
# It helps me to show budgets, overspending alerts, trends, visuals instantly.

import pandas as pd
from datetime import datetime, date, timedelta
import random
import os

print("💎 Generating ShinyJar dummy data – jewelry biz style!")

# ShinyJar Jewelry themed categories
expense_categories = [
    "Jewelry Supplies", "Gold/Silver", "Gemstones", "Packaging", "Marketing", 
    "Instagram Ads", "Transport", "Rent", "Utilities", "Entertainment", "Tools"
]

payment_methods = ["Cash", "Card", "Bank Transfer", "PayPal"]

descriptions = [
    "Gold chain purchase", "Instagram boosted post", "Lunch with supplier", "Gemstone beads", 
    "Packaging boxes", "Taxi to meeting", "Electricity bill", "Studio rent", "Coffee run", 
    "New pliers set", "TikTok ad campaign", "Silver wire"
]

tags_options = ["business", "urgent", "marketing", "supplies", "personal", "monthly", ""]

# Generating 80 realistic expenses over last 3 months
def generate_expenses():
    num_expenses = 80
    start_date = date.today() - timedelta(days=90)
    
    data = []
    for _ in range(num_expenses):
        expense_date = start_date + timedelta(days=random.randint(0, 90))
        category = random.choice(expense_categories)
        
        # Higher amounts for jewelry supplies to show big spends
        if category in ["Gold/Silver", "Gemstones", "Instagram Ads"]:
            amount = round(random.uniform(50.0, 800.0), 2)
        else:
            amount = round(random.uniform(5.0, 150.0), 2)
        
        data.append({
            "amount": amount,
            "date": expense_date,
            "category": category,
            "description": random.choice(descriptions),
            "payment_method": random.choice(payment_methods),
            "tags": random.choice(tags_options)
        })
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])  # Ensure datetime for app
    df = df.sort_values('date').reset_index(drop=True)
    return df

# Generating budgets – some tight to trigger overspend alerts for my demo purposes
def generate_budgets():
    budgets = [
        {"category": "Jewelry Supplies", "amount": 1200.0, "period": "monthly", "start_date": "2025-12-01", "end_date": None},
        {"category": "Marketing", "amount": 400.0, "period": "monthly", "start_date": "2025-12-01", "end_date": None},
        {"category": "Instagram Ads", "amount": 300.0, "period": "monthly", "start_date": "2025-12-01", "end_date": None},
        {"category": "Packaging", "amount": 150.0, "period": "monthly", "start_date": "2025-12-01", "end_date": None},
        {"category": "Transport", "amount": 150.0, "period": "monthly", "start_date": "2025-12-01", "end_date": None},
        {"category": "overall", "amount": 2500.0, "period": "monthly", "start_date": "2025-12-01", "end_date": None},
    ]
    df = pd.DataFrame(budgets)
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')
    return df

# Creating the Excel file with two sheets, downloadable at any moment, check the last page on the left pane "Export Reports/Data" in the main APP
def create_shinyjar_data():
    expenses_df = generate_expenses()
    budgets_df = generate_budgets()
    
    file_name = "shinyjar_data.xlsx"
    
    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        expenses_df.to_excel(writer, sheet_name="Expenses", index=False)
        budgets_df.to_excel(writer, sheet_name="Budgets", index=False)
    
    print(f"✨ Success! Created {file_name}")
    print(f"   • {len(expenses_df)} expenses (jewelry supplies, ads, utilities, etc.)")
    print(f"   • {len(budgets_df)} budgets (some tight → overspend alerts ready!)")
    print("\nNow run: streamlit run streamlit_expense_tracker.py")
    print("Open browser → Home page shows totals, alerts fire, charts pop, Budget vs Actual shows red overspend bars!")
    print("\nPerfect for presentation – Bora's jewelry biz in action 💎")

if __name__ == "__main__":
    create_shinyjar_data()
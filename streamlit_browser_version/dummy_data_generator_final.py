# dummy_data_generator_final.py
# Bora's ShinyJar CRM Suite - Dummy Data Generator (updated for my real product list)
# The file generates realistic sample data for ShinyJar jewelry biz: expenses tied to products (e.g., stock buys), budgets with overspend potential.
# The output is "shinyjar_data.xlsx" (local app, two sheets), and two csv files, expenses.csv + budgets.csv for cloud uploads (Streamlit).

import pandas as pd
from datetime import datetime, date, timedelta
import random

print("💎 Generating ShinyJar dummy data – based on real product list!")

# Categories: grouped from products + added ones
categories = [
    "Jars", "Watches", "Bracelets", "Necklaces", "Rings", "Earrings", "Ties", "Chokers",  # Product-based
    "transport", "marketing", "instagram ads", "video and image creation", "influencer ads", "miscellaneous"  # Added
]

# My real products with prices – for expense descriptions/amounts (multiples for stock buys)
products = {
    "Small Jewelry Jar": 20,
    "Big Jewelry Jar": 100,
    "Vintage Watch": 50,
    "Gold Bracelet": 15,
    "Silver Bracelet": 15,
    "Pearl Necklace": 17,
    "Gold Ring": 10,
    "Chokers": 25,
    "Pearl Tie": 30,
    "Children's Watch": 25,
    "Silver Turtle Ring": 12,
    "Gold Hoop Earrings": 13,
    "Pink Butterfly Earrings": 17,
    "Silver Heart Earrings": 12,
    "Shiny Jewelry Jar": 40,
    "Small Earrings": 10
}

# Product-to-category mapping (grouping for reports)
product_to_cat = {
    "Small Jewelry Jar": "Jars",
    "Big Jewelry Jar": "Jars",
    "Shiny Jewelry Jar": "Jars",
    "Vintage Watch": "Watches",
    "Children's Watch": "Watches",
    "Gold Bracelet": "Bracelets",
    "Silver Bracelet": "Bracelets",
    "Pearl Necklace": "Necklaces",
    "Gold Ring": "Rings",
    "Silver Turtle Ring": "Rings",
    "Gold Hoop Earrings": "Earrings",
    "Pink Butterfly Earrings": "Earrings",
    "Silver Heart Earrings": "Earrings",
    "Small Earrings": "Earrings",
    "Chokers": "Chokers",
    "Pearl Tie": "Ties"
}

# Descriptions: tie to products + general
descriptions = [f"Bought {prod} stock" for prod in products.keys()] + [
    "Shipping to customer", "Instagram ad campaign", "Video editing software", "Influencer collab fee", 
    "Taxi to supplier", "Misc office supplies", "Marketing flyers", "Image creation tools"
]

payment_methods = ["Cash", "Card", "Bank Transfer", "PayPal"]

tags_options = ["stock", "sale", "urgent", "business", "personal", "monthly", "inventory", "ad", "collab", "shipping", "misc"]  # Lots for combos

# Generating 150 expenses over last 6 months (diverse for trends/reports/graphs)
def generate_expenses():
    num_expenses = 150
    start_date = date.today() - timedelta(days=180)
    
    data = []
    for _ in range(num_expenses):
        expense_date = start_date + timedelta(days=random.randint(0, 180))
        category = random.choice(categories)
        
        if category in product_to_cat.values():  # Product-based: pick random product in category
            prod_list = [k for k, v in product_to_cat.items() if v == category]
            prod = random.choice(prod_list or ["Small Jewelry Jar"])
            base_price = products[prod]
            quantity = random.randint(1, 10)  # Stock buy multiples
            amount = round(base_price * quantity, 2)
            desc = f"Bought {quantity} x {prod}"
        else:  # Added categories: general amounts
            amount = round(random.uniform(5.0, 500.0), 2)  # Varied for min/max/std
            desc = random.choice(descriptions)
        
        tags = ", ".join(random.sample(tags_options, k=random.randint(1, 3)))  # Combos for filters
        
        data.append({
            "amount": amount,
            "date": expense_date,
            "category": category,
            "description": desc,
            "payment_method": random.choice(payment_methods),
            "tags": tags
        })
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])  # Ready for app
    df = df.sort_values('date').reset_index(drop=True)
    return df

# Generating 12 budgets – tight on marketing/ads for overspend alerts/graphs
def generate_budgets():
    budgets = []
    for cat in categories:
        amount = round(random.uniform(200.0, 1500.0), 2)  # Varied, some low for red bars
        if cat in ["marketing", "instagram ads", "influencer ads"]:  # Tight for demo alerts
            amount /= 2  # Halve for overspend
        budgets.append({
            "category": cat,
            "amount": amount,
            "period": "monthly",
            "start_date": "2025-12-01",
            "end_date": None
        })
    budgets.append({"category": "overall", "amount": 5000.0, "period": "monthly", "start_date": "2025-12-01", "end_date": None})  # Overall tight too
    df = pd.DataFrame(budgets)
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')
    return df

# Creating .xlsx for local use + .csvs for Streamlit cloud uploads
def create_data_files():
    expenses_df = generate_expenses()
    budgets_df = generate_budgets()
    
    # .xlsx for local
    with pd.ExcelWriter("shinyjar_data.xlsx", engine='openpyxl') as writer:
        expenses_df.to_excel(writer, sheet_name="Expenses", index=False)
        budgets_df.to_excel(writer, sheet_name="Budgets", index=False)
    
    # CSVs for cloud
    expenses_df.to_csv("expenses.csv", index=False)
    budgets_df.to_csv("budgets.csv", index=False)
    
    print(f"✨ Success! Created shinyjar_data.xlsx (local), expenses.csv + budgets.csv (cloud uploads)")
    print(f"   • {len(expenses_df)} expenses (tied to products like Small Jewelry Jar, varied tags/amounts/dates for great reports/graphs)")
    print(f"   • {len(budgets_df)} budgets (tight on marketing/ads → overspend alerts/red bars ready!)")
    print("\nFor local: Run streamlit run streamlit_expense_tracker.py")
    print("For cloud: Upload CSVs in app → demo magic 💎")

if __name__ == "__main__":
    create_data_files()
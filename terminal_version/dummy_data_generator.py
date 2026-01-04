# dummy_data_generator.py
import pandas as pd
from datetime import datetime, timedelta
import random
import os

def generate_dummy_expenses(n=50):
    categories = ["Food", "Transport", "Entertainment", "Rent", "Utilities", "Shopping", "Jewelry Supplies", "Marketing"]
    payment_methods = ["Cash", "Card", "Transfer"]
    descriptions = ["Lunch", "Taxi", "Cinema", "Electricity", "Groceries", "Necklace materials", "Instagram ads", "Coffee"]

    dates = [datetime.now().date() - timedelta(days=random.randint(0, 90)) for _ in range(n)]
    dates.sort()

    data = {
        "amount": [round(random.uniform(5.0, 350.0), 2) for _ in range(n)],
        "date": dates,
        "category": [random.choice(categories) for _ in range(n)],
        "description": [random.choice(descriptions) for _ in range(n)],
        "payment_method": [random.choice(payment_methods) for _ in range(n)],
        "tags": [random.choice(["urgent", "monthly", "gift", "business", "personal", ""]) for _ in range(n)]
    }
    df = pd.DataFrame(data)
    df.to_csv("expenses.csv", index=False)
    # df.to_csv("shinyjar_data.xlsx", index=False)                  # another script has been created
    print("Created expenses.csv with", len(df), "rows")
    # print("Created shinujar_data.xlsx with", len(df), "rows")     # see above


def generate_dummy_budgets():
    budgets = [
        {"category": "Food", "amount": 300.0, "period": "monthly", "start_date": "2025-12-01", "end_date": "2025-12-31"},
        {"category": "Transport", "amount": 150.0, "period": "monthly", "start_date": "2025-12-01", "end_date": "2025-12-31"},
        {"category": "Entertainment", "amount": 100.0, "period": "monthly", "start_date": "2025-12-01", "end_date": "2025-12-31"},
        {"category": "Overall", "amount": 1200.0, "period": "monthly", "start_date": "2025-12-01", "end_date": "2025-12-31"},
    ]
    pd.DataFrame(budgets).to_csv("budgets.csv", index=False)
    print("Created budgets.csv")


if __name__ == "__main__":
    generate_dummy_expenses(60)
    generate_dummy_budgets()
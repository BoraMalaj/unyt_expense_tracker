# streamlit_expense_tracker.py

# Bora's ShinyJar CRM Suite - inspired from her UNYT Project: A full-featured expense tracker app in Streamlit.
# Tracks daily expenses for jewelry biz, with budgets, alerts, advanced reports, interactive visuals, and exports.
# Based explicitely in Python, code with comments – easy to understand.
# The script runs as follows: "streamlit run streamlit_expense_tracker.py" 
# Check requirements.txt to match the requested python packages for the script
# Example (partial libs to be installed): pip install streamlit pandas numpy matplotlib seaborn plotly openpyxl

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from datetime import datetime, date
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import os
import sys

# Defining session for cloud use
if 'expenses_df' not in st.session_state:
    st.session_state.expenses_df = pd.DataFrame(columns=['amount', 'date', 'category', 'description', 'payment_method', 'tags'])
    st.session_state.expenses_df['date'] = pd.to_datetime(st.session_state.expenses_df['date'], errors='ignore')

if 'budgets_df' not in st.session_state:
    st.session_state.budgets_df = pd.DataFrame(columns=['category', 'amount', 'period', 'start_date', 'end_date'])

# Setting up Seaborn for beautiful static charts
sns.set_style("darkgrid")
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (10, 6)

# Helper method for charts
def safe_chart(fig, chart_name):
    if fig is None:
        st.info(f"No data yet for {chart_name} – add expenses to see magic!")
        return
    return fig

class Expense:
    """Simple class for an individual expense – holds all details like amount, date, etc."""
    def __init__(self, amount, date, category, description='', payment_method='', tags=''):
        self.amount = amount
        self.date = date  # Expect datetime or date, we'll convert in manager
        self.category = category
        self.description = description
        self.payment_method = payment_method
        self.tags = tags

    def to_dict(self):
        """Convert expense to a dict for easy Pandas use."""
        return {
            'amount': self.amount,
            'date': self.date,
            'category': self.category,
            'description': self.description,
            'payment_method': self.payment_method,
            'tags': self.tags
        }

class ExpenseManager:
    """Heart of the app: Manages expenses + budgets in one Excel file (two sheets for easy comparison).
    Handles add/edit/delete, filters, saves – all with error handling."""
    def __init__(self, data_file='shinyjar_data.xlsx'):
        self.data_file = data_file
        # self.expenses_df = self._load_expenses()
        # self.budgets_df = self._load_budgets()
        self.expenses_df = st.session_state.expenses_df     # using session for cloud app
        self.budgets_df = st.session_state.budgets_df       # using session for cloud app

    def _load_expenses(self):
        """Load expenses from Excel 'Expenses' sheet, convert dates to datetime64 for Pandas magic."""
        try:
            df = pd.read_excel(self.data_file, sheet_name="Expenses")
            df['date'] = pd.to_datetime(df['date'])  # Key fix: to datetime64 for .dt and comparisons
            return df
        except FileNotFoundError:
            st.info("No ShinyJar data file yet – starting fresh!")
            return pd.DataFrame(columns=['amount', 'date', 'category', 'description', 'payment_method', 'tags'])
        except ValueError:  # Sheet missing
            return pd.DataFrame(columns=['amount', 'date', 'category', 'description', 'payment_method', 'tags'])
        except Exception as e:
            st.error(f"Oops, error loading expenses: {e}. Starting fresh.")
            return pd.DataFrame(columns=['amount', 'date', 'category', 'description', 'payment_method', 'tags'])

    def _load_budgets(self):
        """Load budgets from Excel 'Budgets' sheet, convert dates to datetime64."""
        try:
            df = pd.read_excel(self.data_file, sheet_name="Budgets")
            df['start_date'] = pd.to_datetime(df['start_date'])
            df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')
            return df
        except FileNotFoundError:
            return pd.DataFrame(columns=['category', 'amount', 'period', 'start_date', 'end_date'])
        except ValueError:
            return pd.DataFrame(columns=['category', 'amount', 'period', 'start_date', 'end_date'])
        except Exception as e:
            st.error(f"Oops, error loading budgets: {e}. Starting fresh.")
            return pd.DataFrame(columns=['category', 'amount', 'period', 'start_date', 'end_date'])

    def _save_all(self):
        """Save both expenses and budgets to one Excel file – keeps everything together for easy sharing."""
        # try:
        #     with pd.ExcelWriter(self.data_file, engine='openpyxl') as writer:
        #         self.expenses_df.to_excel(writer, sheet_name="Expenses", index=False)
        #         self.budgets_df.to_excel(writer, sheet_name="Budgets", index=False)
        # except Exception as e:
        #     st.error(f"Error saving data: {e}")
        
        # Data updated in session - no local file on cloud
        st.session_state.expenses_df = self.expenses_df
        st.session_state.budgets_df = self.budgets_df
        st.success("Data updated in session!")  # No local file on cloud

    def add_expense(self, expense):
        """Add new expense, save to Excel."""
        new_row = pd.DataFrame([expense.to_dict()])
        new_row['date'] = pd.to_datetime(new_row['date'])  # Ensure datetime
        self.expenses_df = pd.concat([self.expenses_df, new_row], ignore_index=True)
        self._save_all()
        return "Expense added successfully!"

    def edit_expense(self, index, **kwargs):
        """Edit expense at index, update fields, save."""
        if index < 0 or index >= len(self.expenses_df):
            raise IndexError("Invalid index – out of range.")
        for key, value in kwargs.items():
            if key in self.expenses_df.columns:
                if key == 'date':
                    value = pd.to_datetime(value)
                self.expenses_df.at[index, key] = value
        self._save_all()
        return "Expense edited successfully!"

    def delete_expense(self, index):
        """Delete expense at index, save."""
        if index < 0 or index >= len(self.expenses_df):
            raise IndexError("Invalid index – out of range.")
        self.expenses_df = self.expenses_df.drop(index).reset_index(drop=True)
        self._save_all()
        return "Expense deleted successfully!"

    def view_expenses(self, filters=None, sort_by=None):
        """Filter and sort expenses – dynamic as per PDF."""
        df_view = self.expenses_df.copy()
        if filters:
            for key, value in filters.items():
                if key == 'date_range' and value:
                    start, end = value
                    if start and end:
                        df_view = df_view[(df_view['date'] >= pd.to_datetime(start)) & (df_view['date'] <= pd.to_datetime(end))]
                elif key == 'amount_range' and value:
                    min_amt, max_amt = value
                    if min_amt is not None and max_amt is not None:
                        df_view = df_view[(df_view['amount'] >= min_amt) & (df_view['amount'] <= max_amt)]
                elif key == 'category' and value:
                    df_view = df_view[df_view['category'].str.contains(value, case=False, na=False)]
                elif key == 'payment_method' and value:
                    df_view = df_view[df_view['payment_method'] == value]
                elif key == 'tags' and value:
                    df_view = df_view[df_view['tags'].str.contains(value, case=False, na=False)]
        if sort_by:
            df_view = df_view.sort_values(by=sort_by)
        return df_view

    def add_budget(self, category, amount, period='monthly', start_date=None, end_date=None):
        """Add new budget, save to Excel."""
        if not start_date:
            start_date = date.today()
        new_budget = pd.DataFrame([{
            'category': category if category else 'overall',
            'amount': amount,
            'period': period,
            'start_date': pd.to_datetime(start_date),
            'end_date': pd.to_datetime(end_date) if end_date else pd.NaT
        }])
        self.budgets_df = pd.concat([self.budgets_df, new_budget], ignore_index=True)
        self._save_all()
        return "Budget added successfully!"

    def edit_budget(self, index, **kwargs):
        """Edit budget at index, update fields, save."""
        if index < 0 or index >= len(self.budgets_df):
            raise IndexError("Invalid index – out of range.")
        for key, value in kwargs.items():
            if key in self.budgets_df.columns:
                if key in ['start_date', 'end_date']:
                    value = pd.to_datetime(value) if value else pd.NaT
                self.budgets_df.at[index, key] = value
        self._save_all()
        return "Budget edited successfully!"

    def delete_budget(self, index):
        """Delete budget at index, save."""
        if index < 0 or index >= len(self.budgets_df):
            raise IndexError("Invalid index – out of range.")
        self.budgets_df = self.budgets_df.drop(index).reset_index(drop=True)
        self._save_all()
        return "Budget deleted successfully!"

    def get_alerts(self):
        """Check for overspending alerts – as per PDF."""
        alerts = []
        today = pd.to_datetime(date.today())
        for _, budget in self.budgets_df.iterrows():
            cat = budget['category']
            budget_amount = budget['amount']
            start = budget['start_date']
            end = budget['end_date'] if pd.notnull(budget['end_date']) else today
            mask = (self.expenses_df['date'] >= start) & (self.expenses_df['date'] <= end)
            if cat == 'overall':
                spent = self.expenses_df[mask]['amount'].sum()
            else:
                spent = self.expenses_df[mask & (self.expenses_df['category'] == cat)]['amount'].sum()
            if spent > budget_amount:
                alerts.append(f"Alert: Overspent in {cat} (budget: €{budget_amount:.2f}, spent: €{spent:.2f})")
        return alerts

    def get_budget_vs_actual(self):
        """Compute budget vs actual for active budgets – for the comparison chart."""
        if self.budgets_df.empty or self.expenses_df.empty:
            return pd.DataFrame()
        today = pd.to_datetime(date.today())
        active_budgets = self.budgets_df[
            (self.budgets_df['period'] == 'monthly') &  # Focus on monthly for simplicity
            (self.budgets_df['start_date'] <= today) &
            ((self.budgets_df['end_date'] >= today) | self.budgets_df['end_date'].isna())
        ]
        if active_budgets.empty:
            return pd.DataFrame()
        actual_list = []
        for _, budget in active_budgets.iterrows():
            start = budget['start_date']
            end = budget['end_date'] if pd.notnull(budget['end_date']) else today
            mask = (self.expenses_df['date'] >= start) & (self.expenses_df['date'] <= end)
            if budget['category'] == 'overall':
                spent = self.expenses_df[mask]['amount'].sum()
                actual_list.append({'category': 'Overall', 'actual': spent})
            else:
                spent = self.expenses_df[mask & (self.expenses_df['category'] == budget['category'])]['amount'].sum()
                actual_list.append({'category': budget['category'], 'actual': spent})
        actual_df = pd.DataFrame(actual_list)
        comparison = active_budgets[['category', 'amount']].merge(actual_df, on='category', how='left')
        comparison = comparison.rename(columns={'amount': 'budget'})
        comparison['actual'] = comparison['actual'].fillna(0)
        comparison['difference'] = comparison['actual'] - comparison['budget']
        comparison['percentage'] = (comparison['actual'] / comparison['budget'] * 100).round(1).fillna(0)
        comparison.loc[comparison['category'] == 'overall', 'category'] = 'Overall'
        return comparison

class ReportGenerator:
    """Generates all the fancy reports – totals, categories, trends, top N, custom ranges."""
    def __init__(self, manager):
        self.manager = manager

    def generate_summary(self, date_range=None):
        """Basic stats: total, avg, median, min, max, std – NumPy-powered via Pandas."""
        df = self.manager.view_expenses(filters={'date_range': date_range})
        if df.empty:
            return None
        return {
            'Total': df['amount'].sum(),
            'Average': df['amount'].mean(),
            'Median': df['amount'].median(),
            'Min': df['amount'].min(),
            'Max': df['amount'].max(),
            'Std Dev': df['amount'].std()
        }

    def category_summary(self):
        """Category breakdowns: totals, avgs, counts, % – groupby magic."""
        grouped = self.manager.expenses_df.groupby('category')['amount'].agg(['sum', 'mean', 'count'])
        total = self.manager.expenses_df['amount'].sum()
        grouped['percentage'] = (grouped['sum'] / total * 100) if total > 0 else 0
        return grouped

    def trends(self, period='monthly'):
        """Time trends: monthly/quarterly/yearly totals."""
        df = self.manager.expenses_df.copy()
        if period == 'monthly':
            df['period'] = df['date'].dt.to_period('M')
        elif period == 'quarterly':
            df['period'] = df['date'].dt.to_period('Q')
        elif period == 'yearly':
            df['period'] = df['date'].dt.to_period('Y')
        trends = df.groupby('period')['amount'].sum().reset_index()
        trends['period'] = trends['period'].astype(str)
        return trends

    def top_n_expenses(self, n=5):
        """Top N biggest expenses – quick nlargest."""
        return self.manager.expenses_df.nlargest(n, 'amount')

    def custom_range_report(self, start, end):
        """Stats for custom date range."""
        return self.generate_summary(date_range=(start, end))

    def export_to_pdf(self, data, filename='report.pdf'):
        """Export report data to PDF – simple table."""
        buffer = BytesIO()
        with PdfPages(buffer) as pdf:
            fig, ax = plt.subplots()
            ax.axis('tight')
            ax.axis('off')
            if isinstance(data, dict):
                data_df = pd.DataFrame.from_dict(data, orient='index', columns=['Value'])
            else:
                data_df = data
            ax.table(cellText=data_df.values, colLabels=data_df.columns, loc='center')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
        buffer.seek(0)
        return buffer

class Visualizer:
    """All visuals: static Seaborn/Matplotlib + interactive Plotly – for that UNYT wow factor."""
    def __init__(self, manager):
        self.manager = manager

    def static_category_totals(self):
        """Static bar chart for category totals."""
        grouped = self.manager.expenses_df.groupby('category')['amount'].sum().sort_values(ascending=True)
        if grouped.empty:
            return None
        fig, ax = plt.subplots(figsize=(10, max(6, len(grouped) * 0.5)))
        sns.barplot(x=grouped.values, y=grouped.index, palette="viridis", ax=ax)
        ax.set_title('Category Totals')
        ax.set_xlabel('Amount (€)')
        ax.set_ylabel('Category')
        for i, v in enumerate(grouped.values):
            ax.text(v + 0.01 * grouped.max(), i, f'€{v:.2f}', va='center')
        return fig

    def static_category_percentages(self):
        """Static pie chart for percentages."""
        grouped = self.manager.expenses_df.groupby('category')['amount'].sum()
        if grouped.empty:
            return None
        fig, ax = plt.subplots(figsize=(9, 9))
        ax.pie(grouped, labels=grouped.index, autopct='%1.1f%%', colors=sns.color_palette("pastel"))
        ax.set_title('Category Percentages')
        return fig

    def static_trends(self, period='monthly'):
        """Static line chart for trends."""
        trends = ReportGenerator(self.manager).trends(period)
        if trends.empty:
            return None
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(data=trends, x='period', y='amount', marker='o', ax=ax)
        ax.set_title(f'{period.capitalize()} Trends')
        ax.set_xlabel('Period')
        ax.set_ylabel('Amount (€)')
        plt.xticks(rotation=45)
        return fig

    def interactive_category_totals(self):
        """Interactive Plotly bar for totals."""
        grouped = self.manager.expenses_df.groupby('category')['amount'].sum().reset_index()
        if grouped.empty:
            return None
        fig = px.bar(grouped, x='category', y='amount', title='Category Totals')
        return fig

    def interactive_category_percentages(self):
        """Interactive Plotly pie for percentages."""
        grouped = self.manager.expenses_df.groupby('category')['amount'].sum().reset_index()
        if grouped.empty:
            return None
        fig = px.pie(grouped, values='amount', names='category', title='Category Percentages')
        return fig

    def interactive_trends(self, period='monthly'):
        """Interactive Plotly line for trends."""
        trends = ReportGenerator(self.manager).trends(period)
        if trends.empty:
            return None
        fig = px.line(trends, x='period', y='amount', title=f'{period.capitalize()} Trends')
        return fig

# Category Dropdown – dynamic from budgets (fallback expenses)
def get_categories():
    cats = st.session_state.budgets_df['category'].unique().tolist()
    if 'overall' in cats:
        cats.remove('overall')
    if not cats:  # Fallback
        cats = st.session_state.expenses_df['category'].unique().tolist()
    return sorted(set(cats)) or ["Food", "Transport", "Jewelry Supplies"]  # Default

# Helper to download charts as PNG – for exports.
def download_chart(fig, name, is_plotly=False):
    buffer = BytesIO()
    if is_plotly:
        fig.write_image(buffer, format='png')
    else:
        fig.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    st.download_button(f"Download {name} as PNG", buffer, file_name=f"{name}.png", mime="image/png")

# Streamlit App Setup
st.set_page_config(page_title="ShinyJar Expense Tracker", page_icon="💎", layout="wide")

manager = ExpenseManager()
report_gen = ReportGenerator(manager)
visualizer = Visualizer(manager)

# Sidebar Menu – left pane with all required features 
# Extra here is the budget comparison, export of all data and some of the charts

# st.sidebar.title("ShinyJar Menu 💎")

# Sidebar with ShinyJar Logo – pro branding!
st.sidebar.image("logo.png", width=200)  # Resizes nicely, keeps aspect ratio
st.sidebar.markdown("### ShinyJar Expense Tracker 💎")
page = st.sidebar.radio("Select Action", [
    "Home 🏠",
    "Add Expense ➕",
    "Edit/Delete Expense ✏️🗑️",
    "Budget Management 💰",
    "View & Filter Expenses 👀",
    "Summary Report 📊",
    "Category Summary 🍭",
    "View Trends 📈",
    "Top N Expenses 🔥",
    "Custom Range Report 🗓️",
    "Visualizing Static Category Totals 📊",
    "Visualizing Static Category Percentages 🥧",
    "Visualizing Static Trends 📈",
    "Interactive Category Totals (Plotly) 🔍",
    "Interactive Category Percentages (Plotly) 🔍",
    "Interactive Trends (Plotly) 🔍",
    "Budget vs Actual Comparison 📊",
    "Export Reports 📤"
])

# Main Content – right pane
if page == "Home 🏠":
    st.title("Welcome to ShinyJar Expense Tracker 💎")
    st.markdown("Inspired by UNYT Project – track ShinyJar's Jewelry Business Expenses!")
    # added to upload data via csv in cloud version - session based
    with st.expander("📂 Upload Demo Data – Instant ShinyJar Jewelry Biz!"):
        col1, col2 = st.columns(2)
        with col1:
            exp_upload = st.file_uploader("Expenses CSV", type="csv")
            if exp_upload:
                df = pd.read_csv(exp_upload)
                df['date'] = pd.to_datetime(df['date'])
                st.session_state.expenses_df = df
                st.success("Expenses loaded!")
                st.rerun()
        with col2:
            bud_upload = st.file_uploader("Budgets CSV", type="csv")
            if bud_upload:
                df = pd.read_csv(bud_upload)
                df['start_date'] = pd.to_datetime(df['start_date'])
                df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')
                st.session_state.budgets_df = df
                st.success("Budgets loaded!")
                st.rerun()
    alerts = manager.get_alerts()
    if alerts:
        st.warning("\n".join(alerts))
    if not manager.expenses_df.empty:
        summary = report_gen.generate_summary()
        col1, col2 = st.columns(2)
        col1.metric("Total Expenses", f"€{summary['Total']:.2f}")
        col2.metric("Average", f"€{summary['Average']:.2f}")
        st.subheader("Recent Expenses")
        st.dataframe(manager.expenses_df.tail(5))
    else:
        st.info("Add expenses to start!")

elif page == "Add Expense ➕":
    st.header("Add New Expense")
    with st.form("add_form"):
        amount = st.number_input("Amount", min_value=0.01)
        date_input = st.date_input("Date", value=date.today())
        category = st.text_input("Category")
        description = st.text_area("Description")
        payment_method = st.selectbox("Payment Method", ["Cash", "Card", "Transfer", "Other"])
        tags = st.text_input("Tags")
        if st.form_submit_button("Add"):
            expense = Expense(amount, pd.to_datetime(date_input), category, description, payment_method, tags)
            st.success(manager.add_expense(expense))

elif page == "Edit/Delete Expense ✏️🗑️":
    st.header("Edit or Delete Expense")
    if manager.expenses_df.empty:
        st.info("No expenses yet.")
    else:
        st.dataframe(manager.expenses_df)
        index = st.number_input("Index to edit/delete", 0, len(manager.expenses_df)-1)
        with st.form("edit_form"):
            amount = st.number_input("Amount", value=float(manager.expenses_df.at[index, 'amount']))
            date_input = st.date_input("Date", value=manager.expenses_df.at[index, 'date'].date())
            category = st.text_input("Category", value=manager.expenses_df.at[index, 'category'])
            description = st.text_area("Description", value=manager.expenses_df.at[index, 'description'])
            payment_method = st.selectbox("Payment Method", ["Cash", "Card", "Transfer", "Other"], index=["Cash", "Card", "Transfer", "Other"].index(manager.expenses_df.at[index, 'payment_method']))
            tags = st.text_input("Tags", value=manager.expenses_df.at[index, 'tags'])
            if st.form_submit_button("Edit"):
                kwargs = {'amount': amount, 'date': pd.to_datetime(date_input), 'category': category, 'description': description, 'payment_method': payment_method, 'tags': tags}
                st.success(manager.edit_expense(index, **kwargs))
        if st.button("Delete"):
            st.success(manager.delete_expense(index))

elif page == "Budget Management 💰":
    st.header("Set & Edit Budgets")
    with st.form("add_budget"):
        category = st.text_input("Category (blank for overall)")
        amount = st.number_input("Amount", min_value=0.01)
        period = st.selectbox("Period", ["monthly", "quarterly", "yearly"])
        start_date = st.date_input("Start Date", value=date.today())
        end_date = st.date_input("End Date (optional)")
        if st.form_submit_button("Add Budget"):
            manager.add_budget(category, amount, period, start_date, end_date)
            st.success("Budget added!")
    if not manager.budgets_df.empty:
        st.subheader("Edit Budgets")
        edited_df = st.data_editor(manager.budgets_df)
        if st.button("Save Budget Changes"):
            manager.budgets_df = edited_df
            manager._save_all()
            st.success("Budgets updated!")
    alerts = manager.get_alerts()
    if alerts:
        st.warning("\n".join(alerts))

elif page == "View & Filter Expenses 👀":
    st.header("View & Filter Expenses")
    filters = {}
    start_date = st.date_input("Start Date Filter")
    end_date = st.date_input("End Date Filter")
    if start_date and end_date:
        filters['date_range'] = (start_date, end_date)
    category_filter = st.text_input("Category Filter")
    if category_filter:
        filters['category'] = category_filter
    sort_by = st.selectbox("Sort By", ["date", "amount", "category"])
    df_view = manager.view_expenses(filters, sort_by)
    st.dataframe(df_view)

elif page == "Summary Report 📊":
    st.header("Summary Report")
    summary = report_gen.generate_summary()
    if summary:
        st.json(summary)
    else:
        st.info("No data.")

elif page == "Category Summary 🍭":
    st.header("Category Summary")
    summary = report_gen.category_summary()
    if not summary.empty:
        st.dataframe(summary)
    else:
        st.info("No data.")

elif page == "View Trends 📈":
    st.header("View Trends")
    period = st.selectbox("Period", ["monthly", "quarterly", "yearly"])
    trends = report_gen.trends(period)
    if not trends.empty:
        st.dataframe(trends)
    else:
        st.info("No data.")

elif page == "Top N Expenses 🔥":
    st.header("Top N Expenses")
    n = st.number_input("N", value=5)
    top_n = report_gen.top_n_expenses(n)
    if not top_n.empty:
        st.dataframe(top_n)
    else:
        st.info("No data.")

elif page == "Custom Range Report 🗓️":
    st.header("Custom Range Report")
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    if start_date and end_date:
        summary = report_gen.custom_range_report(start_date, end_date)
        if summary:
            st.json(summary)
        else:
            st.info("No data in range.")

elif page == "Visualizing Static Category Totals 📊":
    st.header("Static Category Totals (Seaborn)")
    fig = visualizer.static_category_totals()
    fig = safe_chart(fig, "Category Totals")
    if fig:
        st.pyplot(fig)
        download_chart(fig, "Category Totals Static")
    else:
        st.info("No data to visualize.")

elif page == "Visualizing Static Category Percentages 🥧":
    st.header("Static Category Percentages")
    fig = visualizer.static_category_percentages()
    if fig:
        st.pyplot(fig)
        download_chart(fig, "Category Percentages", is_plotly=False)
    else:
        st.info("No data to visualize.")

elif page == "Visualizing Static Trends 📈":
    st.header("Static Trends")
    period = st.selectbox("Period", ["monthly", "quarterly", "yearly"])
    fig = visualizer.static_trends(period)
    if fig:
        st.pyplot(fig)
        download_chart(fig, "Static Trends", is_plotly=False)               # download trends
    else:
        st.info("No data to visualize.")

elif page == "Interactive Category Totals (Plotly) 🔍":
    st.header("Interactive Category Totals")
    fig = visualizer.interactive_category_totals()
    if fig:
        st.plotly_chart(fig)
    else:
        st.info("No data to visualize.")

elif page == "Interactive Category Percentages (Plotly) 🔍":
    st.header("Interactive Category Percentages")
    fig = visualizer.interactive_category_percentages()
    if fig:
        st.plotly_chart(fig)
    else:
        st.info("No data to visualize.")

elif page == "Interactive Trends (Plotly) 🔍":
    st.header("Interactive Trends")
    period = st.selectbox("Period", ["monthly", "quarterly", "yearly"])
    fig = visualizer.interactive_trends(period)
    if fig:
        st.plotly_chart(fig)
    else:
        st.info("No data to visualize.")

elif page == "Budget vs Actual Comparison 📊":
    st.header("Budget vs Actual Comparison")
    comparison = manager.get_budget_vs_actual()
    if not comparison.empty:
        st.dataframe(comparison)
        fig = px.bar(comparison, x='category', y=['budget', 'actual'], barmode='group')
        st.plotly_chart(fig)
    else:
        st.info("No active budgets.")
        
elif page == "Export Reports 📤":
    st.header("Export ShinyJar Data")
    st.info("Download the complete workbook with both Expenses and Budgets sheets")
    try:
        with open("shinyjar_data.xlsx", "rb") as f:
            st.download_button(
                label="📥 Download Full Workbook (Expenses + Budgets)",
                data=f,
                file_name="ShinyJar_Expense_Tracker.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except:
        st.error("No data file yet. Add some expenses/budgets first!")

# Auto saving data
st.sidebar.caption("Data saved to CSV automatically.")

if __name__ == "__main__":
    # Streamlit runs all automatically
    pass

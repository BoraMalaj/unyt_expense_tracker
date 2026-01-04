import os
import sys
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns  # static enhanced visuals
import plotly.express as px  # interactive plots
from matplotlib.backends.backend_pdf import PdfPages

# Seaborn style for the plots in dark theme
sns.set_style("darkgrid")
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (10, 6)  # Size here to be defined, I've chosen the larger size as default

class Expense:
    """Represents an individual expense record."""
    def __init__(self, amount, date, category, description='', payment_method='', tags=''):
        self.amount = amount
        self.date = date
        self.category = category
        self.description = description
        self.payment_method = payment_method
        self.tags = tags

    def to_dict(self):
        return {
            'amount': self.amount,
            'date': self.date,
            'category': self.category,
            'description': self.description,
            'payment_method': self.payment_method,
            'tags': self.tags
        }

class ExpenseManager:
    """Manages expense records, budgets, persistence, filtering, sorting, and alerts."""
    def __init__(self, expenses_file='expenses.csv', budgets_file='budgets.csv'):
        self.expenses_file = expenses_file
        self.budgets_file = budgets_file
        self.df = self._load_expenses()
        self.budgets = self._load_budgets()

    def _load_expenses(self):
        """Load expenses from CSV into Pandas DataFrame."""
        try:
            df = pd.read_csv(self.expenses_file)
            df['date'] = pd.to_datetime(df['date'])
            return df
        except FileNotFoundError:
            return pd.DataFrame(columns=['amount', 'date', 'category', 'description', 'payment_method', 'tags'])
        except pd.errors.EmptyDataError:
            print("Warning: Empty or malformed CSV file. Starting fresh.")
            return pd.DataFrame(columns=['amount', 'date', 'category', 'description', 'payment_method', 'tags'])
        except Exception as e:
            print(f"Error loading expenses: {e}. Starting fresh.")
            return pd.DataFrame(columns=['amount', 'date', 'category', 'description', 'payment_method', 'tags'])

    def _load_budgets(self):
        """Load budgets from CSV."""
        try:
            df = pd.read_csv(self.budgets_file)
            df['start_date'] = pd.to_datetime(df['start_date'])
            if 'end_date' in df.columns:
                df['end_date'] = pd.to_datetime(df['end_date'])
            return df.to_dict('records')
        except FileNotFoundError:
            return []
        except pd.errors.EmptyDataError:
            print("Warning: Empty or malformed budgets CSV. Starting fresh.")
            return []
        except Exception as e:
            print(f"Error loading budgets: {e}. Starting fresh.")
            return []

    def _save_expenses(self):
        """Save expenses DataFrame to CSV."""
        self.df.to_csv(self.expenses_file, index=False)

    def _save_budgets(self):
        """Save budgets to CSV."""
        pd.DataFrame(self.budgets).to_csv(self.budgets_file, index=False)

    def add_expense(self, expense):
        """Add a new expense."""
        new_row = pd.DataFrame([expense.to_dict()])
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        self._save_expenses()
        self._check_budget_alerts()

    def edit_expense(self, index, **kwargs):
        """Edit an existing expense by index."""
        if index < 0 or index >= len(self.df):
            raise IndexError("Invalid expense index.")
        for key, value in kwargs.items():
            if key in self.df.columns:
                if key == 'date':
                    value = pd.to_datetime(value)
                if key == 'amount':
                    value = float(value)
                self.df.at[index, key] = value
        self._save_expenses()
        self._check_budget_alerts()

    def delete_expense(self, index):
        """Delete an expense by index."""
        if index < 0 or index >= len(self.df):
            raise IndexError("Invalid expense index.")
        self.df = self.df.drop(index).reset_index(drop=True)
        self._save_expenses()
        self._check_budget_alerts()

    def view_expenses(self, filters=None, sort_by=None):
        """View expenses with dynamic filtering and sorting."""
        df_view = self.df.copy()
        if filters:
            for key, value in filters.items():
                if key == 'date_range':
                    start, end = value
                    df_view = df_view[(df_view['date'] >= pd.to_datetime(start)) & (df_view['date'] <= pd.to_datetime(end))]
                elif key == 'amount_range':
                    min_amt, max_amt = value
                    df_view = df_view[(df_view['amount'] >= min_amt) & (df_view['amount'] <= max_amt)]
                elif key == 'category':
                    df_view = df_view[df_view['category'] == value]
                elif key == 'payment_method':
                    df_view = df_view[df_view['payment_method'] == value]
                elif key == 'tags':
                    df_view = df_view[df_view['tags'].str.contains(value, na=False)]
        if sort_by:
            df_view = df_view.sort_values(by=sort_by)
        return df_view

    def set_budget(self, category, amount, period='monthly', start_date=None, end_date=None):
        """Set a budget for a category or overall."""
        if not start_date:
            start_date = datetime.now().date()
        budget = {
            'category': category if category else 'overall',
            'amount': amount,
            'period': period,
            'start_date': start_date,
            'end_date': end_date
        }
        self.budgets.append(budget)
        self._save_budgets()
        self._check_budget_alerts()

    def _check_budget_alerts(self):
        """Check for overspending and print alerts."""
        for budget in self.budgets:
            cat = budget['category']
            period_amount = budget['amount']
            start = pd.to_datetime(budget['start_date'])
            end = pd.to_datetime(budget['end_date']) if budget['end_date'] else datetime.now()

            if cat == 'overall':
                spent = self.df[(self.df['date'] >= start) & (self.df['date'] <= end)]['amount'].sum()
            else:
                spent = self.df[(self.df['date'] >= start) & (self.df['date'] <= end) & (self.df['category'] == cat)]['amount'].sum()

            if spent > period_amount:
                print(f"Alert: Overspent in {cat} ({budget['period']} budget: {period_amount}, spent: {spent})")

class ReportGenerator:
    """Generates advanced summary reports."""
    def __init__(self, manager):
        self.manager = manager

    def generate_summary(self, date_range=None):
        """Generate total, average, median, min, max, std of expenses."""
        df = self.manager.view_expenses(filters={'date_range': date_range} if date_range else None)
        if df.empty:
            return "No expenses found."
        
        stats = {
            'total': df['amount'].sum(),
            'average': df['amount'].mean(),
            'median': df['amount'].median(),
            'min': df['amount'].min(),
            'max': df['amount'].max(),
            'std': df['amount'].std()
        }
        return stats

    def category_summary(self):
        """Category-wise summaries with totals, averages, percentages."""
        grouped = self.manager.df.groupby('category')['amount'].agg(['sum', 'mean', 'count'])
        total = self.manager.df['amount'].sum()
        grouped['percentage'] = (grouped['sum'] / total) * 100
        return grouped

    def trends(self, period='monthly'):
        """Monthly, quarterly, yearly trends."""
        df = self.manager.df.copy()
        if period == 'monthly':
            df['period'] = df['date'].dt.to_period('M')
        elif period == 'quarterly':
            df['period'] = df['date'].dt.to_period('Q')
        elif period == 'yearly':
            df['period'] = df['date'].dt.to_period('Y')
        return df.groupby('period')['amount'].sum()

    def top_n_expenses(self, n=5):
        """Top N expenses."""
        return self.manager.df.nlargest(n, 'amount')

    def custom_range_report(self, start, end):
        """Custom date range report."""
        return self.generate_summary(date_range=(start, end))

    def export_report(self, report_data, format='pdf', filename='report.pdf'):
        """Export summaries as PDF, Excel, or image."""
        if format == 'excel':
            pd.DataFrame(report_data).to_excel(filename)
        elif format == 'pdf' or format == 'image':
            fig, ax = plt.subplots()
            ax.axis('tight')
            ax.axis('off')
            ax.table(cellText=pd.DataFrame(report_data).values, colLabels=pd.DataFrame(report_data).columns, loc='center')
            if format == 'pdf':
                with PdfPages(filename) as pdf:
                    pdf.savefig(fig, bbox_inches='tight')
            else:
                plt.savefig(filename, bbox_inches='tight')
            plt.close()

class Visualizer:
    """Handles visual analytics: static with Matplotlib/Seaborn + interactive with Plotly."""
    def __init__(self, manager):
        self.manager = manager

    # Static methods (unchanged from Seaborn version)
    def chart_category_totals(self):
        if self.manager.df.empty:
            print("No data to visualize.")
            return
        
        grouped = self.manager.df.groupby('category')['amount'].sum().sort_values(ascending=True)
        
        plt.figure(figsize=(10, max(6, len(grouped) * 0.5)))
        ax = sns.barplot(x=grouped.values, y=grouped.index, palette="viridis")
        ax.set_title('Total Expenses by Category', fontsize=16, pad=20)
        ax.set_xlabel('Total Amount (€)', fontsize=12)
        ax.set_ylabel('Category', fontsize=12)
        
        for i, v in enumerate(grouped.values):
            ax.text(v + grouped.max() * 0.01, i, f'€{v:,.2f}', va='center', fontweight='bold')
        
        plt.tight_layout()
        plt.show()

    def chart_category_percentages(self):
        if self.manager.df.empty:
            print("No data to visualize.")
            return
        
        grouped = self.manager.df.groupby('category')['amount'].sum()
        total = grouped.sum()
        
        explode = [0.05 if x == grouped.max() else 0 for x in grouped]
        
        plt.figure(figsize=(9, 9))
        wedges, texts, autotexts = plt.pie(
            grouped, 
            labels=grouped.index, 
            autopct=lambda pct: f'{pct:.1f}%\n(€{pct/100*total:,.2f})',
            startangle=90,
            explode=explode,
            shadow=True,
            colors=sns.color_palette("pastel")
        )
        
        plt.title('Expense Distribution by Category', fontsize=18, pad=30)
        
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontweight('bold')
        
        plt.axis('equal')
        plt.show()

    def chart_trends(self, period='monthly'):
        if self.manager.df.empty:
            print("No data to visualize.")
            return
        
        df = self.manager.df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        if period == 'monthly':
            df['period'] = df['date'].dt.to_period('M')
            title = 'Monthly Expense Trends'
        elif period == 'quarterly':
            df['period'] = df['date'].dt.to_period('Q')
            title = 'Quarterly Expense Trends'
        elif period == 'yearly':
            df['period'] = df['date'].dt.to_period('Y')
            title = 'Yearly Expense Trends'
        else:
            print("Invalid period. Use monthly, quarterly, or yearly.")
            return
        
        trends = df.groupby('period')['amount'].sum().reset_index()
        trends['period'] = trends['period'].astype(str)
        
        plt.figure(figsize=(12, 6))
        ax = sns.lineplot(data=trends, x='period', y='amount', marker='o', linewidth=3, color='#8B5CF6')
        
        ax.set_title(title, fontsize=18, pad=20)
        ax.set_xlabel('Period', fontsize=12)
        ax.set_ylabel('Total Amount (€)', fontsize=12)
        
        plt.xticks(rotation=45, ha='right')
        
        for i, row in trends.iterrows():
            ax.text(i, row['amount'] + trends['amount'].max() * 0.02, 
                    f'€{row["amount"]:,.2f}', ha='center', fontweight='bold')
        
        plt.tight_layout()
        plt.show()

    # Interactive Plotly methods
    def interactive_category_totals(self):
        """Interactive bar chart for category totals using Plotly."""
        if self.manager.df.empty:
            print("No data to visualize.")
            return
        
        grouped = self.manager.df.groupby('category')['amount'].sum().reset_index().sort_values('amount', ascending=False)
        fig = px.bar(
            grouped, 
            x='category', 
            y='amount', 
            title='Interactive Total Expenses by Category',
            labels={'amount': 'Total Amount (€)', 'category': 'Category'},
            color='amount',
            color_continuous_scale='viridis'
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            title_font_size=20,
            hovermode='x unified'
        )
        fig.show()

    def interactive_category_percentages(self):
        """Interactive pie chart for category percentages using Plotly."""
        if self.manager.df.empty:
            print("No data to visualize.")
            return
        
        grouped = self.manager.df.groupby('category')['amount'].sum().reset_index()
        fig = px.pie(
            grouped, 
            values='amount', 
            names='category', 
            title='Interactive Expense Distribution by Category',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hole=0.3  # Donut style for flair
        )
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label+value',
            hoverinfo='label+percent+value'
        )
        fig.update_layout(
            title_font_size=20,
            legend_title_text='Categories'
        )
        fig.show()

    def interactive_trends(self, period='monthly'):
        """Interactive line chart for trends using Plotly."""
        if self.manager.df.empty:
            print("No data to visualize.")
            return
        
        df = self.manager.df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        if period == 'monthly':
            df['period'] = df['date'].dt.to_period('M').astype(str)
            title = 'Interactive Monthly Expense Trends'
        elif period == 'quarterly':
            df['period'] = df['date'].dt.to_period('Q').astype(str)
            title = 'Interactive Quarterly Expense Trends'
        elif period == 'yearly':
            df['period'] = df['date'].dt.to_period('Y').astype(str)
            title = 'Interactive Yearly Expense Trends'
        else:
            print("Invalid period. Use monthly, quarterly, or yearly.")
            return
        
        trends = df.groupby('period')['amount'].sum().reset_index()
        fig = px.line(
            trends, 
            x='period', 
            y='amount', 
            title=title,
            labels={'amount': 'Total Amount (€)', 'period': 'Period'},
            markers=True,
            line_shape='spline'  # Smooth lines
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            title_font_size=20,
            hovermode='x unified'
        )
        fig.update_traces(
            hovertemplate='Period: %{x}<br>Amount: €%{y:,.2f}'
        )
        fig.show()

    def export_chart(self, chart_func, filename='chart.png', interactive=False):
        """Export static as image/PDF or interactive as HTML."""
        if interactive:
            # For Plotly
            chart_func()  
            # fig to be added...
            print("Interactive charts are shown in browser. Exporting as HTML...")
            # fig to be added and then to be saved if requested...
            print(f"Use browser's save or manually export from shown plot.")
        else:
            chart_func()
            plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            print(f"Static chart exported as {filename}")
        
# Handling the validation and the main function

def validate_input(prompt, type_func, validator=None):
    """Validate user inputs."""
    while True:
        try:
            value = type_func(input(prompt))
            if validator and not validator(value):
                raise ValueError()
            return value
        except ValueError:
            print("Invalid input. Try again.")

def main():
    manager = ExpenseManager()
    report_gen = ReportGenerator(manager)
    visualizer = Visualizer(manager)

    while True:
        print("\nExpense Tracker Menu (ShinyJar Edition):")
        print("1. Add Expense")
        print("2. Edit Expense")
        print("3. Delete Expense")
        print("4. Set Budget")
        print("5. View Expenses")
        print("6. Generate Summary Report")
        print("7. Generate Category Summary")
        print("8. View Trends")
        print("9. Top N Expenses")
        print("10. Custom Range Report")
        print("11. Visualize Category Totals (Static)")
        print("12. Visualize Category Percentages (Static)")
        print("13. Visualize Trends (Static)")
        print("14. Export Report")        
        print("15. Interactive Category Totals (Plotly)")
        print("16. Interactive Category Percentages (Plotly)")
        print("17. Interactive Trends (Plotly)")
        print("99. Exit")

        choice = input("Enter choice: ")

        if choice == '1':
            amount = validate_input("Amount: ", float, lambda x: x > 0)
            date_str = validate_input("Date (YYYY-MM-DD): ", str, lambda x: bool(datetime.strptime(x, '%Y-%m-%d')))
            date = datetime.strptime(date_str, '%Y-%m-%d')
            category = input("Category: ")
            description = input("Description: ")
            payment_method = input("Payment Method: ")
            tags = input("Tags: ")
            expense = Expense(amount, date, category, description, payment_method, tags)
            manager.add_expense(expense)
            print("Expense added.")

        elif choice == '2':
            print(manager.df)
            index = validate_input("Index to edit: ", int, lambda x: 0 <= x < len(manager.df))
            fields = ['amount', 'date', 'category', 'description', 'payment_method', 'tags']
            kwargs = {}
            for field in fields:
                val = input(f"New {field} (leave blank to keep): ")
                if val:
                    if field == 'date':
                        val = datetime.strptime(val, '%Y-%m-%d')
                    elif field == 'amount':
                        val = float(val)
                    kwargs[field] = val
            manager.edit_expense(index, **kwargs)
            print("Expense edited.")

        elif choice == '3':
            print(manager.df)
            index = validate_input("Index to delete: ", int, lambda x: 0 <= x < len(manager.df))
            manager.delete_expense(index)
            print("Expense deleted.")

        elif choice == '4':
            category = input("Category (blank for overall): ")
            amount = validate_input("Budget Amount: ", float, lambda x: x > 0)
            period = input("Period (monthly/default): ") or 'monthly'
            start_date = input("Start Date (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
            end_date = input("End Date (YYYY-MM-DD, optional): ")
            end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
            manager.set_budget(category, amount, period, start_date, end_date)
            print("Budget set.")

        elif choice == '5':
            filters = {}
            date_start = input("Filter start date (YYYY-MM-DD, optional): ")
            date_end = input("Filter end date (YYYY-MM-DD, optional): ")
            if date_start and date_end:
                filters['date_range'] = (date_start, date_end)
            category = input("Filter category (optional): ")
            if category:
                filters['category'] = category
            print(manager.view_expenses(filters=filters, sort_by='date'))

        elif choice == '6':
            print(report_gen.generate_summary())

        elif choice == '7':
            print(report_gen.category_summary())

        elif choice == '8':
            period = input("Period (monthly/quarterly/yearly): ")
            print(report_gen.trends(period))

        elif choice == '9':
            n = int(input("N: "))
            print(report_gen.top_n_expenses(n))

        elif choice == '10':
            start = input("Start date (YYYY-MM-DD): ")
            end = input("End date (YYYY-MM-DD): ")
            print(report_gen.custom_range_report(start, end))

        elif choice == '11':
            visualizer.chart_category_totals()

        elif choice == '12':
            visualizer.chart_category_percentages()

        elif choice == '13':
            period = input("Period (monthly/quarterly/yearly): ") or 'monthly'
            visualizer.chart_trends(period)

        elif choice == '14':
            report_data = report_gen.generate_summary()
            format = input("Format (pdf/excel/image): ")
            filename = input("Filename: ")
            report_gen.export_report(report_data, format, filename)
            print(f"Exported to {filename}")        

        elif choice == '15':
            visualizer.interactive_category_totals()

        elif choice == '16':
            visualizer.interactive_category_percentages()

        elif choice == '17':
            period = input("Period (monthly/quarterly/yearly): ") or 'monthly'
            visualizer.interactive_trends(period)

        elif choice == '99':
            sys.exit(0)
        
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
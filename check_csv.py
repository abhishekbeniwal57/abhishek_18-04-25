import pandas as pd

# Load and display first few rows of each CSV file
print("Store Status CSV:")
status_df = pd.read_csv('store_status.csv')
print(status_df.head())
print("\nColumn names:", list(status_df.columns))

print("\nMenu Hours CSV:")
hours_df = pd.read_csv('menu_hours.csv')
print(hours_df.head())
print("\nColumn names:", list(hours_df.columns))

print("\nTimezones CSV:")
timezone_df = pd.read_csv('timezones.csv')
print(timezone_df.head())
print("\nColumn names:", list(timezone_df.columns)) 
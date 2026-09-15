from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parent

with sqlite3.connect(
    (ROOT / 'data' / 'warehouse.db').as_uri() + '?mode=ro',
    uri=True
) as con:
    df = pd.read_sql_query('SELECT * FROM sales', con)

print(df.head())

# P1: province x month, sum(amount), fill_value=0, margins=True
p1 = pd.pivot_table(
    df,
    index='province',
    columns='month',
    values='amount',
    aggfunc='sum',
    fill_value=0,
    margins=True,
    margins_name='Total'
)

print('\nP1 - Province x Month')
print(p1)


# P2: filter September, then category x province
sep = df[df['month'] == '2026-09']

p2 = pd.pivot_table(
    sep,
    index='category',
    columns='province',
    values='amount',
    aggfunc='sum',
    fill_value=0,
    margins=True,
    margins_name='Total'
)

print('\nP2 - September Category x Province')
print(p2)


# P3: assert that the pivot grand total equals df['amount'].sum()
assert p1.loc['Total', 'Total'] == df['amount'].sum()

print('\nP3: PASS - P1 grand total is correct')


# P4: export each result to CSV in your submission folder
p1.to_csv(ROOT / 'pivot_province_month.csv')
p2.to_csv(ROOT / 'pivot_september.csv')

print('\nP4: Exported CSV files successfully')
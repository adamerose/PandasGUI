import pandas as pd
from pdgui import show

if __name__ == '__main__':
    pass
sample_data = {
    'OrderDate': {0: '1/6/2016', 1: '1/23/2016', 2: '2/9/2016', 3: '2/26/2016', 4: '3/15/2016', 5: '4/1/2016',
                  6: '4/18/2016', 7: '5/5/2016', 8: '5/22/2016'},
    'Region': {0: 'East', 1: 'Central', 2: 'Central', 3: 'Central', 4: 'West', 5: 'East', 6: 'Central',
               7: 'Central', 8: 'West'},
    'Rep': {0: 'Jones', 1: 'Kivell', 2: 'Jardine', 3: 'Gill', 4: 'Sorvino', 5: 'Jones', 6: 'Andrews', 7: 'Jardine',
            8: 'Thompson'},
    'Item': {0: 'Pencil', 1: 'Binder', 2: 'Pencil', 3: 'Pen', 4: 'Pencil', 5: 'Binder', 6: 'Pencil', 7: 'Pencil',
             8: 'Pencil'}, 'Units': {0: 95, 1: 50, 2: 36, 3: 27, 4: 56, 5: 60, 6: 75, 7: 90, 8: 32},
    'UnitCost': {0: 1.99, 1: 19.99, 2: 4.99, 3: 19.99, 4: 2.99, 5: 4.99, 6: 1.99, 7: 4.99, 8: 1.99},
    'Total': {0: 189.05, 1: 999.5, 2: 179.64, 3: 539.73, 4: 167.44, 5: 299.4, 6: 149.25, 7: 449.1, 8: 63.68}}

df = pd.DataFrame(sample_data)
df = pd.read_csv('pokemon.csv')
df.name = "df1"

tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
          ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
df = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])
df = df.reset_index()
show(df)

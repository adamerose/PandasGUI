import pandas as pd
from pdgui import show


def pivot(df, keys, categories, data):


    return pivoted_df


def flatten_multiindex(df):
    # Flatten multi-index headers

    flat_index = []
    names = df.columns.names
    for tuple in df.columns.values:
        for i in range(len(tuple)):

    df.columns = flat_index

df = pd.read_csv('pokemon.csv')

keys = ['Generation']
categories = ['Type 1', 'Type 2']
data = {'Attack': ['min', 'max'], 'Defense': ['mean']}
# data = {'Attack': ['mean']}


grouped = df.groupby(keys + categories)
aggregated = grouped.agg(data)
aggregated.columns.names = ['AggColumn','AggFunc']
pivoted_df = aggregated.unstack(categories)


# Flatten multi-index headers
df=pivoted_df.copy()
flat_index = []
names = df.columns.names
for tuple in df.columns.values:
    dic = {names[i]:tuple[i] for i in range(len(tuple))}
    agg_col = dic['AggColumn']
    agg_func = dic['AggFunc']

    categories_strings = []
    for key in dic.keys():
        if key in categories:
            categories_strings.append('{}={}'.format(key,dic[key]))

    categories_string = '_'.join(categories_strings)
    s = f'{agg_func}({agg_col})_{categories_string}'
    s = '{}({})_{}'.format(agg_func, agg_col, categories_string)
    s = '%s(%s)_%s' % (agg_func, agg_col, categories_string)
    print(s)
    flat_index.append(s)
df.columns = flat_index


# for agg_pair in data:
#     column = agg_pair[0]
#     agg = agg_pair[1]
#

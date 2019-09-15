case = 3

# Simple example
if case == 1:
    from pandasgui import show
    import pandas as pd

    example_df = pd.DataFrame(pd.np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
                              columns=['a', 'b', 'c'])
    show(example_df)

# Advanced example
if case == 2:
    from pandasgui import show
    import seaborn as sns

    flights = sns.load_dataset('flights')
    multi = flights.set_index(['year', 'month']).unstack()  # MultiIndex example
    if __name__ == '__main__':  # This is needed when starting a new process. Not necessary in interactive console.
        show(flights, flightsReshaped=multi, nonblocking=True)

# View all example datasets
if case == 3:
    from pandasgui import show
    from pandasgui.datasets import all_datasets

    show(**all_datasets)

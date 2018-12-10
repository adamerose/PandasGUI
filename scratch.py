import inspect
import pandas as pd


class mock_GUI():
    def __init__(self, *args, **kwargs):
        print(type(kwargs))
        self.df_list = args
        self.callers_local_vars = inspect.currentframe().f_back.f_locals.items()
        self.print_dataframes()


    def print_dataframes(self):
        for var in self.df_list:
            # Iterates over all the variable names and values in the caller's frame
            for var_name, var_val in self.callers_local_vars:
                if var_val is var:
                    print('-----------------------------------')
                    print('DataFrame variable name: ', var_name)
                    print(var_val)


if __name__ == '__main__':
    x = pd.DataFrame([1,2,3])
    y = pd.DataFrame([1,2,3])
    z = pd.DataFrame([1,2,3])

    window = mock_GUI(x,y,z)


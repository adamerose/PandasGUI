import pandas as pd
import numpy as np
from tkinter import Tk
from pdgui import show
x = Tk().clipboard_get()


data = []
x=x.replace("%","")
for line in x.split("\n"):
    data_row = []
    for item in line.split("\t"):
        data_row.append(item)
    data.append(data_row)

df = pd.DataFrame(data[1:-1], columns=data[0])
print(df)
# show(df)
for col in df.columns:
    try:
        df[col] = df[col].astype(np.float32)
        print(df)
    except:
        pass
df.plot('Annualized return')
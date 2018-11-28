import dfgui
import pandas as pd


df = pd.DataFrame([["11","12","13"],["21","22","23"],["31","32","33"]], columns=["A","B","C"])

dfgui.show(df)


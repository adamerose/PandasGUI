"""Defines sample datasets for use in testing and demos"""
import numpy as np
import pandas as pd

iris = pd.read_csv(
    "https://raw.githubusercontent.com/adamerose/datasets/master/iris.csv"
)
mpg = pd.read_csv("https://raw.githubusercontent.com/adamerose/datasets/master/mpg.csv")
pokemon = pd.read_csv(
    "https://raw.githubusercontent.com/adamerose/datasets/master/pokemon.csv"
)
tips = pd.read_csv(
    "https://raw.githubusercontent.com/adamerose/datasets/master/tips.csv"
)
titanic = pd.read_csv(
    "https://raw.githubusercontent.com/adamerose/datasets/master/titanic.csv"
)
flights = pd.read_csv(
    "https://raw.githubusercontent.com/adamerose/datasets/master/flights.csv"
)

multi_index = pd.MultiIndex.from_tuples(
    [
        ("A", "one", "x"),
        ("A", "one", "y"),
        ("A", "two", "x"),
        ("A", "two", "y"),
        ("B", "one", "x"),
        ("B", "one", "y"),
        ("B", "two", "x"),
        ("B", "two", "y"),
    ],
    names=["first", "second", "third"],
)
multi_df = pd.DataFrame(np.random.randn(8, 8), index=multi_index, columns=multi_index)

simple = pd.DataFrame({"a": [1, 2, 3], "b": [10, 20, 30], "c": [300, 200, 100]})


__all__ = [
    "all_datasets",
    "iris",
    "mpg",
    "pokemon",
    "tips",
    "titanic",
    "flights",
    "simple",
    "multi_df",
]

all_datasets = {
    "iris": iris,
    "mpg": mpg,
    "pokemon": pokemon,
    "tips": tips,
    "titanic": titanic,
    "flights": flights,
    "simple": simple,
    "multi_df": multi_df,
}

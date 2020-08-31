from pandasgui.utility import DotDict
import plotly.express as px
from pandas import DataFrame
import inspect
from typing import NewType, Union, List, Callable
from dataclasses import dataclass
import pandasgui
import os
from dataclasses_json import dataclass_json
from dacite import from_dict

ColumnName = Union[str, None]


def line(**kwargs):
    key_cols = []
    for arg in [a for a in ['x', 'color', 'facet_row', 'facet_col'] if a in kwargs.keys()]:
        key_cols_subset = kwargs[arg]
        if type(key_cols_subset) == list:
            key_cols += key_cols_subset
        elif type(key_cols_subset) == str:
            key_cols += [key_cols_subset]
        else:
            raise TypeError

    df = kwargs['data_frame'].groupby(key_cols).mean().reset_index()
    kwargs['data_frame'] = df
    return px.line(**kwargs)

def bar(**kwargs):
    key_cols = []
    for arg in [a for a in ['x', 'color', 'facet_row', 'facet_col'] if a in kwargs.keys()]:
        key_cols_subset = kwargs[arg]
        if type(key_cols_subset) == list:
            key_cols += key_cols_subset
        elif type(key_cols_subset) == str:
            key_cols += [key_cols_subset]
        else:
            raise TypeError

    df = kwargs['data_frame'].groupby(key_cols).mean().reset_index()
    kwargs['data_frame'] = df
    return px.bar(**kwargs)


def scatter_matrix(**kwargs):
    fig = px.scatter_matrix(**kwargs)
    fig.update_traces(diagonal_visible=False)
    return fig


def contour(**kwargs):
    fig = px.density_contour(**kwargs)
    fig.update_traces(contours_coloring="fill", contours_showlabels=True)
    return fig


@dataclass_json
@dataclass
class Arg:
    arg_name: str


@dataclass_json
@dataclass
class Schema:
    name: str
    args: List[Arg]
    label: str
    category: str
    function: Callable
    icon_path: str


schema_data_list = [
    {
        "name": "histogram",
        "label": "Histogram",
        "args": [{'arg_name': "x"},
                 {'arg_name': "color"},
                 {'arg_name': "facet_row"},
                 {'arg_name': "facet_col"}]
        ,
        "function": px.histogram,
        "category": "Basic",
        "icon_path": os.path.join(pandasgui.__path__[0], "images/plotly/trace-type-histogram.svg")
    },
    {
        "name": "scatter",
        "label": "Scatter",
        "args": [{'arg_name': "x"},
                 {'arg_name': "y"},
                 {'arg_name': "color"},
                 {'arg_name': "facet_row"},

                 {'arg_name': "facet_col"}]
        ,
        "function": px.scatter,
        "category": "Basic",
        "icon_path": os.path.join(pandasgui.__path__[0], "images/plotly/trace-type-scatter.svg")
    },
    {
        "name": "line",
        "label": "Line",
        "args": [{'arg_name': "x"},
                 {'arg_name': "y"},
                 {'arg_name': "color"},
                 {'arg_name': "facet_row"},
                 {'arg_name': "facet_col"}]
        ,
        "function": line,
        "category": "Basic",
        "icon_path": os.path.join(pandasgui.__path__[0], "images/plotly/trace-type-line.svg")
    },
    {
        "name": "bar",
        "label": "Bar",
        "args": [{'arg_name': "x"},
                 {'arg_name': "y"},
                 {'arg_name': "color"},
                 {'arg_name': "facet_row"},

                 {'arg_name': "facet_col"}]
        ,
        "function": bar,
        "category": "Basic",
        "icon_path": os.path.join(pandasgui.__path__[0], "images/plotly/trace-type-bar.svg")
    },
    {
        "name": "box",
        "label": "Box",
        "args": [{'arg_name': "x"},
                 {'arg_name': "y"},
                 {'arg_name': "color"},
                 {'arg_name': "facet_row"},

                 {'arg_name': "facet_col"}]
        ,
        "function": px.box,
        "category": "Basic",
        "icon_path": os.path.join(pandasgui.__path__[0], "images/plotly/trace-type-box.svg")
    },
    {
        "name": "violin",
        "label": "Violin",
        "args": [{'arg_name': "x"},
                 {'arg_name': "y"},
                 {'arg_name': "color"},
                 {'arg_name': "facet_row"},

                 {'arg_name': "facet_col"}]
        ,
        "function": px.violin,
        "category": "1D Distributions",
        "icon_path": os.path.join(pandasgui.__path__[0], "images/plotly/trace-type-violin.svg")
    },
    {
        "name": "scatter_3d",
        "label": "Scatter 3D",
        "args": [{'arg_name': "x"},
                 {'arg_name': "y"},
                 {'arg_name': "z"},
                 {'arg_name': "color"},
                 ],
        "function": px.scatter_3d,
        "category": "3-Dimensional",
        "icon_path": os.path.join(pandasgui.__path__[0], "images/plotly/trace-type-scatter3d.svg")
    },
    {
        "name": "density_heatmap",
        "label": "Heatmap",
        "args": [{'arg_name': "x"},
                 {'arg_name': "y"},
                 {'arg_name': "z"},
                 {'arg_name': "facet_row"},

                 {'arg_name': "facet_col"}]
        ,
        "function": px.density_heatmap,
        "category": "2D Distributions",
        "icon_path": os.path.join(pandasgui.__path__[0], "images/plotly/trace-type-heatmap.svg")
    },
    {
        "name": "density_contour",
        "label": "Contour",
        "args": [{'arg_name': "x"},
                 {'arg_name': "y"},
                 {'arg_name': "z"},
                 {'arg_name': "facet_row"},

                 {'arg_name': "facet_col"}]
        ,
        "function": contour,
        "category": "2D Distributions",
        "icon_path": os.path.join(pandasgui.__path__[0], "images/plotly/trace-type-contour.svg")
    },
    {
        "name": "pie",
        "label": "Pie",
        "args": [{'arg_name': "names"},
                 {'arg_name': "values"},
                 ],
        "function": px.pie,
        "category": "Proportion",
        "icon_path": os.path.join(pandasgui.__path__[0], "images/plotly/trace-type-pie.svg")
    },

    {
        "name": "scatter_matrix",
        "label": "Scatter Matrix",
        "args": [{'arg_name': "dimensions"},
                 {'arg_name': "color"},
                 ],
        "function": scatter_matrix,
        "category": "Multidimensional",
        "icon_path": os.path.join(pandasgui.__path__[0], "images/plotly/trace-type-splom.svg")
    },
]

schemas = [from_dict(data_class=Schema, data=schema_data) for schema_data in schema_data_list]

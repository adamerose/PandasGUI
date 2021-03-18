import plotly.express as px
from pandas import DataFrame
from typing import Literal
from plotly.graph_objs import Figure
import typing
from typing import List
import pandas as pd


class ColumnName(str):
    pass


class ColumnNameList(List[str]):
    pass


def histogram(data_frame: DataFrame,
              y: ColumnName = None,
              x: ColumnName = None,
              color: ColumnName = None,
              facet_row: ColumnName = None,
              facet_col: ColumnName = None,
              orientation: Literal['h', 'v'] = 'v',
              cumulative: bool = False,
              **kwargs) -> Figure:
    return px.histogram(data_frame=data_frame,
                        x=x,
                        y=y,
                        color=color,
                        facet_row=facet_row,
                        facet_col=facet_col,
                        orientation=orientation,
                        cumulative=cumulative,
                        **kwargs)


# TODO add old advanced args
def scatter(data_frame: DataFrame,
            y: ColumnName = None,
            x: ColumnName = None,
            color: ColumnName = None,
            facet_row: ColumnName = None,
            facet_col: ColumnName = None,
            **kwargs) -> Figure:
    return px.scatter(data_frame=data_frame,
                      x=x,
                      y=y,
                      color=color,
                      facet_row=facet_row,
                      facet_col=facet_col,
                      **kwargs)


# TODO add old advanced args
def line(data_frame: DataFrame,
         y: ColumnName = None,
         x: ColumnName = None,
         color: ColumnName = None,
         facet_row: ColumnName = None,
         facet_col: ColumnName = None,
         **kwargs) -> Figure:
    return px.line(data_frame=data_frame,
                   x=x,
                   y=y,
                   color=color,
                   facet_row=facet_row,
                   facet_col=facet_col,

                   **kwargs)


# TODO add old advanced args
def bar(data_frame: DataFrame,
        y: ColumnName = None,
        x: ColumnName = None,
        color: ColumnName = None,
        facet_row: ColumnName = None,
        facet_col: ColumnName = None,
        **kwargs) -> Figure:
    return px.bar(data_frame=data_frame,
                  x=x,
                  y=y,
                  color=color,
                  facet_row=facet_row,
                  facet_col=facet_col,

                  **kwargs)


def box(data_frame: DataFrame,
        y: ColumnName = None,
        x: ColumnName = None,
        color: ColumnName = None,
        facet_row: ColumnName = None,
        facet_col: ColumnName = None,
        **kwargs) -> Figure:
    return px.box(data_frame=data_frame,
                  x=x,
                  y=y,
                  color=color,
                  facet_row=facet_row,
                  facet_col=facet_col,

                  **kwargs)


def violin(data_frame: DataFrame,
           y: ColumnName = None,
           x: ColumnName = None,
           color: ColumnName = None,
           facet_row: ColumnName = None,
           facet_col: ColumnName = None,
           **kwargs) -> Figure:
    return px.violin(data_frame=data_frame,
                     x=x,
                     y=y,
                     color=color,
                     facet_row=facet_row,
                     facet_col=facet_col,

                     **kwargs)


def scatter_3d(data_frame: DataFrame,
               y: ColumnName = None,
               x: ColumnName = None,
               z: ColumnName = None,
               color: ColumnName = None,
               **kwargs) -> Figure:
    return px.scatter_3d(data_frame=data_frame,
                         x=x,
                         y=y,
                         z=z,
                         color=color,
                         **kwargs)


# Other

def density_heatmap(data_frame: DataFrame,
                    y: ColumnName = None,
                    x: ColumnName = None,
                    z: ColumnName = None,
                    facet_row: ColumnName = None,
                    facet_col: ColumnName = None,
                    **kwargs) -> Figure:
    return px.density_heatmap(data_frame=data_frame,
                              x=x,
                              y=y,
                              z=z,
                              facet_row=facet_row,
                              facet_col=facet_col,

                              **kwargs)


def density_contour(data_frame: DataFrame,
                    y: ColumnName = None,
                    x: ColumnName = None,
                    z: ColumnName = None,
                    facet_row: ColumnName = None,
                    facet_col: ColumnName = None,
                    **kwargs) -> Figure:
    return px.density_contour(data_frame=data_frame,
                              x=x,
                              y=y,
                              z=z,
                              facet_row=facet_row,
                              facet_col=facet_col,

                              **kwargs)


def pie(data_frame: DataFrame,
        names: ColumnName = None,
        values: ColumnName = None,
        color: ColumnName = None,
        **kwargs) -> Figure:
    return px.pie(data_frame=data_frame,
                  names=names,
                  values=values,
                  color=color,
                  **kwargs)


def scatter_matrix(data_frame: DataFrame,
                   # TODO convert dimensions to ColumnNameList
                   dimensions: ColumnName = None,
                   color: ColumnName = None,
                   **kwargs) -> Figure:
    dimensions = [dimensions]
    return px.scatter_matrix(data_frame=data_frame,
                             dimensions=dimensions,
                             color=color,
                             **kwargs)


# ------------
# Not included in Plotly Express

def word_cloud(data_frame: DataFrame,
               # TODO convert words to ColumnNameList
               words: ColumnName = None,
               **kwargs) -> Figure:
    from wordcloud import WordCloud

    if type(words) == str:
        words = [words]
    text = ' '.join(pd.concat([data_frame[x].dropna().astype(str) for x in words]))
    wc = WordCloud(scale=2, collocations=False).generate(text)
    fig = px.imshow(wc)
    return fig


def jointplot(data_frame: DataFrame,
              y: ColumnName = None,
              x: ColumnName = None,
              color: ColumnName = None,
              facet_row: ColumnName = None,
              facet_col: ColumnName = None,
              **kwargs) -> Figure:
    raise NotImplementedError

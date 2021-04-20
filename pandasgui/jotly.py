import datetime
from collections import defaultdict

import plotly.express as px
from pandas import DataFrame
from typing import Literal
from plotly.graph_objs import Figure
import typing
from typing import List
import pandas as pd
from pandasgui.store import SETTINGS_STORE
from pandasgui.utility import flatten_iter


class HiddenArg(type):
    pass


class ColumnName(str):
    pass


class ColumnNameList(List[str]):
    pass


# ============================================================================ #
# Standard plots

def histogram(data_frame: DataFrame,
              x: ColumnName = None,
              color: ColumnName = None,
              facet_row: ColumnName = None,
              facet_col: ColumnName = None,
              marginal: Literal['none', 'rug', 'box', 'violin'] = 'none',
              cumulative: bool = False,
              # Args that won't appear in Grapher UI
              title_format: HiddenArg = None,
              **kwargs) -> Figure:
    fig = px.histogram(data_frame=data_frame,
                       x=x,
                       color=color,
                       facet_row=facet_row,
                       facet_col=facet_col,
                       marginal=marginal if marginal != 'none' else None,
                       cumulative=cumulative,
                       **kwargs)

    # Settings and config
    fig.update_layout(title=generate_title(data_frame, "histogram", locals()))

    return fig


# TODO add old advanced args
def scatter(data_frame: DataFrame,
            y: ColumnName = None,
            x: ColumnName = None,
            color: ColumnName = None,
            facet_row: ColumnName = None,
            facet_col: ColumnName = None,
            symbol: ColumnName = None,
            size: ColumnName = None,
            trendline: Literal['none', 'ols', 'lowess'] = 'none',
            marginal: Literal['none', 'histogram', 'rug', 'box', 'violin'] = 'none',
            # Args that won't appear in Grapher UI
            title_format: HiddenArg = None,
            **kwargs) -> Figure:
    fig = px.scatter(data_frame=data_frame,
                     x=x,
                     y=y,
                     color=color,
                     symbol=symbol,
                     size=size,
                     trendline=trendline if trendline != 'none' else None,
                     marginal_x=marginal if marginal != 'none' else None,
                     marginal_y=marginal if marginal != 'none' else None,
                     facet_row=facet_row,
                     facet_col=facet_col,

                     render_mode=SETTINGS_STORE.render_mode.value,

                     **kwargs)
    fig.update()

    # Settings and config
    fig.update_layout(title=generate_title(data_frame, "scatter", locals()))

    return fig


def line(data_frame: DataFrame,
         y: ColumnName = None,
         x: ColumnName = None,
         color: ColumnName = None,
         facet_row: ColumnName = None,
         facet_col: ColumnName = None,
         # Custom args
         aggregation: Literal['mean', 'median', 'min', 'max', 'sum', 'none'] = 'mean',
         # Args that won't appear in Grapher UI
         title_format: HiddenArg = None,
         **kwargs) -> Figure:
    # Create list of key columns
    key_cols = [val for val in [x, color, facet_row, facet_col] if val is not None]
    if key_cols != []:
        if aggregation != 'none':
            data_frame = data_frame.groupby(key_cols).agg(aggregation).reset_index()
        else:
            # Only need to sort here because aggregation already sorts
            data_frame = data_frame.sort_values(key_cols)

    fig = px.line(data_frame=data_frame,
                  x=x,
                  y=y,
                  color=color,
                  facet_row=facet_row,
                  facet_col=facet_col,

                  render_mode=SETTINGS_STORE.render_mode.value,

                  **kwargs)

    # Don't want gaps in line where there are NaN datapoints
    fig.update_traces(connectgaps=True)

    # Settings and config
    fig.update_layout(title=generate_title(data_frame, "line", locals()))

    return fig


def bar(data_frame: DataFrame,
        y: ColumnName = None,
        x: ColumnName = None,
        color: ColumnName = None,
        facet_row: ColumnName = None,
        facet_col: ColumnName = None,
        # Custom args
        aggregation: Literal['mean', 'median', 'min', 'max', 'sum', 'none'] = 'mean',
        # Args that won't appear in Grapher UI
        title_format: HiddenArg = None,
        **kwargs) -> Figure:
    # Create list of key columns
    key_cols = [val for val in [x, color, facet_row, facet_col] if val is not None]
    if key_cols != []:
        if aggregation != 'none':
            data_frame = data_frame.groupby(key_cols).agg(aggregation).reset_index()
        else:
            # Only need to sort here because aggregation already sorts
            data_frame = data_frame.sort_values(key_cols)

    fig = px.bar(data_frame=data_frame,
                 x=x,
                 y=y,
                 color=color,
                 facet_row=facet_row,
                 facet_col=facet_col,
                 **kwargs)

    # Settings and config
    fig.update_layout(title=generate_title(data_frame, "bar", locals()))

    return fig


def box(data_frame: DataFrame,
        y: ColumnName = None,
        x: ColumnName = None,
        color: ColumnName = None,
        facet_row: ColumnName = None,
        facet_col: ColumnName = None,
        # Args that won't appear in Grapher UI
        title_format: HiddenArg = None,
        **kwargs) -> Figure:
    fig = px.box(data_frame=data_frame,
                 x=x,
                 y=y,
                 color=color,
                 facet_row=facet_row,
                 facet_col=facet_col,

                 **kwargs)

    # Settings and config
    fig.update_layout(title=generate_title(data_frame, "box", locals()))

    return fig


def violin(data_frame: DataFrame,
           y: ColumnName = None,
           x: ColumnName = None,
           color: ColumnName = None,
           facet_row: ColumnName = None,
           facet_col: ColumnName = None,
           # Args that won't appear in Grapher UI
           title_format: HiddenArg = None,
           **kwargs) -> Figure:
    fig = px.violin(data_frame=data_frame,
                    x=x,
                    y=y,
                    color=color,
                    facet_row=facet_row,
                    facet_col=facet_col,

                    **kwargs)

    # Settings and config
    fig.update_layout(title=generate_title(data_frame, "violin", locals()))

    return fig


def density_heatmap(data_frame: DataFrame,
                    y: ColumnName = None,
                    x: ColumnName = None,
                    z: ColumnName = None,
                    facet_row: ColumnName = None,
                    facet_col: ColumnName = None,
                    # Args that won't appear in Grapher UI
                    title_format: HiddenArg = None,
                    **kwargs) -> Figure:
    fig = px.density_heatmap(data_frame=data_frame,
                             x=x,
                             y=y,
                             z=z,
                             facet_row=facet_row,
                             facet_col=facet_col,

                             **kwargs)

    # Settings and config
    fig.update_layout(title=generate_title(data_frame, "density_heatmap", locals()))

    return fig


def density_contour(data_frame: DataFrame,
                    y: ColumnName = None,
                    x: ColumnName = None,
                    z: ColumnName = None,
                    facet_row: ColumnName = None,
                    facet_col: ColumnName = None,
                    # Args that won't appear in Grapher UI
                    title_format: HiddenArg = None,
                    **kwargs) -> Figure:
    fig = px.density_contour(data_frame=data_frame,
                             x=x,
                             y=y,
                             z=z,
                             facet_row=facet_row,
                             facet_col=facet_col,

                             **kwargs)

    fig.update_traces(contours_coloring="fill", contours_showlabels=True)

    # Settings and config
    fig.update_layout(title=generate_title(data_frame, "density_contour", locals()))

    return fig


def pie(data_frame: DataFrame,
        names: ColumnName = None,
        values: ColumnName = None,
        color: ColumnName = None,
        facet_row: ColumnName = None,
        facet_col: ColumnName = None,
        # Args that won't appear in Grapher UI
        title_format: HiddenArg = None,
        **kwargs) -> Figure:
    if facet_row is not None or facet_col is not None:
        raise NotImplementedError

    fig = px.pie(data_frame=data_frame,
                 names=names,
                 values=values,
                 color=color,
                 **kwargs)

    # Settings and config
    fig.update_layout(title=generate_title(data_frame, "pie", locals()))

    return fig


def scatter_matrix(data_frame: DataFrame,
                   dimensions: ColumnNameList = None,
                   color: ColumnName = None,
                   # Args that won't appear in Grapher UI
                   title_format: HiddenArg = None,
                   **kwargs) -> Figure:
    fig = px.scatter_matrix(data_frame=data_frame,
                            dimensions=dimensions,
                            color=color,

                            **kwargs)

    # Settings and config
    fig.update_layout(title=generate_title(data_frame, "scatter_matrix", locals()))

    return fig


# ============================================================================ #
# Special


def scatter_3d(data_frame: DataFrame,
               y: ColumnName = None,
               x: ColumnName = None,
               z: ColumnName = None,
               color: ColumnName = None,
               # Args that won't appear in Grapher UI
               title_format: HiddenArg = None,
               **kwargs) -> Figure:
    fig = px.scatter_3d(data_frame=data_frame,
                        x=x,
                        y=y,
                        z=z,
                        color=color,
                        **kwargs)

    # Settings and config
    fig.update_layout(title=generate_title(data_frame, "scatter_3d", locals()))

    return fig


def word_cloud(data_frame: DataFrame,
               words: ColumnNameList = None,
               # Args that won't appear in Grapher UI
               title_format: HiddenArg = None,
               **kwargs) -> Figure:
    from wordcloud import WordCloud

    # TODO look at this https://github.com/PrashantSaikia/Wordcloud-in-Plotly/blob/master/plotly_wordcloud.py

    if type(words) == str:
        words = [words]
    text = ' '.join(pd.concat([data_frame[x].dropna().astype(str) for x in words]))
    wc = WordCloud(scale=2, collocations=False).generate(text)
    fig = px.imshow(wc)

    # Settings and config
    fig.update_layout(title=generate_title(data_frame, "word_cloud", locals()))

    return fig


# ============================================================================ #
# Utility functions


def generate_title(data_frame, chart_type, kwargs):
    """template variable replacement.

    Besides all dragger selections (x, y, z, color etc), and all custom kwargs, extra template variables are:

          date: current datetime
          filters: active filter expressions, comma delimited
          title_x: x minus units and with log scale if selected
          title_y: y minus units and with log scale if selected
          title_z: z minus units and with log scale if selected
          title_dimensions: dimensions list minus units
          title_columns: columns list minus units
          title_trendline: trendline description
          vs: when doing a title with x vs y, use {x}{vs}{y}
          over_by: when doing a title y over x, use {y}{over_by}{x}. Preferred. for distributions, will use "by"
          name: dataframe name
          total: total number of observations
          subset: observations with active filters applied
          selection: ready to use string representing {subset} observations of {total}
          groupings: groupings tied to Legend and not on legend: marker_symbol, line_group, size etc
    """
    try:
        def remove_units(label):
            "we do not want to repeat units in the title. It is assumed they are in parenthesis"
            if type(label) == list and len(label) == 0:
                return label
            elif type(label) == list and len(label) == 1:
                return remove_units(label[0])
            elif type(label) == list and len(label) > 1:
                return [remove_units(val) for val in label]
            try:
                return label[:label.rindex("(")] if label[-1] == ")" else label
            except (AttributeError, IndexError, TypeError, ValueError):
                return label

        def axis_title_labels(kwargs):
            "handling of x, y, z and dimentsions, columns / orientation and log scales for all charts"
            orientation = kwargs.get("orientation")
            log_x = kwargs.get("log_x", False)
            log_y = kwargs.get("log_y", False)
            log_z = kwargs.get("log_z", False)

            title_log_x = "log " if log_x else ""
            title_log_y = "log " if log_y else ""
            title_log_z = "log " if log_z else ""

            x = remove_units(kwargs.get("x"))
            y = remove_units(kwargs.get("y", ""))
            z = remove_units(kwargs.get("z", ""))
            dimensions = remove_units(kwargs.get("dimensions", ""))
            columns = remove_units(kwargs.get("columns", ""))

            if orientation == "h":
                x, y = y, x
                title_log_x, title_log_y = title_log_y, title_log_x
            if x is None:
                opt_x = x  # wordcloud, pie etc have no x
            elif type(x) == list:
                opt_x = [title_log_x + val for val in x]
            else:
                opt_x = title_log_x + x
            if type(y) == list:
                opt_y = [title_log_y + val for val in y]
            else:
                opt_y = title_log_y + y
            return opt_x, opt_y, title_log_z + z, dimensions, columns

        pgdf = data_frame.pgdf
        today = datetime.datetime.now()
        name = pgdf.name
        x, y, z, dimensions, columns = axis_title_labels(kwargs)

        # Histograms default to count for aggregation
        histfunc = ""
        over_by = " over "
        vs = " vs "
        color = kwargs.get("color")
        symbol = kwargs.get("symbol")
        aggregation = kwargs.get("aggregation", None)
        title_trendline = kwargs.get("trendline", "")
        if title_trendline != "":
            title_trendline = f"trend lines are <i>{title_trendline}</i>"

        if chart_type == "histogram":
            histfunc = kwargs.get("histfunc", "sum" if y else "count")
            if x is None and y:
                y = f"{y} {histfunc}"
        elif chart_type in ("box", "violin"):
            histfunc = "distribution"
            over_by = " by "
            if x is None and y:
                y = f"{y} {histfunc}"
        elif chart_type == "bar":
            over_by = " by "
            if y == "":
                y = "count"
                if color is None and aggregation:
                    over_by = " of "
            else:
                if aggregation:
                    func = "average"
                else:
                    func = "sum"
                y = f"{func} of {y}"
        elif chart_type == "density_heatmap":
            histfunc = kwargs.get("histfunc", "sum")
            if y and z:
                y, z = f"binned {histfunc} of {z} for ", y
            elif y:
                y = f"binned count of {y}"
            histfunc = ""
        elif chart_type == "density_contour":
            histfunc = kwargs.get("histfunc", "count")
            estimation = "estimated density "
            if y and z:
                y, z = f"estimated {histfunc} density of {z} for ", y
            elif y:
                y = f"estimated count density of {y}"
            histfunc = ""
        elif chart_type == "scatter_3d":
            if y and z:
                # need to separate them
                z = ", " + z
        elif chart_type in ("word_cloud", "scatter_matrix", "pie"):
            x = ""  # else string will evaluate to None
        elif chart_type == "line":
            if kwargs.get("aggregation", None):
                over_by = " by "
                if y:
                    y = f"average of {y}"

        # filters
        filters = ','.join([filter.expr for filter in pgdf.filters if filter.enabled and filter.failed == False])
        if filters != "":
            filters = "Filters: " + filters
        total = pgdf.df_unfiltered.shape[0]

        subset = pgdf.df.shape[0]
        selection = ""
        groupings = ""
        sep = ""
        showlegend = kwargs.get("showlegend", True)

        # over / by
        over_by = f" {histfunc}{over_by}" if x else ""
        vs = f"{vs} {histfunc}" if y else ""

        # Groupings in Legend
        if color or symbol:
            if showlegend:
                groupings += "Legend"
            else:
                if color:
                    groupings += f"{sep}color={color}"
                    sep = ", "
                if symbol:
                    groupings += f"{sep}symbol={symbol}"
            sep = ", "

        # this one shows on the legend, but is not labeled
        if kwargs.get("marker_symbol"):
            groupings += f"{sep}marker={kwargs['marker_symbol']}"

        # next two don't show in the plotly legend, so we need to explicitly add them
        if "line_group" in kwargs.keys():
            groupings += f"{sep}line_group={kwargs['line_group']}"
        if "size" in kwargs.keys():
            groupings += f"{sep}size={kwargs['size']}"
        if "text" in kwargs.keys():
            groupings += f"{sep}text={kwargs['text']}"
        if groupings != "":
            groupings = "Grouped by " + groupings
            if filters != "":
                groupings += " - "

        if subset != total:
            selection = f"({subset} obs. of {total}) "
        elif aggregation:
            selection = "({groupby_obs} " + f"derived obs. from {total})"
        else:
            selection = f"({total} obs.)" if chart_type == "line" else "(all observations)"

        return SETTINGS_STORE['title_format'].value. \
            format_map(defaultdict(str,
                                   date=today,
                                   filters=filters,
                                   title_x=x,
                                   title_y=y,
                                   title_z=z,
                                   title_dimensions=dimensions,
                                   title_columns=columns,
                                   title_trendline=title_trendline,
                                   vs=vs,
                                   over_by=over_by,
                                   name=name,
                                   total=total,
                                   subset=subset,
                                   selection=selection,
                                   groupings=groupings,
                                   **kwargs))
    except:
        return None

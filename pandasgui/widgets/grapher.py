import inspect
import sys
from typing import NewType, Union, List, Callable, Iterable
from dataclasses import dataclass
import pandasgui
import os
import plotly.express as px
import plotly

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

import pandas as pd
from pandasgui.store import PandasGuiStore, PandasGuiDataFrameStore, HistoryItem, SETTINGS_STORE

from pandasgui.widgets.figure_viewer import FigureViewer
from pandasgui.utility import flatten_df, flatten_iter, kwargs_string, nunique, unique, eval_title
from pandasgui.widgets.dragger import Dragger, ColumnArg, Schema, BooleanArg

import logging

logger = logging.getLogger(__name__)

import plotly.graph_objs as go
from plotly.validators.scatter.marker import SymbolValidator
# Available symbol names for a given version of Plotly
_extended_symbols = SymbolValidator().values[0::2][1::3]
plotly_markers = [symbol for symbol in _extended_symbols if symbol[-3:] != "dot"]


class Grapher(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrameStore):
        super().__init__()

        self.pgdf = PandasGuiDataFrameStore.cast(pgdf)

        self.setWindowTitle("Graph Builder")

        # Dropdown to select plot type
        self.plot_type_picker = QtWidgets.QListWidget()
        self.plot_type_picker.setViewMode(self.plot_type_picker.IconMode)
        self.plot_type_picker.setWordWrap(False)
        self.plot_type_picker.setSpacing(20)
        self.plot_type_picker.setResizeMode(self.plot_type_picker.Adjust)
        self.plot_type_picker.setDragDropMode(self.plot_type_picker.NoDragDrop)
        self.plot_type_picker.setStyleSheet("QListView::item {border: 2px solid transparent; padding: 3px;}"
                                            "QListView::item:selected {background: none; border: 2px solid #777;}")

        self.plot_type_picker.sizeHint = lambda: QtCore.QSize(500, 250)

        for schema in schemas:
            icon = QtGui.QIcon(schema.icon_path)
            text = schema.label
            item = QtWidgets.QListWidgetItem(icon, text)
            self.plot_type_picker.addItem(item)

        # UI setup
        self.figure_viewer = FigureViewer(store=self.pgdf.store)
        self.figure_viewer.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                         QtWidgets.QSizePolicy.Expanding)

        df = flatten_df(self.pgdf.df)
        self.dragger = Dragger(sources=df.columns,
                               schema=Schema(),
                               source_nunique=nunique(df).apply('{: >7}'.format).values,
                               source_types=df.dtypes.values.astype(str))

        self.plot_splitter = QtWidgets.QSplitter(Qt.Horizontal)
        self.plot_splitter.setHandleWidth(3)
        self.left_panel = QtWidgets.QGridLayout()
        self.left_panel.addWidget(self.plot_type_picker, 0, 0)
        self.left_panel.addWidget(self.dragger, 1, 0)

        self.dragger.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.plot_type_picker.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # QGrid for first half of splitter
        self.selection_grid = QtWidgets.QWidget()
        self.selection_grid.setLayout(self.left_panel)
        self.plot_splitter.addWidget(self.selection_grid)

        # Figure Viewer for the second half of splitter
        self.figure_viewer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.plot_splitter.addWidget(self.figure_viewer)

        self.plot_splitter.setStretchFactor(1, 1)

        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(self.plot_splitter)
        self.setLayout(self.layout)


        # Signals
        self.plot_type_picker.itemSelectionChanged.connect(self.on_type_changed)
        self.dragger.finished.connect(self.on_dragger_finished)
        self.dragger.saving.connect(self.on_dragger_saving)

        # Initial selection
        self.plot_type_picker.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.plot_type_picker.setCurrentRow(0)
        self.on_type_changed()

        # Show a blank axis initially
        self.fig = plotly.graph_objs.Figure()
        self.figure_viewer.set_figure(self.fig)

    def on_type_changed(self):
        if len(self.plot_type_picker.selectedItems()) == 0:
            return

        self.selected_plot_label = self.plot_type_picker.selectedItems()[0].text()
        self.current_schema = next(filter(lambda schema: schema.label == self.selected_plot_label, schemas))
        arg_list = [arg.arg_name for arg in self.current_schema.args]

        self.dragger.set_schema(self.current_schema)

    def on_dragger_saving(self):
        options = QtWidgets.QFileDialog.Options()
        # using native widgets so it matches the PNG download button

        filename, _ = QtWidgets.QFileDialog().getSaveFileName(self, "Save plot to", "", "HTML Files (*.html)",
                                                              options=options)
        if filename:
            if filename[-5:] != ".html":
                filename += ".html"
            self.fig.write_html(filename)
            self.pgdf.add_history_item("Grapher",
                                       f"fig.write_html('{filename})'")

    def on_dragger_finished(self):
        # df = flatten_df(self.pgdf.df)
        kwargs = {}
        for key, val in self.dragger.get_data().items():
            if type(val) == list and len(val) == 0:
                continue
            elif type(val) == list and len(val) == 1:
                kwargs[key] = val[0]
            elif type(val) == list and len(val) > 1:
                kwargs[key] = val
            else:
                kwargs[key] = val

        render_mode = self.pgdf.settings.render_mode.value
        if kwargs.get("render_mode", "") == "":
            if self.current_schema.name in ("line", "line_polar", "scatter", "scatter_polar"):
                kwargs["render_mode"] = render_mode

        # delayed evaluation of string to use kwargs
        title_format = self.pgdf.settings.title_format.value
        if title_format:
            # user might have provided a title
            title = kwargs.get("title", "")
            if "{title}" in title:
                # user is just adding to the default title
                kwargs["title"] = title.replace("{title}", title_format)
                kwargs["title"] = eval_title(self.pgdf, self.current_schema, kwargs)
            elif title == "":
                # nothing provided
                kwargs["title"] = title_format
                kwargs["title"] = eval_title(self.pgdf, self.current_schema, kwargs)

        func = self.current_schema.function

        self.fig = func(self.pgdf, kwargs)

        self.pgdf.history_imports.add("import plotly.express as px")

        self.figure_viewer.set_figure(self.fig)


def clear_layout(layout):
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)


# ========================================================================
# Schema

def histogram(pgdf, kwargs):
    fig = px.histogram(data_frame=pgdf.df, **kwargs)
    pgdf.add_history_item("Grapher",
                          f"fig = px.histogram(data_frame=df, {kwargs_string(kwargs)})")
    return fig


def scatter(pgdf, kwargs):
    fig = px.scatter(data_frame=pgdf.df, **kwargs)
    pgdf.add_history_item("Grapher",
                          f"fig = px.scatter(data_frame=df, {kwargs_string(kwargs)})")
    return fig


def line(pgdf, kwargs):
    # Argument in Schema but not a Plotly argument
    apply_mean = kwargs.pop('apply_mean')
    apply_sort = kwargs.pop('apply_sort')

    key_cols = flatten_iter([kwargs[arg] for arg in
                             ['x', 'color', 'line_dash', 'line_group', 'hover_name', 'facet_row', 'facet_col',
                              'marker_symbol'] if arg in kwargs.keys()])

    df = pgdf.df
    if apply_mean and key_cols != []:
        df = df.groupby(key_cols).mean().reset_index()
        title = kwargs.get("title", "")
        if "{groupby_obs}" in title:
            # this wasn't available when we rendered the title
            kwargs["title"] = title.replace("{groupby_obs}", str(df.shape[0]))
    if apply_sort and key_cols != []:
        df = df.sort_values(key_cols)
    text = kwargs.get("text")
    marker_symbol = "marker_symbol" in kwargs.keys()
    mode = 'lines'
    trace_kwargs = {}
    # optional
    for trace_attribute in ['textfont', 'textfont_size', 'textfont_color', 'textfont_family', 'textposition',
                             'texttemplate', 'showlegend']:
        try:
            trace_kwargs[trace_attribute] = kwargs.pop(trace_attribute)
        except KeyError:
            pass
    if marker_symbol or text:
        if marker_symbol:
            mode += "+markers"
        if text:
            texthover = kwargs.pop('texthover', None)
            # don't add +text if we want to see text in hover instead of on the plot
            if texthover is None:
                mode += "+text"

        if marker_symbol:
            # get from custom kwargs, but invalid for px.line, so pop them
            marker_col = kwargs.pop('marker_symbol')
            marker_size = kwargs.pop('marker_size', 10)  # optional
            marker_line_width = kwargs.pop('marker_line_width', 2)  # optional

            marker_unique = sorted(unique(df[marker_col]))
            unique_markers = len(plotly_markers)

            kwargs['hover_name'] = kwargs.get('hover_name', marker_col)
            fig = None

            for i in range(0, len(marker_unique)):
                df_sub = df[df[marker_col] == marker_unique[i]]

                if fig is None:
                    fig = px.line(data_frame=df_sub, **kwargs).update_traces(
                        mode=mode,
                        marker_symbol=plotly_markers[i % unique_markers],
                        marker_size=marker_size,
                        marker_line_width=marker_line_width,
                        **trace_kwargs)
                else:
                    fig.add_traces(px.line(data_frame=df_sub, **kwargs).update_traces(
                        mode=mode,
                        marker_symbol=plotly_markers[i % unique_markers],
                        marker_size=marker_size,
                        marker_line_width=marker_line_width,
                        **trace_kwargs).data)
        else:
            # observations have text to label them, but no markers
            fig = px.line(data_frame=df, **kwargs).update_traces(mode=mode, **trace_kwargs)
    else:
        fig = px.line(data_frame=df, **kwargs)
        if len(trace_kwargs) > 0:
            fig = fig.update_traces(**trace_kwargs)

    if apply_sort and df[kwargs['x']].dtype.name == 'object':
        fig.update_xaxes(type='category', categoryorder='category ascending')

    pgdf.add_history_item("Grapher",
                          f"# *Code history for line plot not yet fully implemented*\n"
                          f"fig = px.line(data_frame=df, {kwargs_string(kwargs)})")
    return fig


def bar(pgdf, kwargs):
    # Argument in Schema but not a Plotly argument
    apply_mean = kwargs.pop('apply_mean')
    apply_sort = kwargs.pop('apply_sort')

    key_cols = flatten_iter([kwargs[arg] for arg in ['x', 'color', 'facet_row', 'facet_col'] if arg in kwargs.keys()])

    df = pgdf.df
    if apply_mean and key_cols != []:
        df = df.groupby(key_cols).mean().reset_index()
        title = kwargs.get("title", "")
        if "{groupby_obs}" in title:
            # this wasn't available when we rendered the title
            kwargs["title"] = title.replace("{groupby_obs}", str(df.shape[0]))
    if apply_sort and key_cols != []:
        df = df.sort_values(key_cols)
    trace_kwargs = {}
    for trace_attribute in ['textfont', 'textfont_size', 'textfont_color', 'textfont_family', 'textposition',
                             'texttemplate', 'showlegend']:
        try:
            trace_kwargs[trace_attribute] = kwargs.pop(trace_attribute)
        except KeyError:
            pass

    pgdf.add_history_item("Grapher",
                          f"# *Code history for bar plot not yet fully implemented*\n"
                          f"fig = px.bar(data_frame=df, {kwargs_string(kwargs)})")
    fig = px.bar(data_frame=df, **kwargs)
    if len(trace_kwargs) > 0:
        fig = fig.update_traces(**trace_kwargs)

    if apply_sort and df[kwargs['x']].dtype.name == 'object':
        fig.update_xaxes(type='category', categoryorder='category ascending')

    return fig


def box(pgdf, kwargs):
    fig = px.box(data_frame=pgdf.df, **kwargs)
    pgdf.add_history_item("Grapher",
                          f"fig = px.box(data_frame=df, {kwargs_string(kwargs)})")
    return fig


def violin(pgdf, kwargs):
    fig = px.violin(data_frame=pgdf.df, **kwargs)
    pgdf.add_history_item("Grapher",
                          f"fig = px.violin(data_frame=df, {kwargs_string(kwargs)})")
    return fig


def scatter_3d(pgdf, kwargs):
    fig = px.scatter_3d(data_frame=pgdf.df, **kwargs)
    pgdf.add_history_item("Grapher",
                          f"fig = px.scatter_3d(data_frame=df, {kwargs_string(kwargs)})")
    return fig


def density_heatmap(pgdf, kwargs):
    fig = px.density_heatmap(data_frame=pgdf.df, **kwargs)
    pgdf.add_history_item("Grapher",
                          f"fig = px.density_heatmap(data_frame=df, {kwargs_string(kwargs)})")
    return fig


def density_contour(pgdf, kwargs):
    fig = px.density_contour(data_frame=pgdf.df, **kwargs)
    fig.update_traces(contours_coloring="fill", contours_showlabels=True)
    pgdf.add_history_item("Grapher",
                          f"fig = px.density_contour(data_frame=df, {kwargs_string(kwargs)})"
                          "fig.update_traces(contours_coloring='fill', contours_showlabels=True)")
    return fig


def pie(pgdf, kwargs):
    fig = px.pie(data_frame=pgdf.df, **kwargs)
    pgdf.add_history_item("Grapher",
                          f"fig = px.pie(data_frame=df, {kwargs_string(kwargs)})")
    return fig


def scatter_matrix(pgdf, kwargs):
    fig = px.scatter_matrix(data_frame=pgdf.df, **kwargs)
    fig.update_traces(diagonal_visible=False)
    pgdf.add_history_item("Grapher",
                          f"fig = px.scatter_matrix(data_frame=df, {kwargs_string(kwargs)})"
                          "fig.update_traces(diagonal_visible=False)")
    return fig


def word_cloud(pgdf, kwargs):
    columns = kwargs['columns']

    if type(columns) == str:
        columns = [columns]

    from wordcloud import WordCloud
    text = ' '.join(pd.concat([pgdf.df[x].dropna().astype(str) for x in columns]))
    wc = WordCloud(scale=2, collocations=False).generate(text)
    title = kwargs.get("title", "")
    fig = px.imshow(wc, title=title)

    pgdf.history_imports.add("from wordcloud import WordCloud")
    pgdf.add_history_item("Grapher",
                          inspect.cleandoc(f"""
                          columns = {columns}
                          text = ' '.join(pd.concat([pgdf.df[x].dropna().astype(str) for x in columns]))
                          wc = WordCloud(scale=2, collocations=False).generate(text)
                          fig = px.imshow(wc)
                          """))
    return fig


schemas = [Schema(name='histogram',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Histogram',
                  function=histogram,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-histogram.svg')),
           Schema(name='scatter',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='symbol'),
                        ColumnArg(arg_name='size'),
                        ColumnArg(arg_name='text'),
                        ColumnArg(arg_name='hover_name'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Scatter',
                  function=scatter,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-scatter.svg')),
           Schema(name='line',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='line_dash'),
                        ColumnArg(arg_name='line_group'),
                        ColumnArg(arg_name='marker_symbol'),
                        ColumnArg(arg_name='text'),
                        ColumnArg(arg_name='hover_name'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col'),
                        BooleanArg(arg_name='apply_mean', default_value=SETTINGS_STORE.apply_mean.value),
                        BooleanArg(arg_name='apply_sort', default_value=SETTINGS_STORE.apply_sort.value)],
                  label='Line',
                  function=line,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-line.svg')),
           Schema(name='bar',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='text'),
                        ColumnArg(arg_name='hover_name'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col'),
                        BooleanArg(arg_name='apply_mean', default_value=SETTINGS_STORE.apply_mean.value),
                        BooleanArg(arg_name='apply_sort', default_value=SETTINGS_STORE.apply_sort.value)],
                  label='Bar',
                  function=bar,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-bar.svg')),
           Schema(name='box',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Box',
                  function=box,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-box.svg')),
           Schema(name='violin',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Violin',
                  function=violin,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-violin.svg')),
           Schema(name='scatter_3d',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='z'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='symbol'),
                        ColumnArg(arg_name='size'),
                        ColumnArg(arg_name='hover_name')],
                  label='Scatter 3D',
                  function=scatter_3d,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-scatter3d.svg')),
           Schema(name='density_heatmap',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='z'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Heatmap',
                  function=density_heatmap,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-heatmap.svg')),
           Schema(name='density_contour',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='z'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Contour',
                  function=density_contour,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-contour.svg')),
           Schema(name='pie',
                  args=[ColumnArg(arg_name='names'),
                        ColumnArg(arg_name='values'),
                        ColumnArg(arg_name='color'), ],
                  label='Pie',
                  function=pie,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-pie.svg')),
           Schema(name='scatter_matrix',
                  args=[ColumnArg(arg_name='dimensions'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='symbol'),
                        ColumnArg(arg_name='size'), ],
                  label='Splom',
                  function=scatter_matrix,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-splom.svg')),
           Schema(name='word_cloud',
                  args=[ColumnArg(arg_name='columns'),
                        ],
                  label='Word Cloud',
                  function=word_cloud,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/word-cloud.svg'))

           ]

if __name__ == "__main__":
    from pandasgui.utility import fix_ipython, fix_pyqt
    from pandasgui.datasets import iris, pokemon

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    gb2 = Grapher(pokemon)
    gb2.show()

    app.exec_()

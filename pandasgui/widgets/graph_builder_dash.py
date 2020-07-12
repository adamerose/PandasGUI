from pandasgui.utility import fix_ipython, fix_pyqt

import numpy as np
import plotly.graph_objs as go
import dash_core_components as dcc
from threading import Thread
from pandasgui.widgets.plotly_viewer import PlotlyViewer

import dash
import dash_core_components as dcc 
import dash_html_components as html
from dash.dependencies import Input, Output

import plotly.graph_objects as go
from pandasgui.datasets import pokemon
import random

class GraphBuilder(PlotlyViewer):
    def __init__(self, df, unique_name=None):
        if not unique_name:
            unique_name = str(random.randint(0, 10000))
        p = Thread(target=self.run_plotly_dash, args=(df, unique_name, ))
        p.start()  # Start the execution
        url = f"http://127.0.0.1:8050/{unique_name}/"
        super().__init__(url=url)
        self.setWindowTitle("Graph Builder")

    def run_plotly_dash(self, df, unique_name):
        # Supress logging of HTTP requests to console
        import logging
        # log = logging.getLogger('werkzeug')
        # log.setLevel(logging.ERROR)

        external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

        app = dash.Dash(external_stylesheets=external_stylesheets,
                        # https://community.plot.ly/t/how-to-get-a-responsive-layout/18029
                        meta_tags=[
                            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
                        ],
                        # https://community.plot.ly/t/multiple-dashboards/4656/3
                        name=unique_name, url_base_pathname=f'/{unique_name}/'
                        )

        app.layout = html.Div([
            dcc.Dropdown(
                id='dropdown',
                options=[{'label': col, 'value': col} for col in df.columns],
                value=df.columns[0]
            ),
            dcc.Graph(id='graph'),

        ])

        # the "value" property of the Slider is the input of the app and the output of the app is the "figure" property of the Graph.
        @app.callback(
            Output('graph', 'figure'),
            [Input('dropdown', 'value')])
        def update_figure(dropdown_value):
            return {
                'data': [go.Histogram(x=df[dropdown_value])],
                'title': unique_name
            }

        # debug=True will not work unless it's running in the main thread
        app.run_server(debug=False)


if __name__ == "__main__":
    fix_ipython()
    fix_pyqt()
    from PyQt5.QtWidgets import QApplication
    import sys

    # Create a QApplication instance or use the existing one if it exists
    app = QApplication(sys.argv)
    gb = GraphBuilder(pokemon, 'pokemon')

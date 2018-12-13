import inspect
import random
import sys
from threading import Thread
import traceback
from collections import OrderedDict

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import \
    NavigationToolbar2QT as NavigationToolbar
from PyQt5 import QtCore, QtGui, QtWidgets

from dataframe_viewer import DataFrameModel, DataFrameView

# This fixes lack of stack trace on PyQt exceptions
import pyqt_fix

sns.set()


class PandasGUI(QtWidgets.QMainWindow):

    def __init__(self, *args, app, **kwargs):
        """

        Args:
            *args (): Tuple of DataFrame objects
            **kwargs (): Dict of (key, value) pairs of
                         {'DataFrame name': DataFrame object}
        """
        super().__init__()

        # Dictionary holding all the DataFrames in the GUI keyed by name
        self.df_dict = {}

        # Dictionary holding metadata for the DataFrames, including the following:
        '''
        tab_widget: QTabWidget object
        '''
        self.df_metadata = {}
        self.app = app

        # I needed to add a section '.f_back', not sure why
        callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()

        # Adds positional arguments to df_dict.
        for i, df_object in enumerate(args):
            df_name = 'untitled' + str(i + 1)

            for var_name, var_val in callers_local_vars:
                if var_val is df_object:
                    print("TEST")
                    df_name = var_name

            self.df_dict[df_name] = df_object
            self.df_metadata[df_name] = {}

        # Adds keyword arguments to df_dict.
        for i, (df_name, df_object) in enumerate(kwargs.items()):
            self.df_dict[df_name] = df_object
            self.df_metadata[df_name] = {}

        # Create main Widget
        self.main_layout = QtWidgets.QHBoxLayout()

        #########################################################
        # Creating and adding all widgets to main_layout

        # Make the menu bar
        self.make_menu_bar()

        # Make the navigation bar
        self.make_nav()

        # Make the QTabWidget
        self.df_shown = list(self.df_dict.values())[0]

        # Make the QTabWidgets for each DataFrame
        self.tabs_stacked_widget = QtWidgets.QStackedWidget()
        for df_name, df_object in self.df_dict.items():
            tab_widget = self.make_tab_widget(df_object)
            self.df_metadata[df_name]['tab_widget'] = tab_widget
            self.tabs_stacked_widget.addWidget(tab_widget)

        initial_df_name = list(self.df_dict.keys())[0]
        initial_tab_widget = self.df_metadata[initial_df_name]['tab_widget']

        self.tabs_stacked_widget.setCurrentWidget(initial_tab_widget)

        # Adds navigation section to splitter.
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.nav_view)
        self.splitter.addWidget(self.tabs_stacked_widget)

        # Combines navigation section and main section.
        self.main_layout.addWidget(self.splitter)
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(self.main_layout)

        self.setCentralWidget(self.main_widget)
        #########################################################

        # Center window on screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)
        self.setWindowTitle('PandasGUI')

        self.show()

    ####################
    # Menu bar functions

    def make_menu_bar(self):

        ## Create a menu for setting the GUI style with radio-style buttons in a QActionGroup
        menubar = self.menuBar()
        styleMenu = menubar.addMenu('&Set Style')
        styleGroup = QtWidgets.QActionGroup(styleMenu, exclusive=True)

        # Iterate over all GUI Styles that exist for the user's system
        for style in QtWidgets.QStyleFactory.keys():
            styleAction = QtWidgets.QAction(f'&{style}', self, checkable=True)
            styleAction.triggered.connect(lambda state, style=style: self.set_style(style))
            styleGroup.addAction(styleAction)
            styleMenu.addAction(styleAction)

        # Set the default style
        styleAction.trigger()  # REEEEEEE

        ## Creates a chart menu.
        chartMenu = menubar.addMenu('&Plot Charts')
        # chartGroup = QtWidgets.QActionGroup(chartMenu)
        scatterChartAction = QtWidgets.QAction('&Scatter Chart', self)
        scatterChartAction.triggered.connect(self.scatter_plot)
        chartMenu.addAction(scatterChartAction)
        boxplotChartAction = QtWidgets.QAction('&Box Plot', self)
        boxplotChartAction.triggered.connect(self.boxplot)
        chartMenu.addAction(boxplotChartAction)

    def set_style(self, style):
        print("Setting style to", style)
        self.app.setStyle(style)

    ####################
    # Tab widget functions

    def make_tab_widget(self, df):
        """Take a DataFrame and creates tabs for it in self.tab_widget."""

        # Creates the tabs
        dataframe_tab = self.make_tab_dataframe(df)
        statistics_tab = self.make_tab_statistics(df)
        chart_tab = self.make_tab_charts(df)

        tab_widget = QtWidgets.QTabWidget()
        # Adds them to the tab_view
        tab_widget.addTab(dataframe_tab, "Dataframe")
        tab_widget.addTab(statistics_tab, "Statistics")
        tab_widget.addTab(chart_tab, "Charts")

        return tab_widget

    def make_tab_dataframe(self, df):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.df_model = DataFrameModel(df)
        view = DataFrameView()
        view.setModel(self.df_model)
        view.verticalHeader().sectionClicked.connect(self.header_clicked)
        view.horizontalHeader().sectionClicked.connect(self.header_clicked)

        # view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        size_policy = QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow
        view.setSizeAdjustPolicy(size_policy)
        layout.addWidget(view)
        tab.setLayout(layout)
        return tab

    def make_tab_statistics(self, df):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        tab_df = df.describe(include='all').T
        tab_df.insert(loc=0,column='Type',value=df.dtypes)
        model = DataFrameModel(tab_df)
        view = DataFrameView()
        view.setModel(model)

        size_policy = QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow
        view.setSizeAdjustPolicy(size_policy)
        layout.addWidget(view)

        tab.setLayout(layout)

        return tab

    def make_tab_charts(self, df):
        # '''Icons from https://www.freepik.com/'''

        # scatterplot_btn = QtWidgets.QPushButton()
        # scatterplot_btn.setIcon(QtGui.QIcon('Images/scatter_icon_64x64.png'))
        # scatterplot_btn.setIconSize(QtCore.QSize(64, 64))
        # scatterplot_btn.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
        #                               QtWidgets.QSizePolicy.Expanding)
        # scatterplot_btn.clicked.connect(self.get_chart_parameters)
        # boxplot_btn = QtWidgets.QPushButton()
        # boxplot_btn.setIcon(QtGui.QIcon('Images/box_plot_icon_64x64.png'))
        # boxplot_btn.setIconSize(QtCore.QSize(64, 64))
        # boxplot_btn.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
        #                           QtWidgets.QSizePolicy.Expanding)

        # button_layout = QtWidgets.QHBoxLayout()
        # button_layout.addWidget(scatterplot_btn)
        # button_layout.addWidget(boxplot_btn)
        # buttons = QtWidgets.QWidget()
        # buttons.setLayout(button_layout)

        # charts = QtWidgets.QWidget()
        # self.chart_layout = QtWidgets.QVBoxLayout()
        # charts.setLayout(self.chart_layout)

        # self.charts_stack = QtWidgets.QStackedWidget(self)

        # self.charts_stack = QtWidgets.QStackedWidget(self.tab_widget)
        # self.charts_stack.addWidget(buttons)
        # self.charts_stack.addWidget(charts)
        # tab = self.charts_stack

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        button = QtWidgets.QPushButton("Print DF")
        # button.clicked.connect(self.printdf)

        layout.addWidget(button)
        tab.setLayout(layout)
        return tab

    def make_tab_reshape(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        button = QtWidgets.QPushButton("Print DF")
        # button.clicked.connect(self.printdf)

        layout.addWidget(button)
        tab.setLayout(layout)
        return tab

    ####################
    # Nav bar functions

    def make_nav(self):
        # Creates the navigation pane.
        df_names = list(self.df_dict.keys())
        self.nav_view = QtWidgets.QTreeView()

        # Creates the headers.
        model = QtGui.QStandardItemModel(0, 2, self)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Shape')

        # Adds the user-inputted dataframes as navbar elements.
        self.main_nav_branch = QtGui.QStandardItem('Master Folder')
        self.second_nav_branch = QtGui.QStandardItem('Other Folder')
        rootnode = model.invisibleRootItem()
        rootnode.setFlags(rootnode.flags() &
                          ~QtCore.Qt.ItemIsDropEnabled)
        rootnode.appendRow([self.main_nav_branch, None])
        rootnode.appendRow([self.second_nav_branch, None])
        for df_name in df_names:
            self.add_nav_dataframe(df_name, self.main_nav_branch)

        # Sets navigation pane properties.
        self.nav_view.setDragDropMode(self.nav_view.InternalMove)
        self.nav_view.setModel(model)
        self.nav_view.expandAll()
        self.nav_view.clicked.connect(self.select_dataframe)

    def select_dataframe(self, location_clicked):
        """
        Examines navbar row pressed by user
        and then changes the dataframe shown.

        Args:
            location_clicked: Automatically passed during clicked signal.
                              Instance of QtCore.ModelIndex.
                              Provides information on the location clicked,
                              accessible with methods such as row() or data().
        """

        df_parent_folder_index = location_clicked.parent().row()
        df_clicked_row_index = location_clicked.row()

        # Gets name of dataframe by using index of the row clicked.
        nav_pane = self.nav_view.model()
        df_parent_folder_name = nav_pane.index(df_parent_folder_index, 0)
        df_name = df_parent_folder_name.child(df_clicked_row_index, 0).data()
        df = self.df_dict.get(df_name)

        if df is not None:
            self.df_shown = df
            tab_widget = self.df_metadata[df_name]['tab_widget']
            self.tabs_stacked_widget.setCurrentWidget(tab_widget)

    def add_nav_dataframe(self, df_name, folder):
        """Adds a dataframe to the navigation sidebar"""

        # Calculate and format the shape of the DataFrame
        shape = self.df_dict[df_name].shape
        shape = str(shape[0]) + ' X ' + str(shape[1])

        df_name_label = QtGui.QStandardItem(df_name)
        shape_label = QtGui.QStandardItem(shape)

        # Disables dropping dataframes on other dataframes in nav pane.
        df_name_label.setFlags(df_name_label.flags() &
                               ~QtCore.Qt.ItemIsDropEnabled)
        shape_label.setFlags(shape_label.flags() &
                             ~QtCore.Qt.ItemIsDropEnabled)
        df_name_label.setEditable(False)
        shape_label.setEditable(False)

        folder.appendRow([df_name_label, shape_label])

    ####################
    # Charts functions.

    def header_clicked(self, data):
        ctrl_pressed = (QtGui.QGuiApplication.keyboardModifiers() ==
                        QtCore.Qt.ControlModifier)
        if ctrl_pressed:
            self.headers_highlighted.append(data)
        else:
            self.headers_highlighted = [data]

    def scatter_plot(self):
        parameters = {'x_values': self.df_shown.columns,
                      'y_values': self.df_shown.columns}
        prompt = ChartInputColumnsDialog(window_title='Create Scatter Plot',
                                         parameters=parameters)
        if prompt.exec_() == prompt.Accepted:
            x, y = prompt.get_parameters()

        # # a figure instance to plot on
        self.chart_figure = plt.figure()
        x_values = self.df_shown[x]
        y_values = self.df_shown[y]

        ax = self.chart_figure.add_subplot(111)
        ax.scatter(x_values, y_values)
        # ax.plot(x_values, 'o-')
        plt.show()

    def boxplot(self):
        parameters = {'column': self.df_shown.columns,
                      'by': self.df_shown.columns}
        prompt = ChartInputColumnsDialog(window_title='Create Box Plot',
                                         parameters=parameters)
        if prompt.exec_() == prompt.Accepted:
            column, by = prompt.get_user_choice()

        sns.boxplot(x=by, y=column, data=self.df_shown)
        plt.show()


class ChartInputColumnsDialog(QtWidgets.QDialog):

    def __init__(self, window_title, parameters):
        super().__init__()
        self.parameters = parameters
        self.createFormGroupBox(self.parameters)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                               QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle(window_title)

    def createFormGroupBox(self, chart_parameters):
        self.formGroupBox = QtWidgets.QGroupBox("Form layout")
        layout = QtWidgets.QFormLayout()

        self.chart_parameter_widgets = {}
        for label, options in chart_parameters.items():
            self.chart_parameter_widgets[label] = QtWidgets.QComboBox()
            self.chart_parameter_widgets[label].addItems(options)
            layout.addRow(QtWidgets.QLabel(label), self.chart_parameter_widgets[label])

        self.formGroupBox.setLayout(layout)

    def get_user_choice(self):
        return_values = [parameter.currentText()
                         for parameter in self.chart_parameter_widgets.values()]
        return return_values


def start_gui(*args, **kwargs):
    app = QtWidgets.QApplication(sys.argv)

    win = PandasGUI(*args, **kwargs, app=app)
    app.exec_()


def show(*args, **kwargs):
    thread = Thread(target=start_gui, args=args, kwargs=kwargs)
    thread.start()

if __name__ == '__main__':
    tips = sns.load_dataset('tips')
    tips = pd.DataFrame(tips)
    pokemon = pd.read_csv('pokemon.csv')

    sample = pd.read_csv('sample.csv')

    tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
              ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
    index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
    multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])

    show(sample, tips, multidf=multidf, pokemon=pokemon)

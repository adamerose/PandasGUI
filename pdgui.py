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
        self.df_dicts is a dictionary of all dataframes in the GUI.
        {dataframe name: objects}

        The objects are their own dictionary of:
        {object name: object}

        possible objects
        dataframe: DataFrame object
        view: DataFrameViewer object
        model: DataFrameModel object
        tab_widget: QTabWidget object

        Args:
            *args (): Tuple of DataFrame objects
            **kwargs (): Dict of (key, value) pairs of
                         {'DataFrame name': DataFrame object}
        """
        super().__init__()
        self.app = app
        self.df_dicts = {}
        self.headers_highlighted = []

        # I needed to add a second '.f_back', not sure why
        callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()

        # Adds positional arguments to df_dicts.
        for i, df_object in enumerate(args):
            df_name = 'untitled' + str(i + 1)

            for var_name, var_val in callers_local_vars:
                if var_val is df_object:
                    df_name = var_name

            self.df_dicts[df_name] = {}
            self.df_dicts[df_name]['dataframe'] = df_object

        # Adds keyword arguments to df_dict.
        for i, (df_name, df_object) in enumerate(kwargs.items()):
            self.df_dicts[df_name] = {}
            self.df_dicts[df_name]['dataframe'] = df_object

        # Generates the user interface.
        self.setupUi()

        # Center window on screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)
        self.setWindowTitle('PandasGUI')
        self.app.setWindowIcon(QtGui.QIcon('icon.png'))

        # Create main Widget
        self.show()

    def setupUi(self):
        """
        Creates and adds all widgets to main_layout.
        """

        self.main_layout = QtWidgets.QHBoxLayout()

        # Make the menu bar
        self.make_menu_bar()

        # Make the navigation bar
        self.make_nav()

        # Make the QTabWidget
        inital_df = list(self.df_dicts.keys())[0]
        self.df_shown = self.df_dicts[inital_df]['dataframe']

        # Make the QTabWidgets for each DataFrame
        self.tabs_stacked_widget = QtWidgets.QStackedWidget()

        # Iterate over all dataframe names and make the tab_widgets
        for df_name in self.df_dicts.keys():
            tab_widget = self.make_tab_widget(df_name)
            self.df_dicts[df_name]['tab_widget'] = tab_widget
            self.tabs_stacked_widget.addWidget(tab_widget)

        initial_df_name = list(self.df_dicts.keys())[0]
        initial_tab_widget = self.df_dicts[initial_df_name]['tab_widget']

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

    ####################
    # Menu bar functions

    def make_menu_bar(self):

        # Create a menu for setting the GUI style with radio-style buttons in a QActionGroup
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
        distplotChartAction = QtWidgets.QAction('&Distribution Plot', self)
        distplotChartAction.triggered.connect(self.distplot)
        chartMenu.addAction(distplotChartAction)

    def set_style(self, style):
        print("Setting style to", style)
        self.app.setStyle(style)

    ####################
    # Tab widget functions

    def make_tab_widget(self, df_name):
        """Take a DataFrame and creates tabs for it in self.tab_widget."""

        # Creates the tabs
        dataframe_tab = self.make_tab_dataframe(df_name)
        statistics_tab = self.make_tab_statistics(df_name)
        chart_tab = self.make_tab_charts()

        tab_widget = QtWidgets.QTabWidget()
        # Adds them to the tab_view
        tab_widget.addTab(dataframe_tab, "Dataframe")
        tab_widget.addTab(statistics_tab, "Statistics")
        tab_widget.addTab(chart_tab, "Charts")

        return tab_widget

    def make_tab_dataframe(self, df_name):

        df = self.df_dicts[df_name]['dataframe']

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.df_model = DataFrameModel(df)
        view = DataFrameView()
        view.setModel(self.df_model)
        view.horizontalHeader().sectionClicked.connect(self.header_clicked)

        # view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        size_policy = QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow
        view.setSizeAdjustPolicy(size_policy)
        layout.addWidget(view)
        tab.setLayout(layout)
        return tab

    def make_tab_statistics(self, df_name):

        df = self.df_dicts[df_name]['dataframe']

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        tab_df = df.describe(include='all').T
        tab_df.insert(loc=0, column='Type', value=df.dtypes)
        model = DataFrameModel(tab_df)
        view = DataFrameView()
        view.setModel(model)

        size_policy = QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow
        view.setSizeAdjustPolicy(size_policy)
        layout.addWidget(view)

        tab.setLayout(layout)

        return tab

    def make_tab_charts(self):
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
        # Create the navigation pane
        df_names = list(self.df_dicts.keys())
        self.nav_view = QtWidgets.QTreeView()

        # Creates the headers.
        model = QtGui.QStandardItemModel(0, 2, self)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Shape')
        root_node = model.invisibleRootItem()

        self.main_nav_branch = QtGui.QStandardItem('Master')
        for df_name in df_names:
            self.add_nav_dataframe(df_name, self.main_nav_branch)

        root_node.appendRow([self.main_nav_branch, None])
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
        df = self.df_dicts.get(df_name)

        if df is not None:
            self.df_shown = self.df_dicts[df_name]['dataframe']
            tab_widget = self.df_dicts[df_name]['tab_widget']
            self.tabs_stacked_widget.setCurrentWidget(tab_widget)

    def add_nav_dataframe(self, df_name, folder):
        """Adds a dataframe to the navigation sidebar"""

        # Calculate and format the shape of the DataFrame
        shape = self.df_dicts[df_name]['dataframe'].shape
        shape = str(shape[0]) + ' X ' + str(shape[1])

        df_name_label = QtGui.QStandardItem(df_name)
        shape_label = QtGui.QStandardItem(shape)

        # Disables dropping dataframes on other dataframes in nav pane.
        df_name_label.setFlags(df_name_label.flags() &
                               ~QtCore.Qt.ItemIsDropEnabled)
        shape_label.setFlags(shape_label.flags() &
                             ~QtCore.Qt.ItemIsDropEnabled)

        # Disables editing the names of the dataframes.
        df_name_label.setEditable(False)
        shape_label.setEditable(False)

        folder.appendRow([df_name_label, shape_label])

    ####################
    # Charts functions.

    def header_clicked(self, header_index):
        """
        Detects if headers are highlighted. If they are,
        sets the default text on the create_plot dialogs to
        the highlighted headers.
        Requires holding control to highlight multiple headers.

        Args:
            header_index: Automatically passed during clicked signal.
                          Provides the index of the header clicked.
                          Type int.
        """

        ctrl_pressed = (QtGui.QGuiApplication.keyboardModifiers() ==
                        QtCore.Qt.ControlModifier)
        if ctrl_pressed:
            self.headers_highlighted.append(header_index)
        else:
            self.headers_highlighted = [header_index]

        print(self.headers_highlighted)

    def scatter_plot(self):
        """
        Shows a popup dialog asking for the inputs to the chart.
        Then creates a scatter plot if 'OK' is pressed, otherwise
        does nothing.
        """
        # Dictionary of {parameter name: possible options}
        parameters = {'x_values': self.df_shown.columns,
                      'y_values': self.df_shown.columns}

        # Makes an instance of a popup dialog to collect information.
        prompt = ChartInputDialog(window_title='Create Scatter Plot',
                                 parameters=parameters,
                                 headers_highlighted=self.headers_highlighted)

        # If the accept button is pressed, get the choices and plot.
        # Otherwise Ignore.
        if prompt.exec_() == prompt.Accepted:
            x, y = prompt.get_user_choice()

            # # a figure instance to plot on
            self.chart_figure = plt.figure()
            x_values = self.df_shown[x]
            y_values = self.df_shown[y]

            try:
                ax = self.chart_figure.add_subplot(111)
                ax.scatter(x_values, y_values)
            except:
                print(traceback.print_exc())
            else:
                plt.show()

    def boxplot(self):
        parameters = {'column': self.df_shown.columns,
                      'by': self.df_shown.columns}
        prompt = ChartInputDialog(window_title='Create Box Plot',
                                 parameters=parameters,
                                 headers_highlighted=self.headers_highlighted)
        if prompt.exec_() == prompt.Accepted:
            column, by = prompt.get_user_choice()

            try:
                sns.boxplot(x=by, y=column, data=self.df_shown)
            except:
                print(traceback.print_exc())
            else:
                plt.show()

    def distplot(self):
        parameters = {'column': self.df_shown.columns}
        prompt = ChartInputDialog(window_title='Create Box Plot',
                                 parameters=parameters,
                                 headers_highlighted=self.headers_highlighted)
        if prompt.exec_() == prompt.Accepted:
            column = prompt.get_user_choice()[0]
            data = self.df_shown[column]

            try:
                sns.distplot(data)
            except:
                print(traceback.print_exc())
            else:
                plt.show()

    def printdf(self):
        print('debug')


class ChartInputDialog(QtWidgets.QDialog):

    def __init__(self, window_title, parameters, headers_highlighted):
        """
        Creates a popup dialog to get user inputs to plot a chart.

        Args:
            window_title: string to label to window.
            parameters: dictionary of chart input parameters
                        {parameter name: parameter options}
            headers_highlighted: list of ints. Each element is the index
                                 of the column highlighted.
        """
        super().__init__()
        self.headers_highlighted = headers_highlighted
        self.parameters = parameters
        self.createFormGroupBox()

        # Creates the 'OK' and 'Cancel' buttons.
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                               QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        # Adds the input form to the layout.
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle(window_title)

    def createFormGroupBox(self):
        """
        Creates the form to get the columns the user wants to use
        to plot the chart using QComboBox widgets.
        If the headers highlighted are equal to the parameters the chart
        needs, autofills the QComboboxes with the highlighted columns.
        """
        self.formGroupBox = QtWidgets.QGroupBox("Form layout")
        layout = QtWidgets.QFormLayout()

        self.chart_parameter_widgets = {}
        # loops through the parameters, makes them into combo boxes
        # and adds to a dict {parameter name: QComboBox widget}.
        for i, (label, options) in enumerate(self.parameters.items()):
            self.chart_parameter_widgets[label] = QtWidgets.QComboBox()
            self.chart_parameter_widgets[label].addItems(options)
            layout.addRow(QtWidgets.QLabel(label), self.chart_parameter_widgets[label])

            if len(self.headers_highlighted) == len(self.parameters):
                self.chart_parameter_widgets[label].setCurrentIndex(self.headers_highlighted[i])

        self.formGroupBox.setLayout(layout)

    def get_user_choice(self):
        """
        Method to get the last text in the QComboBox widgets before the
        dialog closed.

        Returns:
            return_values: list of strings from the QComboBox Widgets.
        """
        return_values = [parameter.currentText()
                         for parameter in
                         self.chart_parameter_widgets.values()]
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

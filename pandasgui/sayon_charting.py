####################
# Charts functions.

def scatter_dialog(self):
    from pandasgui.chart_dialogs import scatterDialog
    win = scatterDialog(self.df_dicts, parent=self)


def header_clicked(self, header_index):
    """
    Detects if headers are highlighted. If they are,
    adds them to a class variable holding all the columns
    currently highlighted in a list.
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


def scatter_plot(self):
    """
    Shows a popup dialog asking for the inputs to the chart.
    Then creates a scatter plot if 'OK' is pressed, otherwise
    does nothing.
    """

    has_multiindex = isinstance(self.df_shown.index, pd.core.index.MultiIndex)
    # Dictionary of {parameter name: possible options}
    parameters = {'x_values': self.df_shown.columns,
                  'y_values': self.df_shown.columns}

    # Makes an instance of a popup dialog to collect information.
    prompt = ChartInputDialog(window_title='Create Scatter Plot',
                              parameters=parameters,
                              headers_highlighted=self.headers_highlighted,
                              multiindex=has_multiindex)

    # If the accept button is pressed, get the choices and plot.
    # Otherwise ignore.
    if prompt.exec_() == prompt.Accepted:
        x, y = prompt.get_user_choice()

        # a figure instance to plot on
        chart_figure = plt.figure()

        try:
            ax = chart_figure.add_subplot(111)
            ax.scatter(self.df_shown[x], self.df_shown[y])
        except:
            print(traceback.print_exc())
        else:
            plt.show()


def boxplot(self):
    parameters = {'column': self.df_shown.columns,
                  'by': self.df_shown.columns}
    has_multiindex = isinstance(self.df_shown.index, pd.core.index.MultiIndex)
    prompt = ChartInputDialog(window_title='Create Box Plot',
                              parameters=parameters,
                              headers_highlighted=self.headers_highlighted,
                              multiindex=has_multiindex)
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
    has_multiindex = isinstance(self.df_shown.index, pd.core.index.MultiIndex)
    prompt = ChartInputDialog(window_title='Create Box Plot',
                              parameters=parameters,
                              headers_highlighted=self.headers_highlighted,
                              multiindex=has_multiindex)
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

    def __init__(self, window_title, parameters,
                 headers_highlighted, multiindex):
        """
        Creates a popup dialog to get user inputs to plot a chart.

        Args:
            window_title: String to set the window name in the title bar.
            parameters: Dictionary of chart input parameters
                        {parameter name: parameter options}
            headers_highlighted: List of ints. Each element is the index of
                                 any columns highlighted in the main window.
            multiindex: Bool that describes if the dataframe columns
                        are multiindexed.
        """
        super().__init__()
        self.headers_highlighted = headers_highlighted
        self.parameters = parameters
        self.df_has_multiindex_columns = multiindex

        # Initializes make_input_form() class variables.
        self.input_form = None
        self.chart_combobox_widgets = None

        self.make_input_form()

        # Creates the 'OK' and 'Cancel' buttons.
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                                               QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        # Adds the input form to the layout.
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.input_form)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle(window_title)
        self.resize(300, 100)

    def make_input_form(self):
        """
        Creates the form to get the columns the user wants to use
        to plot the chart.
        Displays options using QComboBox widgets.
        """
        self.input_form = QtWidgets.QGroupBox('Plot with Parameters:')
        layout = QtWidgets.QFormLayout()

        self.chart_combobox_widgets = []
        # Iterates through the parameters, makes them into combo boxes
        # and adds to a list of QComboBox widgets.
        for i, (label, options) in enumerate(self.parameters.items()):
            # Converts options to strings in the case that the options
            # are defined as tuples (i.e. in multiindexed columns).
            options = [str(option) for option in options]
            combobox_widget = QtWidgets.QComboBox()
            combobox_widget.addItems(options)
            self.chart_combobox_widgets.append(combobox_widget)
            layout.addRow(QtWidgets.QLabel(label), self.chart_combobox_widgets[i])

            # If the headers highlighted are equal to the parameters the chart
            # needs, autofills the QComboboxes with the highlighted columns.
            if len(self.headers_highlighted) == len(self.parameters):
                self.chart_combobox_widgets[i].setCurrentIndex(self.headers_highlighted[i])

        self.input_form.setLayout(layout)

    def get_user_choice(self):
        """
        Method to get the last text in all QComboBox widgets before the
        dialog closed. If the dataframe is multiindexed, converts the text
        to a tuple before returning.

        Returns:
            last_combobox_values: list of strings or tuples(if dataframe
                                  columns are multiindexed) pulled from
                                  QComboBox widgets text.
        """
        last_combobox_values = []
        for combobox in self.chart_combobox_widgets:
            combobox_text = combobox.currentText()
            if self.df_has_multiindex_columns:
                # Finds text in between single quotes to add to tuple.
                combobox_tuple = tuple(combobox_text.split("'")[1::2])
                last_combobox_values.append(combobox_tuple)
            else:
                last_combobox_values.append(combobox_text)

        return last_combobox_values



###

scatterChartAction = QtWidgets.QAction('&Scatter Chart', self)
scatterChartAction.triggered.connect(self.scatter_plot)
chartMenu.addAction(scatterChartAction)

boxplotChartAction = QtWidgets.QAction('&Box Plot', self)
boxplotChartAction.triggered.connect(self.boxplot)
chartMenu.addAction(boxplotChartAction)

distplotChartAction = QtWidgets.QAction('&Distribution Plot', self)
distplotChartAction.triggered.connect(self.distplot)
chartMenu.addAction(distplotChartAction)

scatterDialogAction = QtWidgets.QAction('&Scatter Dialog', self)
scatterDialogAction.triggered.connect(self.scatter_dialog)
chartMenu.addAction(scatterDialogAction)

'''
Menu that appears on right clicking a column header. Contains options for modifying DataFrame columns
'''

import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from pandasgui.store import PandasGuiDataFrameStore


class ColumnMenu(QtWidgets.QMenu):
    def __init__(self, pgdf: PandasGuiDataFrameStore, column_ix: int, parent=None):
        super().__init__(parent)

        self.pgdf = pgdf
        self.column_ix = column_ix

        ########################
        # Info
        label = QtWidgets.QLabel(self.pgdf.df_unfiltered.columns[column_ix])
        self.add_widget(label)

        ########################
        # Sorting

        def select_button():
            self.sort_b1.setDown(self.pgdf.sort_state == 'Asc' and self.pgdf.sorted_column_ix == column_ix)
            self.sort_b2.setDown(self.pgdf.sort_state == 'Desc' and self.pgdf.sorted_column_ix == column_ix)
            self.sort_b3.setDown(self.pgdf.sort_state == 'None' or self.pgdf.sorted_column_ix != column_ix)

        self.sort_b1 = QtWidgets.QPushButton("Asc")
        self.sort_b1.clicked.connect(lambda: [self.pgdf.sort_column(self.column_ix, "Asc"),
                                              select_button()])

        self.sort_b2 = QtWidgets.QPushButton("Desc")
        self.sort_b2.clicked.connect(lambda: [self.pgdf.sort_column(self.column_ix, "Desc"),
                                              select_button()])

        self.sort_b3 = QtWidgets.QPushButton("None")
        self.sort_b3.clicked.connect(lambda: [self.pgdf.sort_column(self.column_ix, "None"),
                                              select_button()])

        select_button()

        sort_control = QtWidgets.QWidget()
        sort_control_layout = QtWidgets.QHBoxLayout()
        sort_control_layout.setSpacing(0)
        sort_control_layout.setContentsMargins(0, 0, 0, 0)
        sort_control.setLayout(sort_control_layout)
        [sort_control_layout.addWidget(w) for w in [self.sort_b1, self.sort_b2, self.sort_b3]]

        self.add_widget(sort_control)

        ########################
        # Move

        col_name = self.pgdf.df.columns[column_ix]
        self.move_b1 = QtWidgets.QPushButton("<<")
        self.move_b1.clicked.connect(lambda: [self.pgdf.move_column(column_ix, -1, True),
                                              self.close(), self.pgdf.dataframe_viewer.show_column_menu(col_name)])
        self.move_b2 = QtWidgets.QPushButton("<")
        self.move_b2.clicked.connect(lambda: [self.pgdf.move_column(column_ix, -1, False),
                                              self.close(), self.pgdf.dataframe_viewer.show_column_menu(col_name)])
        self.move_b3 = QtWidgets.QPushButton(">")
        self.move_b3.clicked.connect(lambda: [self.pgdf.move_column(column_ix, 1, False),
                                              self.close(), self.pgdf.dataframe_viewer.show_column_menu(col_name)])
        self.move_b4 = QtWidgets.QPushButton(">>")
        self.move_b4.clicked.connect(lambda: [self.pgdf.move_column(column_ix, 1, True),
                                              self.close(), self.pgdf.dataframe_viewer.show_column_menu(col_name)])

        move_control = QtWidgets.QWidget()
        move_control_layout = QtWidgets.QHBoxLayout()
        move_control_layout.setSpacing(0)
        move_control_layout.setContentsMargins(0, 0, 0, 0)
        move_control.setLayout(move_control_layout)
        [move_control_layout.addWidget(w) for w in [self.move_b1, self.move_b2, self.move_b3, self.move_b4]]

        self.add_widget(move_control)

        ########################
        # Delete

        button = QtWidgets.QPushButton("Delete Column")
        button.clicked.connect(lambda: [self.pgdf.delete_column(column_ix), self.close()])
        self.add_widget(button)

        ########################
        # Coloring
        self.add_action("Color by None",
                        lambda: [setattr(self.pgdf.dataframe_viewer, 'color_mode', None),
                                 self.pgdf.dataframe_viewer.refresh_ui()]
                        )

        self.add_action("Color by columns",
                        lambda: [setattr(self.pgdf.dataframe_viewer, 'color_mode', 'column'),
                                 self.pgdf.dataframe_viewer.refresh_ui()]
                        )

        self.add_action("Color by rows",
                        lambda: [setattr(self.pgdf.dataframe_viewer, 'color_mode', 'row'),
                                 self.pgdf.dataframe_viewer.refresh_ui()]
                        )

        self.add_action("Color by all",
                        lambda: [setattr(self.pgdf.dataframe_viewer, 'color_mode', 'all'),
                                 self.pgdf.dataframe_viewer.refresh_ui()]
                        )

    def add_action(self, text, function):
        action = QtWidgets.QAction(text, self)
        action.triggered.connect(function)
        self.addAction(action)

    def add_widget(self, widget):
        # https://stackoverflow.com/questions/55086498/highlighting-custom-qwidgetaction-on-hover
        widget.setMouseTracking(True)

        custom_action = QtWidgets.QWidgetAction(self)
        widget.setStyleSheet(widget.styleSheet() + "margin: 5px;")
        custom_action.setDefaultWidget(widget)
        self.addAction(custom_action)

    def show_menu(self, point):
        self.move(point)
        self.show()


if __name__ == "__main__":
    # Create a QtWidgets.QApplication instance or use the existing one if it exists
    app = QtWidgets.QApplication(sys.argv)
    from pandasgui.datasets import pokemon
    from pandasgui import show

    # gui = show(pokemon)

    w = ColumnMenu(pokemon, 0)
    app.exec_()

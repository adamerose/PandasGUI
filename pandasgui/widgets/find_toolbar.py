from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
import os
from functools import reduce
import pkg_resources

class Find_Toolbar(QtWidgets.QToolBar):
    def __init__(self, parent):
        """
        Creates modified toolbar with only a find textbox and match modification.

        Args:
            parent: parent widget (the gui) is required to access the current
                    DataFrame shown to the user.
        """
        super().__init__(parent=parent)

        # global variable initialization
        self.search_matches = []
        self.search_selection = None
        self.match_flags = [QtCore.Qt.MatchContains]
        self.image_folder = '../images'

        # main toolbar widget
        find_toolbar_widget = QtWidgets.QWidget()
        find_toolbar_layout = QtWidgets.QHBoxLayout()
        find_toolbar_layout.setContentsMargins(0, 0, 0, 0)
        find_toolbar_layout.setSpacing(0)
        find_toolbar_widget.setLayout(find_toolbar_layout)

        # textedit portion of toolbar
        
        self.find_textbox = ButtonLineEdit(content_margins=(0, 0, 5, 0))
        self.find_textbox.setPlaceholderText('Find')
        self.find_textbox.textChanged.connect(self.find)

        # add match modification
        self.match_flags = [QtCore.Qt.MatchContains]
        match_case_icon_raw_path = self.image_folder + '/case-match.png'
        match_case_icon_path = pkg_resources.resource_filename(__name__,
                                                               match_case_icon_raw_path)
        match_case_icon = QtGui.QIcon(match_case_icon_path)
        self.find_textbox.add_button(match_case_icon, connection=self.toggle_match_case,
                                     tooltip='Match Case')
        regex_icon_raw_path = self.image_folder + '/curly-brackets.png'
        regex_icon_path = pkg_resources.resource_filename(__name__,
                                                          regex_icon_raw_path)       
        regex_icon = QtGui.QIcon(regex_icon_path)
        self.find_textbox.add_button(regex_icon, connection=self.toggle_regex,
                                     tooltip='Use Regular Expression')
        match_exactly_icon_raw_path = self.image_folder + '/match-exactly.png'
        match_exactly_icon_path = pkg_resources.resource_filename(__name__,
                                                                  match_exactly_icon_raw_path)       
        whole_word_icon = QtGui.QIcon(match_exactly_icon_path)
        self.find_textbox.add_button(whole_word_icon, connection=self.toggle_match_exactly,
                                     tooltip='Match Exactly')
        find_toolbar_layout.addWidget(self.find_textbox)

        # go up a match
        previous_match_button = QtWidgets.QPushButton()
        up_arrow_icon_raw_path = self.image_folder + '/up-arrow.png'
        up_arrow_icon_path = pkg_resources.resource_filename(__name__,
                                                             up_arrow_icon_raw_path) 
        up_arrow_icon = QtGui.QIcon(up_arrow_icon_path)
        previous_match_button.setIcon(up_arrow_icon)
        previous_match_button.setToolTip('Previous match (Shift + Enter)')
        previous_match_button.setShortcut('Shift+Return')
        previous_match_button.clicked.connect(self.select_previous_match)
        find_toolbar_layout.addWidget(previous_match_button)

        # go down a match
        next_match_button = QtWidgets.QPushButton()
        down_arrow_icon_raw_path = self.image_folder + '/down-arrow.png'
        down_arrow_icon_path = pkg_resources.resource_filename(__name__,
                                                               down_arrow_icon_raw_path) 
        down_arrow_icon = QtGui.QIcon(down_arrow_icon_path)
        next_match_button.setIcon(down_arrow_icon)
        next_match_button.setToolTip('Next match (Enter)')
        next_match_button.setShortcut('Return')
        next_match_button.clicked.connect(self.select_next_match)
        find_toolbar_layout.addWidget(next_match_button)

        # close find toolbar
        close_find_button = QtWidgets.QPushButton()
        cancel_icon_raw_path = self.image_folder + '/cancel.png'
        cancel_icon_path = pkg_resources.resource_filename(__name__,
                                                           cancel_icon_raw_path) 
        close_icon = QtGui.QIcon(cancel_icon_path)
        close_find_button.setIcon(close_icon)
        close_find_button.clicked.connect(self.hide_find_bar)
        find_toolbar_layout.addWidget(close_find_button)

        self.addWidget(find_toolbar_widget)
        
        # hide toolbar
        self.setFixedHeight(0)
    
    def find(self, text):
        # get current dataframe data
        current_df = self.parent().stacked_widget.currentWidget().dataframe_tab
        df_data = current_df.dataView
        model = df_data.model()

        # clear matches and selection from last search results
        self.search_matches = []
        df_data.selectionModel().clear()

        if not text: return

        # match algorithm. Iterate through the columns and then rows to find matches.
        for i in range(model.columnCount()):
            start = model.index(0, i)
            # Qt.MatchFlags requires that binary OR is recursively applied to all flags
            combined_match_flags = reduce(lambda x, y: x | y, self.match_flags)
            # gives list of indices of cells with successful match
            matches = model.match(start, QtCore.Qt.DisplayRole,
                                  text, -1, QtCore.Qt.MatchFlags(combined_match_flags))
            self.search_matches.extend(matches)

        if self.search_matches:
            # highlight first match
            self.search_selection = 0
            self.highlight_match()
        
    def show_find_bar(self):
        if self.height() == 0:
            animation_duration = 200
            full_toolbar_height = 30

            showAnimation = QtCore.QVariantAnimation(self)
            showAnimation.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
            showAnimation.setDuration(animation_duration)
            showAnimation.setStartValue(0)
            showAnimation.setEndValue(full_toolbar_height)
            showAnimation.valueChanged.connect(lambda val: self.setFixedHeight(val))

            showAnimation.start()

    def hide_find_bar(self):
        if self.height() == 30:
            hideAnimation = QtCore.QVariantAnimation(self)
            hideAnimation.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
            hideAnimation.setDuration(200)
            hideAnimation.setStartValue(30)
            hideAnimation.setEndValue(0)
            hideAnimation.valueChanged.connect(lambda val: self.setFixedHeight(val))

            hideAnimation.start()
    
    def select_next_match(self):
        if self.search_matches:
            # loop around to the first match if user hits last match
            if self.search_selection == len(self.search_matches)-1:
                self.search_selection = 0
            else:
                self.search_selection +=1

            self.highlight_match()
    
    def select_previous_match(self):
        if self.search_matches:
            # loop around to the last match if user hits first match
            if self.search_selection == 0:
                self.search_selection = len(self.search_matches)-1
            else:
                self.search_selection -=1

            self.highlight_match()
    
    def highlight_match(self):
        current_df = self.parent().stacked_widget.currentWidget().dataframe_tab
        df_data = current_df.dataView

        # clear last seletion
        df_data.selectionModel().clear()

        df_data.selectionModel().select(self.search_matches[self.search_selection],
                                        QtCore.QItemSelectionModel.Select)
        df_data.scrollTo(self.search_matches[self.search_selection])
    
    def toggle_match_case(self):
        if QtCore.Qt.MatchCaseSensitive in self.match_flags:
            self.match_flags.remove(QtCore.Qt.MatchCaseSensitive)
        else:
            self.match_flags.append(QtCore.Qt.MatchCaseSensitive)
        
        if self.find_textbox.text():
            self.find(self.find_textbox.text())

    def toggle_regex(self):
        if QtCore.Qt.MatchRegExp in self.match_flags:
            self.match_flags.remove(QtCore.Qt.MatchRegExp)
            self.match_flags.append(QtCore.Qt.MatchContains)
        else:
            self.match_flags.append(QtCore.Qt.MatchRegExp)
            if QtCore.Qt.MatchContains in self.match_flags:
                self.match_flags.remove(QtCore.Qt.MatchContains)
        
        if self.find_textbox.text():
            self.find(self.find_textbox.text())

    def toggle_match_exactly(self):
        if QtCore.Qt.MatchExactly in self.match_flags:
            self.match_flags.remove(QtCore.Qt.MatchExactly)
            self.match_flags.append(QtCore.Qt.MatchContains)
        else:
            self.match_flags.append(QtCore.Qt.MatchExactly)
            self.match_flags.remove(QtCore.Qt.MatchContains)
        
        if self.find_textbox.text():
            self.find(self.find_textbox.text())

class ButtonLineEdit(QtWidgets.QLineEdit):
    buttonClicked = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None, content_margins=(0, 0, 0, 0)):
        '''
        Modified LineEdit with buttons inside the LineEdit.
        '''
        super(ButtonLineEdit, self).__init__(parent)

        self.setContentsMargins(*content_margins)
        self.buttons = []

    def resizeEvent(self, event):
        '''
        Moves all buttons to the correct position or else the buttons will
        be stacked on top of each other on the left.
        '''
        frameWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
        right_margin = self.getContentsMargins()[2]
        bottom_margin = self.getContentsMargins()[3]

        for i, button in enumerate(self.buttons):
            buttonSize = button.sizeHint()
            button.move(self.rect().right() - frameWidth - buttonSize.width()*(i+1) - right_margin,
                        (self.rect().bottom() - buttonSize.height() + 1)/2 - bottom_margin)
        super(ButtonLineEdit, self).resizeEvent(event)
    
    def add_button(self, icon, connection, tooltip=None, checkable=True):
        button = QtWidgets.QToolButton(self)
        button.setIcon(icon)
        if tooltip: button.setToolTip(tooltip)
        button.setCursor(QtCore.Qt.PointingHandCursor)
        button.setCheckable(checkable)
        button.clicked.connect(connection)

        self.buttons.append(button)

        # makes sure text doesn't type behind the buttons
        totalWidth = sum([b.sizeHint().width() for b in self.buttons])
        frameWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
        right_padding = int(totalWidth + frameWidth + 1)
        self.setStyleSheet(f'QLineEdit {{padding-right: {right_padding}px; }}' )

        # makes sure the typing area doesn't get too small if toolbar is shrunk.
        maxHeight = max([b.sizeHint().height() for b in self.buttons])
        self.setMinimumSize(max(self.minimumSizeHint().width(), totalWidth + frameWidth*2 + 2),
                            max(self.minimumSizeHint().height(), maxHeight + frameWidth*2 + 2))


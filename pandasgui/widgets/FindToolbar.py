from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
import os
from functools import reduce, partial
import pkg_resources
import numpy as np
import threading
import re

class FindToolbar(QtWidgets.QToolBar):
    def __init__(self, parent):
        """
        Creates modified toolbar with only a find textbox and match modification.

        Args:
            parent: parent widget (the gui) is required to access the current
                    DataFrame shown to the user.
        """
        super().__init__(parent=parent)

        # global variable initialization
        self.findThread = None
        self.search_matches = []
        self.search_selection = None
        self.match_flags = {'regex': False,
                            'case': False,
                            'whole word': False}
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
        self.find_textbox.textChanged.connect(self.query)

        ####################
        # add match modification

        # add match case button
        match_case_icon_raw_path = self.image_folder + '/case-match.png'
        match_case_icon_path = pkg_resources.resource_filename(__name__,
                                                               match_case_icon_raw_path)
        match_case_icon = QtGui.QIcon(match_case_icon_path)
        self.match_case_button = QtWidgets.QToolButton(self.find_textbox)
        self.match_case_button.setIcon(match_case_icon)
        self.match_case_button.setToolTip('Match Case')
        self.match_case_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.match_case_button.setCheckable(True)
        self.match_case_button.clicked.connect(self.toggle_match_case)
        self.find_textbox.add_button(self.match_case_button)

        # add match regex button
        regex_icon_raw_path = self.image_folder + '/curly-brackets.png'
        regex_icon_path = pkg_resources.resource_filename(__name__,
                                                          regex_icon_raw_path)       
        regex_icon = QtGui.QIcon(regex_icon_path)
        self.match_regex_button = QtWidgets.QToolButton(self.find_textbox)
        self.match_regex_button.setIcon(regex_icon)
        self.match_regex_button.setToolTip('Use Regular Expression')
        self.match_regex_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.match_regex_button.setCheckable(True)
        self.match_regex_button.clicked.connect(self.toggle_regex)
        self.find_textbox.add_button(self.match_regex_button)        

        # add match exactly button
        match_exactly_icon_raw_path = self.image_folder + '/match-exactly.png'
        match_exactly_icon_path = pkg_resources.resource_filename(__name__,
                                                                  match_exactly_icon_raw_path)       
        whole_word_icon = QtGui.QIcon(match_exactly_icon_path)
        self.match_exactly_button = QtWidgets.QToolButton(self.find_textbox)
        self.match_exactly_button.setIcon(whole_word_icon)
        self.match_exactly_button.setToolTip('Match Exactly')
        self.match_exactly_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.match_exactly_button.setCheckable(True)
        self.match_exactly_button.clicked.connect(self.toggle_match_exactly)
        self.find_textbox.add_button(self.match_exactly_button)
        find_toolbar_layout.addWidget(self.find_textbox)

        self.matches_found_label = QtWidgets.QLabel('Matches Found: 0')
        self.matches_found_label.setContentsMargins(0, 0, 7, 0)
        find_toolbar_layout.addWidget(self.matches_found_label)

        ####################
        # Main toolbar buttons

        # go to next match
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

        # go to previous match
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
        close_find_button.setToolTip('Close Find Bar')
        close_find_button.clicked.connect(self.hide_find_bar)
        find_toolbar_layout.addWidget(close_find_button)

        self.addWidget(find_toolbar_widget)
        
        # hide toolbar
        self.setFixedHeight(0)

    @QtCore.pyqtSlot(str)
    def query(self, text):
        '''
        Query operation done each time user changes the text.

        Args:
            text: text to search for.
        '''
        # get current dataframe data
        current_df = self.parent().stacked_widget.currentWidget().dataframe_tab
        self.current_dataView = current_df.dataView
        self.current_model = self.current_dataView.model()
        df = self.current_model.df

        # clear matches and selection from last search results
        if self.findThread: self.findThread.stop()
        self.search_matches = []
        self.current_dataView.selectionModel().clear()
        self.matches_found_label.setText('Matches Found: 0')
        self.search_selection = None

        if not text: return
        
        # Initialize findThread
        self.findThread = FindThread(df, text, self.match_flags)
        self.findThread.matches.connect(self.update_matches)
        self.findThread.start()
    
    @QtCore.pyqtSlot(list)
    def update_matches(self, cells_matched):
        '''
        PyQt Slot that updates the matches found each time it gets a signal.

        Args:
            cells_matched: list of tuples - (row, col). Type QtCore.pyqtSignal(list).
        '''
        # converts list of tuples to list of QtCore.QModelIndex for easy selection.
        match_idxs = [self.current_model.index(row, col) for row, col in cells_matched]
        self.search_matches.extend(match_idxs)

        matches_found_text = 'Matches Found: ' + str(len(self.search_matches))
        self.matches_found_label.setText(matches_found_text)

        if self.search_matches and self.search_selection is None:
            # highlight first match
            self.search_selection = 0
            self.highlight_match()

    @QtCore.pyqtSlot()
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
            
            # clear the last search, and set cursor on the QLineEdit
            self.find_textbox.setText('')
            self.find_textbox.setFocus()

    @QtCore.pyqtSlot()
    def hide_find_bar(self):
        if self.height() == 30:
            animation_duration = 200
            full_toolbar_height = 30

            hideAnimation = QtCore.QVariantAnimation(self)
            hideAnimation.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
            hideAnimation.setDuration(animation_duration)
            hideAnimation.setStartValue(full_toolbar_height)
            hideAnimation.setEndValue(0)
            hideAnimation.valueChanged.connect(lambda val: self.setFixedHeight(val))

            hideAnimation.start()

            # stop any running findThread
            if self.findThread: self.findThread.stop()
    
    @QtCore.pyqtSlot()
    def select_next_match(self):
        if self.search_matches:
            # loop around to the first match if user hits last match
            if self.search_selection == len(self.search_matches)-1:
                self.search_selection = 0
            else:
                self.search_selection +=1

            self.highlight_match()
    
    @QtCore.pyqtSlot()
    def select_previous_match(self):
        if self.search_matches:
            # loop around to the last match if user hits first match
            if self.search_selection == 0:
                self.search_selection = len(self.search_matches)-1
            else:
                self.search_selection -=1

            self.highlight_match()
    
    @QtCore.pyqtSlot()
    def toggle_match_case(self):
        self.match_flags['case'] = not self.match_flags['case']
        
        if self.find_textbox.text():
            self.query(self.find_textbox.text())

    @QtCore.pyqtSlot()
    def toggle_regex(self):
        self.match_flags['regex'] = not self.match_flags['regex']
        if self.match_flags['whole word']:
            self.match_flags['whole word'] = False
            self.match_exactly_button.setChecked(False)
        
        if self.find_textbox.text():
            self.query(self.find_textbox.text())

    @QtCore.pyqtSlot()
    def toggle_match_exactly(self):
        self.match_flags['whole word'] = not self.match_flags['whole word']
        if self.match_flags['regex']:
            self.match_flags['regex'] = False
            self.match_regex_button.setChecked(False)
        
        if self.find_textbox.text():
            self.query(self.find_textbox.text())
    
    def highlight_match(self):
        # clear last seletion
        self.current_dataView.selectionModel().clear()

        self.current_dataView.selectionModel().select(self.search_matches[self.search_selection],
                                        QtCore.QItemSelectionModel.Select)
        self.current_dataView.scrollTo(self.search_matches[self.search_selection])

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

    def add_button(self, button):
        '''
        Adds a button to the right side of the QLineEdit.

        Args:
            button: Type QtWidgets.QPushButton or QtWidgets.QToolButton
        '''
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


class FindThread(QtCore.QThread):
    matches = QtCore.pyqtSignal(list)

    def __init__(self, df, text, match_flags, parent=None):
        '''
        Thread to search DataFrame for a string.

        Args:
            df: Type pd.DataFrame
            text: Text to search for. Type string.
            match_flags: User enabled match flags. Can match case, regex, or exact.
                         Type dict.
        '''
        QtCore.QThread.__init__(self, parent=parent)
        self.isRunning = True
        self.df = df
        self.text = text
        self.match_flags = match_flags
        self.max_chunk_size = 10000
        self.chunks = self.split_chunks()
    
    def split_chunks(self):
        '''
        Splits each Series in the DataFrame into many Series.
        Number of chunks outputted depends on size of each column
        and self.max_chunk_size.

        Returns:
            chunks: List of pd.Series.
        '''
        chunks = []
        for col_idx, col_name in enumerate(self.df.columns):
            column = self.df[col_name].copy()
            while len(column) > 0:
                chunk = column.iloc[:self.max_chunk_size]
                chunks.append(chunk)
                column = column.iloc[self.max_chunk_size:]
        return chunks
    
    def get_matches(self, chunk):
        '''
        Gets row numbers of matches.

        Args:
            chunk: Type pd.Series
        '''
        if self.match_flags['whole word']:
            if self.match_flags['case']:
                rows_with_match = chunk[chunk == self.text]               
            else:
                rows_with_match = chunk[chunk.astype(str).str.lower() == self.text.lower()]
        else:
            pd_match_flags = self.match_flags.copy()
            pd_match_flags.pop('whole word')
            check_for_match = chunk.astype(str).str.contains(self.text,
                                                             **pd_match_flags)
            rows_with_match = chunk[check_for_match]

        return rows_with_match

    def run(self):
        col_idx = 0
        # since the chunks don't preserve row number, need to keep track of
        # chunks processed to get row number
        chunks_in_column = 0
        for chunk in self.chunks:
            try:
                # gives series with dtype bool
                rows_with_match = self.get_matches(chunk)
                # gives indicies where the series is True
                row_idx_with_match = [chunk.index.get_loc(i)
                                      + chunks_in_column*self.max_chunk_size
                                      for i in rows_with_match.index]
                # print(chunk.index.get_loc(rows_with_match.index))
                # output list of table coordinates where match is found
                coords_with_match = [(row_idx, col_idx)
                                    for row_idx in row_idx_with_match]

                # check if a stop is requested
                # (in case the user types another letter)
                if self.isRunning:
                    self.matches.emit(coords_with_match)
                else:
                    break
                    
                chunks_in_column += 1
                
                # if the last index of the chunk is equal to the last index
                # of the whole dataframe, move to the next column
                if chunk.index[-1] == self.df.index[-1]:
                    col_idx += 1
                    chunks_in_column = 0

                # waits 50 milliseconds to process gui interactions,
                # so the gui does not freeze
                time.sleep(0.05)
            except re.error:
                break
        self.isRunning = False

    def stop(self):
        self.isRunning = False
        self.quit()
        self.wait()

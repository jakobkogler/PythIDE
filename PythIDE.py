import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox, QPlainTextEdit, QShortcut
from PyQt5 import QtCore, QtGui
from mainwindow import Ui_MainWindow
import subprocess


class IdeMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)

        self.settings = QtCore.QSettings('ide_settings.ini', QtCore.QSettings.IniFormat)
        width = int(self.settings.value('WindowSettings/Width', '0'))
        height = int(self.settings.value('WindowSettings/Height', '0'))
        if width and height:
            self.resize(width, height)
        desktop = QApplication.desktop()
        center_width = (desktop.width() - self.width())//2
        center_height = (desktop.height() - self.height())//2
        self.move(center_width, center_height)

        # Keyboard shortcuts
        self.shortcuts = []
        add_tab_shortcut = QShortcut(QtGui.QKeySequence('Ctrl+T', 0), self)
        add_tab_shortcut.activated.connect(self.add_new_tab)
        self.shortcuts.append(add_tab_shortcut)
        find_shortcut = QShortcut(QtGui.QKeySequence('Ctrl+F', 0), self)
        find_shortcut.activated.connect(self.find_line_edit.setFocus)
        self.shortcuts.append(find_shortcut)

        self.doc_items = self.get_docs()
        self.fill_doc_table()
        self.doc_table_widget.resizeColumnsToContents()
        self.code_text_edits = []
        self.add_new_tab()

        self.action_run.triggered.connect(lambda: self.run_program(debug_on=False))
        self.action_debug.triggered.connect(lambda: self.run_program(debug_on=True))
        self.action_about.triggered.connect(self.show_about)
        self.find_line_edit.textChanged.connect(self.fill_doc_table)
        self.code_tabs.currentChanged.connect(self.change_tab)

    def change_tab(self, tab_idx):
        count = self.code_tabs.count()
        if count == tab_idx + 1:
            self.add_new_tab()
        self.update_code_length()

    def add_new_tab(self):
        count = self.code_tabs.count()
        code_text_edit = QPlainTextEdit()
        code_text_edit.textChanged.connect(self.update_code_length)
        self.code_text_edits.append(code_text_edit)
        self.code_tabs.insertTab(count - 1, code_text_edit, str(count))
        self.code_tabs.setCurrentIndex(count - 1)
        code_text_edit.setFocus()
        code_text_edit.setTabChangesFocus(True)
        monospace_font = QtGui.QFont()
        monospace_font.setFamily("Monospace")
        code_text_edit.setFont(monospace_font)

        if count < 10:
            tab_shortcut = QShortcut(QtGui.QKeySequence('Alt+' + str(count), 0), self)
            tab_shortcut.activated.connect(lambda: self.code_tabs.setCurrentIndex(count - 1))
            self.shortcuts.append(tab_shortcut)

    def run_program(self, debug_on):
        tab_idx = self.code_tabs.currentIndex()
        code = self.code_text_edits[tab_idx].toPlainText()
        code = '\n'.join(code.split('\r\n'))

        if self.input_tabs.currentIndex() == 0:
            input_data = self.input_text_edit.toPlainText() + '\n'
            message = self.run_code(code, input_data, debug_on)
        else:
            input_data = self.test_suite_text_edit.toPlainText().split('\n')
            input_length = self.test_suite_spinbox.value()
            input_data = ['\n'.join(input_data[i:i+input_length]) for i in range(0, len(input_data), input_length)]

            messages = [self.run_code(code, input_data[0], debug_on)] + \
                [self.run_code(code, input_data, False) for input_data in input_data[1:]]
            message = '\n'.join(messages)

        self.output_text_edit.setPlainText(message)

    @staticmethod
    def run_code(self, code, input_data, debug_on):
        pyth_process = subprocess.Popen(['/usr/bin/env', 'python3', 'pyth/pyth.py',
                                         '-cd' if debug_on else '-c', code],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)

        output, errors = pyth_process.communicate(input=bytearray(input_data, 'utf-8'))
        message = output.decode() + (errors if errors else '')
        return message

    @staticmethod
    def get_docs():
        with open('pyth/web-docs.txt', 'r') as f:
            return [line.split(' ', maxsplit=4) for line in f]

    def fill_doc_table(self):
        self.doc_table_widget.setRowCount(0)
        self.doc_table_widget.setColumnCount(5)
        header = ['Char', 'Arity', 'Starts', 'Mnemonic', 'Details']
        self.doc_table_widget.setHorizontalHeaderLabels(header)

        filter_text = self.find_line_edit.text()
        if not filter_text:
            filtered = self.doc_items
        if len(filter_text) == 1 or (len(filter_text) == 2 and filter_text[0] == '.'):
            filtered = [line for line in self.doc_items if line[0].lower() == filter_text.lower()]
        else:
            filtered = [line for line in self.doc_items if any(filter_text.lower() in item.lower() for item in line)]

        self.doc_table_widget.setRowCount(len(filtered))

        for row, items in enumerate(filtered):
            for column, item in enumerate(items):
                if len(item) > 40:
                    item = self.split_sentence(item, 40)
                table_widget_item = QTableWidgetItem(item)
                if column < 4:
                    table_widget_item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.doc_table_widget.setItem(row, column, table_widget_item)

        self.doc_table_widget.resizeRowsToContents()

    @staticmethod
    def split_sentence(sentence, length):
        lines = [[]]
        for word in sentence.split(' '):
            if len(' '.join(lines[-1] + [word])) > length:
                lines.append([word])
            else:
                lines[-1].append(word)

        lines = [' '.join(line) for line in lines]
        return '\n'.join(lines)

    def closeEvent(self, event):
        """Remember the current window size before closing"""
        self.settings.setValue('WindowSettings/Width', self.width())
        self.settings.setValue('WindowSettings/Height', self.height())
        event.accept()

    @staticmethod
    def show_about(self):
        try:
            with open('version.txt', 'r') as f:
                version = f.read().strip()
                version_msg = "Version {}, commit {}".format(version.split('-')[0][1:],
                                                             version.split('-')[2][1:])
        except FileNotFoundError:
            version_msg = 'Version unknown'

        message_box = QMessageBox()
        message_box.about('About PythIDE',
                          '\n'.join([version_msg, "Copyright (C) 2015 Jakob Kogler, MIT License"]))

    def update_code_length(self):
        current_tab = self.code_tabs.currentIndex()
        code = self.code_text_edits[current_tab].toPlainText()
        self.code_length_label.setText(str(len(code)))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = IdeMainWindow()
    window.show()
    sys.exit(app.exec_())

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, \
    QTableWidgetItem, QMessageBox, QPlainTextEdit, QShortcut
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSlot
from mainwindow import Ui_MainWindow
from clipboard_template import Ui_TemplateDialog
import subprocess
from urllib.parse import quote, unquote
import re
import os
from execute_pyth import CodeExecutor


example_template = """\
# Pyth, {length} bytes

    {code}

Try it online: [Demonstration][1] or [Test Suite][2]

### Expanation:

    {code}


  [1]: {url}
  [2]: {url_test_suite}\
"""


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

        # Prepare docs
        self.doc_items = self.get_docs()
        self.fill_doc_table()
        self.doc_table_widget.resizeColumnsToContents()

        # Prepare code tabs
        self.add_new_tab()

        # Connect signals and slots
        self.action_run.triggered.connect(lambda: self.run_program(debug_on=False))
        self.action_debug.triggered.connect(lambda: self.run_program(debug_on=True))
        self.action_about.triggered.connect(self.show_about)
        self.find_line_edit.textChanged.connect(self.fill_doc_table)
        self.code_tabs.currentChanged.connect(self.update_code_length)
        self.action_open_tab.triggered.connect(self.add_new_tab)
        self.action_close_tab.triggered.connect(self.delete_tab)
        self.action_to_clipboard.triggered.connect(self.to_clipboard)
        self.action_heroku.triggered.connect(self.open_in_browser)
        self.action_define_template.triggered.connect(self.define_template)
        self.action_import_heroku.triggered.connect(self.import_heroku)
        self.action_duplicate.triggered.connect(self.duplicate)

        # Keyboard shortcuts
        self.shortcuts = []
        find_shortcut = QShortcut(QtGui.QKeySequence('Ctrl+F', 0), self)
        find_shortcut.activated.connect(self.find_line_edit.setFocus)
        self.shortcuts.append(find_shortcut)
        rotate = QShortcut(QtGui.QKeySequence('Ctrl+Tab', 0), self)
        rotate.activated.connect(self.rotate_tabs)
        self.shortcuts.append(rotate)
        rotate_back = QShortcut(QtGui.QKeySequence('Ctrl+Shift+Tab', 0), self)
        rotate_back.activated.connect(self.rotate_back_tabs)
        self.shortcuts.append(rotate_back)

    @pyqtSlot()
    def import_heroku(self):
        clipboard = QApplication.clipboard()
        url = clipboard.text()
        if 'pyth.herokuapp.com' in url:
            url = url.replace('+', ' ')
            parameters = re.split('[?=&]', url)[1:]
            params_dict = {parameters[i]: unquote(parameters[i+1]) for i in range(0, len(parameters), 2)}

            if 'code' in params_dict:
                if len(self.code_tabs.currentWidget().toPlainText()):
                    self.add_new_tab()
                self.code_tabs.currentWidget().setPlainText(params_dict['code'])
            if 'input' in params_dict:
                self.input_text_edit.setPlainText(params_dict['input'])
            if 'test_suite_input' in params_dict:
                self.test_suite_text_edit.setPlainText(params_dict['test_suite_input'])
            if 'input_size' in params_dict:
                self.test_suite_spinbox.setValue(int(params_dict['input_size']))
            if 'test_suite' in params_dict:
                self.input_tabs.setCurrentIndex(int(params_dict['test_suite']))
            else:
                self.input_tabs.setCurrentIndex(0)
        else:
            QMessageBox().about(self, 'Import from Heroku-App',
                                '\n'.join(['Copy the Permalink of the Heroku-App.',
                                           'The url will be extracted from the Clipboard.']))

    def get_url(self, show_test_suite=False):
        code = self.code_tabs.currentWidget().toPlainText()
        input_data = self.input_text_edit.toPlainText()
        test_suite_data = self.test_suite_text_edit.toPlainText()
        url_parameter = dict()
        url_parameter['code'] = code
        if input_data:
            url_parameter['input'] = input_data
        if test_suite_data:
            url_parameter['test_suite_input'] = test_suite_data
            url_parameter['test_suite'] = '1' if show_test_suite else '0'
            input_size = self.test_suite_spinbox.value()
            if input_size > 1:
                url_parameter['input_size'] = str(input_size)
        combined_parameter = '&'.join(key + '=' + quote(value) for key, value in url_parameter.items())
        return 'http://pyth.herokuapp.com/?' + combined_parameter

    @pyqtSlot()
    def open_in_browser(self):
        url = self.get_url(self.input_tabs.currentIndex() == 1)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    @pyqtSlot()
    def to_clipboard(self):
        code = self.code_tabs.currentWidget().toPlainText()

        template = self.settings.value('Template/Template', example_template)
        export = template.format(code=code, length=self.code_length(), url=self.get_url(),
                                 url_test_suite=self.get_url(True))

        clipboard = QApplication.clipboard()
        clipboard.setText(export)

    @pyqtSlot()
    def define_template(self):
        template_diaglog = TemplateDialog(self.settings)
        template_diaglog.exec_()

    @pyqtSlot()
    def delete_tab(self):
        current_index = self.code_tabs.currentIndex()
        self.code_tabs.removeTab(current_index)

        # Update all header, quite hacky
        current_index = self.code_tabs.currentIndex()
        for i in range(self.code_tabs.count()):
            self.code_tabs.setCurrentIndex(i)
            self.update_code_length()
        self.code_tabs.setCurrentIndex(current_index)

    @pyqtSlot()
    def rotate_tabs(self):
        current_index = self.code_tabs.currentIndex()
        new_index = (current_index + 1) % self.code_tabs.count()
        self.code_tabs.setCurrentIndex(new_index)

    @pyqtSlot()
    def rotate_back_tabs(self):
        current_index = self.code_tabs.currentIndex()
        new_index = (current_index - 1) % self.code_tabs.count()
        self.code_tabs.setCurrentIndex(new_index)

    @pyqtSlot()
    def add_new_tab(self):
        count = self.code_tabs.count()
        code_text_edit = QPlainTextEdit()
        code_text_edit.textChanged.connect(self.update_code_length)
        self.code_tabs.addTab(code_text_edit, str(count + 1))
        self.code_tabs.setCurrentIndex(count)
        code_text_edit.setFocus()
        code_text_edit.setTabChangesFocus(True)
        monospace_font = QtGui.QFont()
        monospace_font.setFamily("Monospace")
        code_text_edit.setFont(monospace_font)
        self.update_code_length()

    @pyqtSlot()
    def duplicate(self):
        code = self.code_tabs.currentWidget().toPlainText()
        self.add_new_tab()
        self.code_tabs.currentWidget().setPlainText(code)

    def output_clear(self):
        self.output_text_edit.clear()

    def output_write(self, text):
        self.output_text_edit.insertPlainText(text)

    def run_program(self, debug_on):
        code_text_edit = self.code_tabs.currentWidget()
        code = code_text_edit.toPlainText()
        code = '\n'.join(code.split('\r\n'))
        multi_line_on = self.action_multi_line.isChecked()

        self.code_executor = CodeExecutor(code, '')
        self.code_executor.text_edit_clear.connect(self.output_clear)
        self.code_executor.text_edit_write.connect(self.output_write)
        self.code_executor.start()
        #run_print_code(code, '', self.output_text_edit)
        # if self.input_tabs.currentIndex() == 0:
        #     input_data = self.input_text_edit.toPlainText() + '\n'
        #     message = self.run_code(code, input_data, debug_on, multi_line_on)
        # else:
        #     input_data = self.test_suite_text_edit.toPlainText().split('\n')
        #     input_length = self.test_suite_spinbox.value()
        #     input_data = ['\n'.join(input_data[i:i+input_length]) for i in range(0, len(input_data), input_length)]
        #
        #     messages = [self.run_code(code, input_data[0], debug_on, multi_line_on)] + \
        #         [self.run_code(code, input_data, False, multi_line_on) for input_data in input_data[1:]]
        #     message = '\n'.join(messages)
        #
        #self.output_text_edit.setPlainText(message)

    @staticmethod
    def run_code(code, input_data, debug_on=False, multi_line_on=False):
        real_path = os.path.realpath(__file__)
        pyth_path = os.path.split(real_path)[0] + '/pyth/pyth.py'
        flags = ['-', 'c']
        if debug_on:
            flags.append('d')
        if multi_line_on:
            flags.append('m')
        pyth_process = subprocess.Popen(['/usr/bin/env', 'python3', pyth_path, ''.join(flags), code],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)

        output, errors = pyth_process.communicate(input=bytearray(input_data, 'utf-8'))
        message = output.decode() + (errors if errors else '')
        return message

    @staticmethod
    def get_docs():
        real_path = os.path.realpath(__file__)
        web_docs_path = os.path.split(real_path)[0] + '/pyth/web-docs.txt'
        with open(web_docs_path, 'r') as f:
            return [line.split(' ', maxsplit=4) for line in f]

    @pyqtSlot()
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

    @pyqtSlot()
    def show_about(self):
        try:
            with open('version.txt', 'r') as f:
                version = f.read().strip()
                version_msg = "Version {}, commit {}".format(version.split('-')[0][1:],
                                                             version.split('-')[2][1:])
        except FileNotFoundError:
            version_msg = 'Version unknown'

        QMessageBox().about(self, 'About PythIDE', '\n'.join([version_msg, "Copyright (C) 2015 Jakob Kogler, MIT License"]))

    def code_length(self):
        return len(self.code_tabs.currentWidget().toPlainText())

    @pyqtSlot()
    def update_code_length(self):
        current_tab = self.code_tabs.currentIndex()
        code_length = self.code_length()
        self.code_length_label.setText(str(code_length))
        self.code_tabs.setTabText(current_tab, 'Tab &{} ({} chars)'.format(current_tab + 1, code_length))


class TemplateDialog(QDialog, Ui_TemplateDialog):
    def __init__(self, settings):
        QDialog.__init__(self)
        self.setupUi(self)
        self.settings = settings

        template_text = self.settings.value('Template/Template', example_template)
        self.template_text_edit.setPlainText(template_text)

        # Connect signals and slots
        self.buttonBox.accepted.connect(self.accept_template)

    def accept_template(self):
        template_text = self.template_text_edit.toPlainText()
        self.settings.setValue('Template/Template', template_text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = IdeMainWindow()
    window.show()
    sys.exit(app.exec_())

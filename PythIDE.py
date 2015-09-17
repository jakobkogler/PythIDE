import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from PyQt5 import QtCore
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

        self.doc_items = self.get_docs()
        self.fill_doc_table()
        self.doc_table_widget.resizeColumnsToContents()

        self.action_run.triggered.connect(lambda: self.run_program(debug_on=False))
        self.action_debug.triggered.connect(lambda: self.run_program(debug_on=True))
        self.action_find.triggered.connect(self.find_line_edit.setFocus)
        self.find_line_edit.textChanged.connect(self.fill_doc_table)

    def run_program(self, debug_on):
        code = self.code_text_edit.toPlainText()
        input_data = self.input_text_edit.toPlainText()

        input_data += '\n'
        code = '\n'.join(code.split('\r\n'))
        pyth_process = subprocess.Popen(['/usr/bin/env', 'python3', 'pyth/pyth.py',
                                         '-cd' if debug_on else '-c', code],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)

        output, errors = pyth_process.communicate(input=bytearray(input_data, 'utf-8'))

        message = output.decode() + (errors if errors else '')
        self.output_text_edit.setPlainText(message)

    def get_docs(self):
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = IdeMainWindow()
    window.show()
    sys.exit(app.exec_())

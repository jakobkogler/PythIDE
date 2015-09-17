import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from PyQt5 import QtCore
from mainwindow import Ui_MainWindow
import subprocess


class IdeMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)

        self.action_run.triggered.connect(lambda: self.run_program(debug_on=False))
        self.action_debug.triggered.connect(lambda: self.run_program(debug_on=True))

        self.fill_doc_table()
        self.output_box.hide()

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

        if not errors:
            self.output_text_edit.setPlainText(output.decode())
            self.output_box.show()

    def fill_doc_table(self):
        with open('pyth/web-docs.txt', 'r') as f:
            docs = [line.split(' ', maxsplit=4) for line in f]

        self.doc_table_widget.setColumnCount(5)
        self.doc_table_widget.setRowCount(len(docs))

        header = ['Char', 'Arity', 'Starts', 'Mnemonic', 'Details']
        self.doc_table_widget.setHorizontalHeaderLabels(header)
        for row, items in enumerate(docs):
            for column, item in enumerate(items):
                if len(item) > 40:
                    item = self.split_sentence(item, 40)
                    print(item)
                table_widget_item = QTableWidgetItem(item)
                if column < 4:
                    table_widget_item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.doc_table_widget.setItem(row, column, table_widget_item)

        self.doc_table_widget.resizeColumnsToContents()
        for i in range(10):
            self.doc_table_widget.resizeRowToContents(i)

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = IdeMainWindow()
    window.show()
    sys.exit(app.exec_())

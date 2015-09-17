import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from mainwindow import Ui_MainWindow
import subprocess


class IdeMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)

        self.action_run.triggered.connect(self.run_program)

        self.output_box.hide()

    def run_program(self):
        code = self.code_text_edit.toPlainText()
        input_data = self.input_text_edit.toPlainText()
        debug_on = False

        input_data += '\n'
        code = '\n'.join(code.split('\r\n'))
        pyth_process = subprocess.Popen(['/usr/bin/env', 'python3', 'pyth/pyth.py',
                                         '-csd' if debug_on else '-cs', code],
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)

        output, errors = pyth_process.communicate(input=bytearray(input_data, 'utf-8'))

        if not errors:
            self.output_text_edit.setPlainText(output.decode())
            self.output_box.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = IdeMainWindow()
    window.show()
    sys.exit(app.exec_())

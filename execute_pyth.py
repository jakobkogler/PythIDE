import sys
from contextlib import redirect_stdout
import io
import traceback
from PyQt5.QtCore import QThread, pyqtSignal
sys.path.insert(0, './pyth')
from pyth import *


class OutputWriter:
        def __init__(self, text_edit_write):
            self.text_edit_write = text_edit_write

        def write(self, s):
            self.text_edit_write.emit(str(s))


class CodeExecutor(QThread):
    begin = pyqtSignal(name='start')
    text_edit_write = pyqtSignal(str, name='text_edit_write')
    finished = pyqtSignal(name='finished')

    def __init__(self, code, inp, debug_on, multi_line_on):
        QThread.__init__(self)
        self.code = code
        self.inp = inp
        self.debug_on = debug_on
        self.multi_line_on = multi_line_on

        if multi_line_on:
            self.code = preprocess_multiline(self.code)

    def run(self):
        self.begin.emit()

        output_writer = OutputWriter(self.text_edit_write)
        sys.stderr = output_writer
        with redirect_stdout(output_writer):
            if isinstance(self.inp, list):
                for input_data in self.inp:
                    self.execute_code(input_data)
                    print()
            else:
                self.execute_code(self.inp)

        sys.stdin = sys.__stdin__
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        self.finished.emit()

    def execute_code(self, input_data):
        global safe_mode
        global environment
        global c_to_i

        sys.stdin = io.StringIO(input_data)

        saved_env = c.deepcopy(environment)
        saved_c_to_i = c.deepcopy(c_to_i)

        try:
            safe_mode = False

            py_code_line = general_parse(self.code)
            if self.debug_on:
                print('{:=^50}'.format(' ' + str(len(self.code)) + ' chars '))
                print(self.code)
                print('='*50)
                print(py_code_line)
                print('='*50)

            exec(py_code_line, environment)
        except SystemExit:
            pass
        except Exception as error:
            traceback.print_exc()

        for key in saved_env:
            environment[key] = saved_env[key]
        c_to_i = saved_c_to_i

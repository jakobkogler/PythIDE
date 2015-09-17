import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from mainwindow import Ui_MainWindow


class IdeMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)

        self.output_box.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = IdeMainWindow()
    window.show()
    sys.exit(app.exec_())

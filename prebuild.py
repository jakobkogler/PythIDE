import subprocess
from PyQt5.uic import compileUi

ui_files = ['mainwindow', 'clipboard_template']
for file in ui_files:
    with open(file + '.py', 'w') as f:
        compileUi(file + '.ui', f)

try:
    version = subprocess.check_output(['git', 'describe', '--tags', '--long', '--always']).decode()
except:
    version = 'v?.?-??-??????'

with open('version.txt', 'w') as f:
    f.write(version)
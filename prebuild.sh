#!/usr/bin/env bash
pyuic5 mainwindow.ui >mainwindow.py
pyuic5 clipboard_template.ui >clipboard_template.py
git describe --tags --long --always >version.txt

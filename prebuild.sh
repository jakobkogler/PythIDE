#!/usr/bin/env bash
pyuic5 mainwindow.ui >mainwindow.py
git describe --tags --long --always >version.txt

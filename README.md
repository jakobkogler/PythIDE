# PythIDE

An IDE for the golfing language [Pyth](https://github.com/isaacg1/pyth)

![Screenshot of PythIDE](https://github.com/jakobkogler/PythIDE/blob/master/screenshot.png)

## Requirements ##

* Python 3.4
* PyQt 5.2.1

## Usage ##

First clone the project and fetch the submodule pyth: 

```
git clone https://github.com/jakobkogler/PythIDE.git
cd PythIDE
git submodule update --init 
```

Then before the first start, you have to run the script `prebuild.sh`.
It determines the version number via Git.
Afterwards you can start the the program with

```
python3 PythIDE.py
```

## Licence ##

Copyright (C) 2015 Jakob Kogler, [MIT License](https://github.com/jakobkogler/PythIDE/blob/master/LICENSE.txt)

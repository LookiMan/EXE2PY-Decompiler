# EXE2PY-Decompiler

With this program you can decompile executable files created using **pyinstaller** or **py2exe**.

It is also possible to decompile individual cache files back into the original python source code.

<hr>

*Screenshot of the main application window*

![](https://github.com/topdefaultuser/EXE2PY-Decompiler/blob/master/example/main_window.PNG)


**What's new:**

=== Jul 27, 2023 ===

- Full refactoring was performed

- Updated README.md

- Updated requirements.txt

- Add logical disabling of the checkbox 'Decompile all additional libraries' if not .exe file is selected

=== Jun 11, 2021 ===

- Completely redesigned graphical interface

- Added support for ***DRAG & DROP*** for ```LineEdit```

- Added the ability to specify a folder to decompile its contents

- Code significantly rewritten


**Fixes:**

- Fixed the problem of decompiling version 3.6 code with older versions of python

- Added the ability to interrupt the decompilation process

- Added a banner that appears during the decompilation process


**Note:**

- If you cannot decompile one of the libraries from the **EXE2PY_Pycache** folder, check the "decompile all additional libraries" checkbox and try again.

- The program can work on python versions 3.7 and older

- With its help, it is possible to decompile programs - 3.4, 3.6, 3.7. 3.8 python versions. 
At the same time, the difference in versions does not matter. (With python version 3.8, you can decompile a program written in python 3.4, 3.6, etc).


<hr>

*Screenshot of the running application*


![](https://github.com/topdefaultuser/EXE2PY-Decompiler/blob/master/example/decompiling_process.PNG)


# Upgrade pip:

`python -m pip install --upgrade pip`

# Install requirements:

`python -m pip install -r requirements.txt`

# Usage:

`python main.py`

# Validate-flake8:

`flake8 filename.py`

# Validate-pyright:

`pyright filename.py`

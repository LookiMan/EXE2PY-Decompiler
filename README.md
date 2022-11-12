# EXE2PY-Decompiler

С помощью данной программы можно декомпилировать исполняемые файлы, созданные с помощью **pyinstaller** или **py2exe**.

Также возможно декомпилировать отдельные кэш-файлы назад в исходный код python.

<hr>

*Скриншот главного окна приложения*

![](https://github.com/topdefaultuser/EXE2PY-Decompiler/blob/master/Examples/MainForm.PNG)


**Что нового**

- Полностью переработан графический интерфейс

- Добавлена поддержка ***DRAG & DROP*** для ```LineEdit```

- Добавлена возможность указывать папку для декомпиляции её содержимого

- Значительно переписан код



**Фиксы:**

- Исправлена проблема с декомпиляции кода версии 3.6 старшими версиями python

- Добавлена возможность прерывания процесса декомпиляции

- Добавлен баннер, появляющийся во время работы декомпилятора



**Примечание:**

Если не удается декомпилировать одну из библиотек с папки ```EXE2PY_Pycache``` переключите флажок «декомпилировать все дополнительные библиотеки» в активное положение и повторите попытку.

Программа может работать на версиях python 3.4, 3.6, 3.7. 
С её помощью, возможно, декомпилировать программы ранее перечисленных версий python. 
При этом различие версий не играет никакой роли. (С помощью python версии 3. 4. можно декомпилировать программу, написанную на python 3. 6.).

<hr>

*Скриншот работающего приложения*


![](https://github.com/topdefaultuser/EXE2PY-Decompiler/blob/master/Examples/Working.PNG)

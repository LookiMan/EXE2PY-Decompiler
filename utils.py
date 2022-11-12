# -*- coding: UTF-8 -*-
import os
import sys
import glob
import platform
import shutil
import time
import pyautogui


# Список заголовков для разных версий python
HEADERS = [
    b"\xee\x0c\r\n\x11;\x8d_\x93!\x00\x00",  # 3.4
    b"3\r\r\n0\x07>]a4\x00\x00",  # 3.6
    b"B\r\r\n\x00\x00\x00\x000\x07>]a4\x00\x00",  # 3.7
    b"U\r\r\n\x00\x00\x00\x000\x07>]a4\x00\x00",  # 3.8
]

# Коды возврата некоторых функций
STATUS_CODES = {
    200: "Декомпиляция исполняемого файла успешно завершена",
    201: "Декомпиляция кэш-файла успешно завершена",
    202: "Декомпиляция дополнительной библиотеки успешно завершена",
    203: "Декомпиляция кэш-файлов успешно завершена",
    204: "Декомпиляция дополнительных библиотек успешно завершена",
    400: "Передан файл с неожиданым расширением",
    401: "Процесс остановлен пользователем",
    402: "Получено непредвиденное сочетание параметров для декомпиляции",
    403: "В функцию decompile_pyc_files передан неожиданый тип данныйх",
    404: "В функцию decompile_sublibraries передан неожиданый тип данныйх",
    405: "В папке не обнаружено нужных файлов",
    500: "Возникла непредвиденная ошибка при декомпиляции исполняемого файла",
    501: "Возникла непредвиденная ошибка при декомпиляции кэш-файла",
    502: "Невозможно исправить заголовок дополнительной библиотеки",
    503: "Возникла непредвиденная ошибка при декомпиляции дополнительной библиотеки",
}


PATH_TO_LOG_DIR = os.path.join(os.path.dirname(sys.argv[0]), "Logs")
MAIN_DIR = "EXE2PY_Main"
PYCACHE_DIR = "EXE2PY_Pycache"
MODULES_DIR = "EXE2PY_Modules"
EXTRACTED_DIR = "EXE2PY_Extracted"


def _generate_pyc_header(python_version, size):
    """Выполняет роль заглушки"""
    return b""


def search_pyc_files(directory):
    return glob.glob("%s\\*.pyc" % directory)


def make_folders(folders):
    """Создание нужных директорий"""
    for folder in folders:
        if os.path.exists(folder):
            remove_folder(folder)

        create_folder(folder)


def create_folder(folder: str):
    """Создает папку"""
    try:
        os.mkdir(folder)
    except Exception as exc:
        print("[!] Error creating folder: %s" % folder)
        print("[e]", exc)


def open_output_folder(folder: str):
    """Открывает папку с декомпилированным проектом"""
    if platform.system() == "Windows":
        os.system('start "" "%s"' % folder)

    elif platform.system() == "Linux":
        os.system('xdg-open "%s"' % folder)

    elif platform.system() == "Darwin":
        os.system('open "%s"' % folder)


def remove_folder(folder: str):
    """Удаление файла"""
    try:
        shutil.rmtree(folder)
    except Exception as exc:
        print("[!] Error removing folder: %s" % folder)
        print("[e]", exc)


def make_log_file_name():
    """Создание имени для лог файла"""
    return time.ctime(time.time()).replace(" ", "-").replace(":", "-") + ".txt"


def get_screen_width():
    return pyautogui.size()[0]


def get_screen_height():
    return pyautogui.size()[1]

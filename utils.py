
import os
import glob
import webbrowser
import shutil
import pyautogui

from enum import Enum


PYTHON_HEADERS = [
    b'\xee\x0c\r\n\x11;\x8d_\x93!\x00\x00',  # 3.4
    b'3\r\r\n0\x07>]a4\x00\x00',  # 3.6
    b'B\r\r\n\x00\x00\x00\x000\x07>]a4\x00\x00',  # 3.7
    b'U\r\r\n\x00\x00\x00\x000\x07>]a4\x00\x00',  # 3.8
]

START_BYTE = b'\xe3'

# Коды возврата некоторых функций
STATUS_CODES = {
    200: 'Декомпиляция исполняемого файла успешно завершена',
    201: 'Декомпиляция кэш-файла успешно завершена',
    202: 'Декомпиляция дополнительной библиотеки успешно завершена',
    203: 'Декомпиляция кэш-файлов успешно завершена',
    204: 'Декомпиляция дополнительных библиотек успешно завершена',
    400: 'Передан файл с неожиданым расширением',
    401: 'Процесс остановлен пользователем',
    402: 'Получено непредвиденное сочетание параметров для декомпиляции',
    403: 'В функцию decompile_pyc_files передан неожиданый тип данныйх',
    404: 'В функцию decompile_sublibraries передан неожиданый тип данныйх',
    405: 'В папке не обнаружено нужных файлов',
    500: 'Возникла непредвиденная ошибка при декомпиляции исполняемого файла',
    501: 'Возникла непредвиденная ошибка при декомпиляции кэш-файла',
    502: 'Невозможно исправить заголовок дополнительной библиотеки',
    503: 'Возникла непредвиденная ошибка при декомпиляции дополнительной библиотеки',
}


class Platforms(Enum):
    WINDOWS = 'Windows'


def _generate_pyc_header(python_version, size) -> bytes:
    return b''


def search_pyc_files(directory: str) -> list:
    return glob.glob('%s\\*.pyc' % directory)


def make_folders(folders: list) -> None:
    for folder in folders:
        if os.path.exists(folder):
            remove_folder(folder)

        create_folder(folder)


def create_folder(folder: str) -> None:
    try:
        os.mkdir(folder)
    except Exception as e:
        print(f'[!] Error creating folder: {folder}')
        print(f'[e] {e}')


def open_output_folder(folder: str) -> None:
    webbrowser.open(folder)


def remove_folder(folder: str) -> None:
    try:
        shutil.rmtree(folder)
    except Exception as e:
        print(f'[!] Error removing folder: {folder}')
        print(f'[e] {e}')


def get_screen_size() -> pyautogui.Size:
    return pyautogui.size()

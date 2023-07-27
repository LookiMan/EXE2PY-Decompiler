
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


class Platforms(Enum):
    WINDOWS = 'Windows'


class StatusCodes(Enum):
    # Success codes
    EXE_DECOMPILED_SUCCESSFULLY = 200
    EXE_PARTIALLY_DECOMPILATION = 201
    PYC_DECOMPILED_SUCCESSFULLY = 202
    PYC_PARTIALLY_DECOMPILATION = 203
    LIB_DECOMPILED_SUCCESSFULLY = 204
    LIB_PARTIALLY_DECOMPILATION = 205
    # User error codes
    USER_STOPED = 400
    UNEXPECTED_CONFIGURATION = 401
    UNEXPECTED_EXTENSION = 402
    TARGET_NOT_EXISTS = 403
    FILES_NOT_FOUND = 404
    # Unknown error codes
    EXE_DECOMPILATION_ERROR = 500
    PYC_DECOMPILATION_ERROR = 501
    LIB_DECOMPILATION_ERROR = 502


# Return codes of some functions
STATUS_CODES = {
    # Success messages
    StatusCodes.EXE_DECOMPILED_SUCCESSFULLY.value: 'Decompilation of the executable has been successfully completed',
    StatusCodes.EXE_PARTIALLY_DECOMPILATION.value: 'Decompilation of the executable file partially successful',
    StatusCodes.PYC_DECOMPILED_SUCCESSFULLY.value: 'Decompilation of the cache files has been successfully completed',
    StatusCodes.PYC_PARTIALLY_DECOMPILATION.value: 'Decompilation of cache files partially successful',
    StatusCodes.LIB_DECOMPILED_SUCCESSFULLY.value: 'Decompilation of the additional libraries has been successfully completed',
    StatusCodes.LIB_PARTIALLY_DECOMPILATION.value: 'Decompilation of the additional libraries partially successful',
    # User error messages
    StatusCodes.USER_STOPED.value: 'Process stopped by user',
    StatusCodes.UNEXPECTED_CONFIGURATION.value: 'Received unexpected combination of parameters for decompilation',
    StatusCodes.UNEXPECTED_EXTENSION.value: 'A file with an unexpected extension was transferred',
    StatusCodes.TARGET_NOT_EXISTS.value: 'A selected file or directory not exists',
    StatusCodes.FILES_NOT_FOUND.value: 'No files found in the folder',
    # Unknown error messages
    StatusCodes.EXE_DECOMPILATION_ERROR.value: 'An unexpected error occurred while decompiling the executable file',
    StatusCodes.PYC_DECOMPILATION_ERROR.value: 'An unexpected error occurred while decompiling the cache file',
    StatusCodes.LIB_DECOMPILATION_ERROR.value: 'An unexpected error occurred while decompiling an additional library',
}


def search_pyc_files(directory: str) -> list:
    return glob.glob(f'{directory}\\*.pyc')


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

import sys

from argparse import ArgumentParser
from os import listdir
from os import rename
from os import path
from platform import system

from PyQt5.QtWidgets import QApplication

from config import EXTRACTED_DIR
from config import LOG_FILE
from config import LOG_LEVEL
from config import MODULES_DIR
from config import MAIN_DIR
from config import PYCACHE_DIR

from ui import show_error
from ui import MainWindow

from utils import _generate_pyc_header
from utils import make_folders
from utils import open_output_folder
from utils import search_pyc_files
from utils import START_BYTE
from utils import PYTHON_HEADERS
from utils import Platforms

import logging

logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL)
log = logging.getLogger(__name__)

import_errors = list()
try:
    from uncompyle6.bin import uncompile
except ImportError as e:
    import_errors.append(str(e))

try:
    import unpy2exe
except ImportError as e:
    import_errors.append(str(e))

try:
    import pyinstxtractor
except ImportError as e:
    import_errors.append(str(e))


class StreamBuffer:
    """Класс имитирующий sys.stdout для для перехвата данных"""

    def __init__(self) -> None:
        self.stream = None
        self.lines = list()

    def intercept_stream(self, stream) -> None:
        self.stream = stream
        sys.stdout = self

    def release_stream(self) -> None:
        sys.stdout = self.stream
        self.stream = None

    def write(self, line: str) -> None:
        self.lines.append(line)

    def flush(self) -> None:
        pass

    def dump_logs(self, filename: str) -> None:
        with open(filename, mode='w') as file:
            file.write(''.join(self.lines))
        self.lines = list()

    def is_has(self, text: str) -> bool:
        return any([line for line in self.lines if text in line])


class HeaderCorrectorMainFiles:
    """Класс для подбора заголовка для .pyc файла"""
    filename = None
    filedata = b''

    def set_file(self, filename: str) -> None:
        self.filename = filename

        with open(self.filename, mode='rb') as file:
            self.filedata = file.read()

    def is_need_correct(self) -> bool:
        with open(self.filename, mode='rb') as file:
            return file.read(1) == START_BYTE

    def correct_file(self, header: bytes) -> None:
        with open(self.filename, mode='wb') as file:
            file.write(header)
            file.write(self.filedata)


class HeaderCorrectorSubLibraries(HeaderCorrectorMainFiles):
    """Класс для коррекции заголовка кэш-файла для версий python 3.7, 3.8"""
    header = b'\x00\x00\x00\x00'

    def is_need_correct(self) -> bool:
        with open(self.filename, mode='rb') as file:
            file.seek(12)
            return file.read(1) == START_BYTE

    def correct_file(self) -> None:
        with open(self.filename, mode='wb') as file:
            file.write(self.filedata.read(12))
            file.write(self.header)
            file.write(self.filedata.read())


def decompile_pyc_file(filename: str, output_directory: str) -> int:
    corrector = HeaderCorrectorMainFiles()
    corrector.set_file(filename)

    sys.argv = ['uncompile', '-o', output_directory, filename]

    stream_buffer = StreamBuffer()
    stream_buffer.intercept_stream(sys.stdout)

    if corrector.is_need_correct():
        for header in PYTHON_HEADERS:
            corrector.correct_file(header)
            try:
                uncompile.main_bin()
            except Exception as e:
                log.exception(e)
                continue
            else:
                if stream_buffer.is_has('# Successfully decompiled file'):
                    break
    else:
        uncompile.main_bin()

    stream_buffer.release_stream()
    stream_buffer.dump_logs(path.join(output_directory, 'output.log'))

    return 201


def decompile_pyc_files(filenames: list, output_directory: str):
    for filename in filenames:
        decompile_pyc_file(filename, output_directory)
    return 203


def decompile_sublibrary(filename: str, output_directory: str):
    corrector = HeaderCorrectorSubLibraries()
    corrector.set_file(filename)

    sys.argv = ['uncompile', '-o', output_directory, filename]

    stream_buffer = StreamBuffer()
    stream_buffer.intercept_stream(sys.stdout)

    try:
        uncompile.main_bin()
    except Exception:
        """Для python версии 3.6 заголовок файла на 4 байта короче, и поэтому сначала пытаемся декомпилировать байт-код без изменений,
        в случае возникновении ошибки, в заголовок файла дописывается 4 байта, для нормальной декомпиляции кэш-файлов версий 3.7, 3.8"""
        corrector.correct_file()
        uncompile.main_bin()

    stream_buffer.release_stream()
    stream_buffer.dump_logs(path.join(output_directory, 'output.log'))
    return 202


def decompile_sublibraries(filenames: list, output_directory: str):
    for filename in filenames:
        decompile_sublibrary(filename, output_directory)
    return 204


def decompile_with_pyinstxtractor(filename: str, is_need_decompile_sub_libraries: bool):
    current_directory = path.dirname(filename)
    extract_directory = path.join(current_directory, EXTRACTED_DIR)
    modules_directory = path.join(current_directory, MODULES_DIR)
    scripts_directory = path.join(current_directory, MAIN_DIR)
    cache_directory = path.join(current_directory, PYCACHE_DIR)

    make_folders([
        extract_directory,
        modules_directory,
        cache_directory,
        scripts_directory,
    ])

    # Передача pyinstxtractor'у пути для сохранения кэша модулей
    pyinstxtractor.CACHE_DIRECTORY = cache_directory
    # Передача pyinstxtractor'у пути для сохранения содержимого .ехе файла
    pyinstxtractor.EXTRACTION_DIR = extract_directory

    if (len(sys.argv)) > 1:
        sys.argv[1] = filename
    else:
        sys.argv.append(filename)

    stream_buffer = StreamBuffer()
    stream_buffer.intercept_stream(sys.stdout)

    pyinstxtractor.main()
    # Получение списка возможных основных файлов
    files = pyinstxtractor.MAIN_FILES

    # Эти библиотеки всегда в списке основных библиотек, но не относятся к ним
    if 'pyi_rth_multiprocessing' in files:
        files.remove('pyi_rth_multiprocessing')
    if 'pyiboot01_bootstrap' in files:
        files.remove('pyiboot01_bootstrap')
    if 'pyi_rth_qt4plugins' in files:
        files.remove('pyi_rth_qt4plugins')
    if 'pyi_rth__tkinter' in files:
        files.remove('pyi_rth__tkinter')
    if 'pyi_rth_pyqt5' in files:
        files.remove('pyi_rth_pyqt5')

    main_files = [path.join(extract_directory, filename) for filename in files]

    for filename in main_files:
        rename(filename, filename + '.pyc')

    main_files = [filename + '.pyc' for filename in main_files]

    stream_buffer.release_stream()
    stream_buffer.dump_logs(path.join(scripts_directory, 'output.log'))

    decompile_pyc_files(main_files, scripts_directory)

    if is_need_decompile_sub_libraries is True:
        cache_files = [
            path.join(cache_directory, file) for file in listdir(cache_directory)
        ]

        decompile_sublibraries(cache_files, modules_directory)


def decompile_with_unpy2exe(filename: str):
    current_directory = path.dirname(filename)
    extract_directory = path.join(current_directory, EXTRACTED_DIR)
    scripts_directory = path.join(current_directory, MAIN_DIR)

    if system() == Platforms.WINDOWS:
        # В названии присутствуют запрещенные символы символы  для windows '<, >'
        unpy2exe.IGNORE.append('<boot hacks>.pyc')

    # Делаем заглушку, поскольку с заголовками от функции unpy2exe._generate_pyc_header байт-код не компилируется в чистый код
    unpy2exe._generate_pyc_header = _generate_pyc_header
    unpy2exe.unpy2exe(filename, f'{sys.version_info[:2]}.{extract_directory}')

    decompile_pyc_files(search_pyc_files(extract_directory), scripts_directory)


def decompile_python_cache_file(filename: str) -> int:
    output_directory = path.dirname(filename)

    try:
        status_code = decompile_pyc_file(filename, output_directory)
    except Exception:
        status_code = 501
    finally:
        return status_code


def decompile_python_cache_files(filenames: list) -> int:
    output_directory = path.dirname(filenames[0])

    try:
        status_code = decompile_pyc_files(filenames, output_directory)
    except Exception:
        status_code = 501
    finally:
        return status_code


def decompile_python_sublibrary(filename: str):
    output_directory = path.dirname(filename)

    try:
        status_code = decompile_sublibrary(filename, output_directory)
    except Exception as e:
        log.exception(e)
        status_code = 503
    finally:
        return status_code


def decompile_python_sublibraries(filenames: list):
    output_directory = path.dirname(filenames[0])

    try:
        status_code = decompile_sublibraries(filenames, output_directory)
    except Exception as e:
        log.exception(e)
        status_code = 503
    finally:
        return status_code


def decompile_executable(filename: str, is_need_decompile_sub_libraries: bool):
    """Главная функция для декомпиляции .exe файлов"""
    try:
        decompile_with_pyinstxtractor(filename, is_need_decompile_sub_libraries)
    except Exception:
        """Выбросит данное исключение в случае, если программа скомпилирована не с помощью pyinstaller"""
        decompile_with_unpy2exe(filename)
    except (ValueError, TypeError, ImportError, FileNotFoundError, PermissionError):
        return 500
    else:
        return 200


def start_decompile(
    filename: str,
    is_need_decompile_sub_libraries: bool,
    is_need_open_output_folder: bool,
) -> None:

    if filename.endswith('.pyc'):
        if not is_need_decompile_sub_libraries:
            status_code = decompile_python_cache_file(filename)

        if is_need_decompile_sub_libraries:
            status_code = decompile_python_sublibrary(filename)

        if is_need_open_output_folder:
            current_directory = path.dirname(filename)
            open_output_folder(current_directory)

    elif filename.endswith('.exe'):
        status_code = decompile_executable(filename, is_need_decompile_sub_libraries)

        if is_need_open_output_folder:
            current_directory = path.dirname(filename)
            scripts_directory = path.join(current_directory, MAIN_DIR)
            open_output_folder(scripts_directory)

    elif path.isdir(filename):
        filenames = search_pyc_files(filename)

        if not is_need_decompile_sub_libraries:
            status_code = decompile_python_cache_files(filenames)

        if is_need_decompile_sub_libraries:
            status_code = decompile_python_sublibraries(filenames)

        if is_need_open_output_folder:
            current_directory = path.dirname(filename)
            open_output_folder(current_directory)

    elif not filename.endswith('.exe') and not filename.endswith('.pyc'):
        status_code = 400

    else:
        status_code = 402

    return status_code


def main() -> None:
    app = QApplication(sys.argv)

    if len(import_errors) > 0:
        show_error('Критическая ошибка', '\n'.join(import_errors))

    widget = MainWindow()
    widget.worker = start_decompile

    parser = ArgumentParser()
    parser.add_argument('-t', '--target', help='File or directory to decompile')
    args = parser.parse_args()

    if args.target:
        widget.lineEdit.setText(args.target)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

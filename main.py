import sys

from argparse import ArgumentParser
from io import BytesIO
from os import listdir
from os import rename
from os import path
from platform import system
from typing import Literal

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMessageBox

from config import EXTRACTED_DIR
from config import EXTRACTING_LOG
from config import LOG_FILE
from config import LOG_LEVEL
from config import MAIN_DIR
from config import MODULES_DIR
from config import PYCACHE_DIR

from ui import MainWindow

from utils import make_folders
from utils import open_output_folder
from utils import search_pyc_files
from utils import START_BYTE
from utils import PYTHON_HEADERS
from utils import Platforms
from utils import StatusCodes

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
    """Class mimicking sys.stdout to capture data"""

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
        """ Stub """
        pass

    def dump_logs(self, filename: str) -> None:
        with open(filename, mode='a') as file:
            file.write(''.join(self.lines))
        self.lines = list()

    def is_has(self, text: str) -> bool:
        return any([line for line in self.lines if text in line])


class HeaderCorrectorMainFiles:
    """Class for picking a header for a .pyc file"""
    filename: str
    filedata: bytes

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
    """Class for cache file header correction for python versions 3.7, 3.8"""
    header: bytes = b'\x00\x00\x00\x00'
    filedata: BytesIO

    def set_file(self, filename: str) -> None:
        self.filename = filename

        with open(self.filename, mode='rb') as file:
            self.filedata = BytesIO(file.read())

    def is_need_correct(self) -> bool:
        with open(self.filename, mode='rb') as file:
            file.seek(12)
            return file.read(1) == START_BYTE

    def correct_file(self) -> None:
        with open(self.filename, mode='wb') as file:
            file.write(self.filedata.read(12))
            file.write(self.header)
            file.write(self.filedata.read())


def decompile_pyc_file(
    filename: str,
    *,
    output_directory: str
) -> Literal[
    StatusCodes.PYC_DECOMPILED_SUCCESSFULLY,
    StatusCodes.PYC_DECOMPILATION_ERROR,
]:
    is_decompiled_successfully = False
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
            except Exception:
                continue
            else:
                if stream_buffer.is_has('# Successfully decompiled file'):
                    break
    else:
        uncompile.main_bin()

    if stream_buffer.is_has('# Successfully decompiled file'):
        is_decompiled_successfully = True

    stream_buffer.release_stream()
    stream_buffer.dump_logs(path.join(output_directory, EXTRACTING_LOG))

    return StatusCodes.PYC_DECOMPILED_SUCCESSFULLY if is_decompiled_successfully else StatusCodes.PYC_DECOMPILATION_ERROR


def decompile_pyc_files(
    filenames: list,
    *,
    output_directory: str
) -> Literal[
    StatusCodes.PYC_DECOMPILED_SUCCESSFULLY,
    StatusCodes.PYC_PARTIALLY_DECOMPILATION,
]:
    is_decompiled_successfully = True

    for filename in filenames:
        status = decompile_pyc_file(
            filename,
            output_directory=output_directory,
        )

        if is_decompiled_successfully and status != StatusCodes.PYC_DECOMPILED_SUCCESSFULLY:
            is_decompiled_successfully = False

    return StatusCodes.PYC_DECOMPILED_SUCCESSFULLY if is_decompiled_successfully else StatusCodes.PYC_PARTIALLY_DECOMPILATION


def decompile_sub_library(
    filename: str,
    *,
    output_directory: str
) -> Literal[
    StatusCodes.LIB_DECOMPILED_SUCCESSFULLY,
    StatusCodes.LIB_DECOMPILATION_ERROR,
]:
    is_decompiled_successfully = False

    corrector = HeaderCorrectorSubLibraries()
    corrector.set_file(filename)

    sys.argv = ['uncompile', '-o', output_directory, filename]

    stream_buffer = StreamBuffer()
    stream_buffer.intercept_stream(sys.stdout)

    for attempt in range(1, 3):
        if attempt == 2:
            # For python version 3.6, the file header is 4 bytes shorter,
            # so we first try to decompile the bytecode without changes,
            # if an error occurs, 4 bytes are added to the file header
            # to allow normal decompilation of cache files for versions 3.7 3.8
            corrector.correct_file()
        try:
            uncompile.main_bin()
            is_decompiled_successfully = True
        except Exception:
            continue

    stream_buffer.release_stream()
    stream_buffer.dump_logs(path.join(output_directory, EXTRACTING_LOG))

    return StatusCodes.LIB_DECOMPILED_SUCCESSFULLY if is_decompiled_successfully else StatusCodes.LIB_DECOMPILATION_ERROR


def decompile_sub_libraries(
    filenames: list,
    *,
    output_directory: str
) -> Literal[
    StatusCodes.LIB_DECOMPILED_SUCCESSFULLY,
    StatusCodes.LIB_PARTIALLY_DECOMPILATION,
]:
    is_decompiled_successfully = True

    for filename in filenames:
        status = decompile_sub_library(
            filename,
            output_directory=output_directory
        )

        if is_decompiled_successfully and status != StatusCodes.PYC_DECOMPILED_SUCCESSFULLY:
            is_decompiled_successfully = False

    return StatusCodes.LIB_DECOMPILED_SUCCESSFULLY if is_decompiled_successfully else StatusCodes.LIB_PARTIALLY_DECOMPILATION


def decompile_with_pyinstxtractor(
    filename: str,
    *,
    is_need_decompile_sub_libraries: bool
) -> Literal[
    StatusCodes.PYC_DECOMPILATION_ERROR,
    StatusCodes.LIB_DECOMPILATION_ERROR,
    StatusCodes.EXE_DECOMPILED_SUCCESSFULLY,
    StatusCodes.EXE_PARTIALLY_DECOMPILATION,
]:
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

    # Passing to pyinstxtractor the path to save the module cache
    pyinstxtractor.CACHE_DIRECTORY = cache_directory
    # Passing to pyinstxtractor the path to save the contents of the .exe file
    pyinstxtractor.EXTRACTION_DIR = extract_directory

    if (len(sys.argv)) > 1:
        sys.argv[1] = filename
    else:
        sys.argv.append(filename)

    stream_buffer = StreamBuffer()
    stream_buffer.intercept_stream(sys.stdout)

    pyinstxtractor.main()
    # Getting a list of possible main files
    files = pyinstxtractor.MAIN_FILES

    # These libraries are always on the list of core libraries,
    # but are not related to them
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

    files = [path.join(extract_directory, filename) for filename in files]

    for filename in files:
        rename(filename, filename + '.pyc')

    files = [filename + '.pyc' for filename in files]

    stream_buffer.release_stream()
    stream_buffer.dump_logs(path.join(scripts_directory, EXTRACTING_LOG))

    pyc_status = None
    lib_status = None

    try:
        pyc_status = decompile_pyc_files(
            files,
            output_directory=scripts_directory
        )
    except Exception as e:
        log.exception(e)
        return StatusCodes.PYC_DECOMPILATION_ERROR

    if is_need_decompile_sub_libraries:
        cache_files = list(
            map(
                lambda file: path.join(cache_directory, file),
                listdir(cache_directory)
            )
        )

        try:
            lib_status = decompile_sub_libraries(
                cache_files,
                output_directory=modules_directory
            )
        except Exception as e:
            log.exception(e)
            return StatusCodes.LIB_DECOMPILATION_ERROR

    if pyc_status == StatusCodes.PYC_DECOMPILED_SUCCESSFULLY and lib_status == StatusCodes.LIB_DECOMPILED_SUCCESSFULLY:
        status = StatusCodes.EXE_DECOMPILED_SUCCESSFULLY
    else:
        status = StatusCodes.EXE_PARTIALLY_DECOMPILATION

    return status


def decompile_with_unpy2exe(filename: str) -> Literal[
    StatusCodes.EXE_DECOMPILED_SUCCESSFULLY,
    StatusCodes.EXE_PARTIALLY_DECOMPILATION,
]:
    current_directory = path.dirname(filename)
    extract_directory = path.join(current_directory, EXTRACTED_DIR)
    scripts_directory = path.join(current_directory, MAIN_DIR)

    if system() == Platforms.WINDOWS.value:
        # The name contains forbidden symbols symbols for windows '<', '>'
        unpy2exe.IGNORE.append('<boot hacks>.pyc')

    # Set a stub, because with the function headers
    # unpy2exe._generate_pyc_header bytecode is not compiled into source code
    unpy2exe._generate_pyc_header = lambda python_version, size: b''
    unpy2exe.unpy2exe(filename, f'{sys.version_info[:2]}.{extract_directory}')

    status = decompile_pyc_files(
        search_pyc_files(extract_directory),
        output_directory=scripts_directory,
    )

    if status == StatusCodes.PYC_DECOMPILED_SUCCESSFULLY:
        status_code = StatusCodes.EXE_DECOMPILED_SUCCESSFULLY
    else:
        status_code = StatusCodes.EXE_PARTIALLY_DECOMPILATION

    return status_code


def decompile_executable(
    filename: str,
    *,
    is_need_decompile_sub_libraries: bool
) -> Literal[
    StatusCodes.EXE_DECOMPILED_SUCCESSFULLY,
    StatusCodes.EXE_PARTIALLY_DECOMPILATION,
    StatusCodes.PYC_DECOMPILATION_ERROR,
    StatusCodes.LIB_DECOMPILATION_ERROR,
    StatusCodes.EXE_DECOMPILATION_ERROR,
]:
    try:
        return decompile_with_pyinstxtractor(
            filename,
            is_need_decompile_sub_libraries=is_need_decompile_sub_libraries,
        )
    except (ValueError, TypeError, ImportError, FileNotFoundError, PermissionError) as e:
        log.exception(e)
        return StatusCodes.EXE_DECOMPILATION_ERROR
    except Exception:
        # Raise this exception if the program is not compiled with pyinstaller
        return decompile_with_unpy2exe(filename)


def start_decompile(
    target: str,
    *,
    is_need_decompile_sub_libraries: bool,
    is_need_open_output_folder: bool,
) -> int:

    status = StatusCodes.UNEXPECTED_CONFIGURATION

    if not path.exists(target):
        status = StatusCodes.TARGET_NOT_EXISTS

    elif target.endswith('.pyc'):
        output_directory = path.dirname(target)

        status = decompile_pyc_file(
            target,
            output_directory=output_directory,
        )

        if is_need_open_output_folder:
            open_output_folder(output_directory)

    elif target.endswith('.exe'):
        status = decompile_executable(
            target,
            is_need_decompile_sub_libraries=is_need_decompile_sub_libraries
        )

        if is_need_open_output_folder:
            open_output_folder(
                path.join(path.dirname(target), MAIN_DIR)
            )

    elif path.isdir(target):
        filenames = search_pyc_files(target)
        output_directory = target

        if filenames:
            status = decompile_pyc_files(
                filenames,
                output_directory=output_directory,
            )

            if is_need_open_output_folder:
                open_output_folder(output_directory)
        else:
            status = StatusCodes.FILES_NOT_FOUND

    return status.value


def main() -> None:
    app = QApplication(sys.argv)
    widget = MainWindow(start_decompile)

    if import_errors:
        QMessageBox.critical(
            widget.form,
            'Critical error',
            '\n'.join(import_errors),
            QMessageBox.Ok,
        )

    parser = ArgumentParser()
    parser.add_argument('-t', '--target', help='File or directory to decompile')
    args = parser.parse_args()

    if args.target:
        widget.lineEdit.setText(args.target)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

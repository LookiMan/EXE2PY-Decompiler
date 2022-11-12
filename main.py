# -*- coding: UTF-8 -*-
import os
import io
import sys

from PyQt5.QtWidgets import QApplication


import_errors = list()

try:
    from uncompyle6.bin import uncompile
except Exception as exc:
    import_errors.append(exc.msg)

try:
    import unpy2exe
except Exception as exc:
    import_errors.append(exc.msg)

try:
    import pyinstxtractor
except Exception as exc:
    import_errors.append(exc.msg)

import ui
import utils


class StreamBuffer(object):
    """Класс имитирующий sys.stdout для для перехвата данных"""

    def __init__(self):
        self.stream = None
        self.data = list()

    def intercept_stream(self, stream):
        """перехват потока и подмена его собой"""
        self.stream = stream
        #
        sys.stdout = self

    def release_stream(self):
        """освобождение потока"""
        sys.stdout = self.stream

        self.stream = None

    def write(self, text):
        """Запись данных в буфер"""
        self.data.append(text)

    def flush(self):
        """Заглушка сброса буфера"""
        pass

    def write_data_to_file(self, filename):
        """Запись перехваченого потода sys.stdout в файл"""
        with open(filename, mode="a") as file:
            file.write("".join(self.data))
        #
        self.data = list()

    def is_has_string(self, string):
        """Поиск строки в списке"""
        for line in self.data:
            if string in line:
                return True


class HeaderCorrectorMainFiles(object):
    """Класс для подбора заголовка для .pyc файла"""

    def __init__(self, headers: list):
        self.headers = headers
        self.filename = None
        self.iteration = 0
        self.bytes = b""

    def set_file(self, filename):
        """Сохранение имени файла и сохранение содержимого данного файла"""
        self.filename = filename

        fp = open(self.filename, mode="rb")
        self.bytes = fp.read()
        fp.close()

        self.iteration = 0

    def get_range_iterations(self):
        """Формирует диапазон с количеством возможных итераций"""
        return range(len(self.headers))

    def is_need_correct(self):
        """Проверка первого байта файла"""
        with open(self.filename, mode="rb") as file:
            first_byte = file.read(1)
            if first_byte == b"\xe3":
                return True
            return False

    def correct_file(self):
        """Дописывает заголок в начало файла"""
        with open(self.filename, mode="wb") as file:
            file.write(self.headers[self.iteration])
            file.write(self.bytes)

        self.iteration += 1


class HeaderCorrectorSubLibraries(object):
    """Класс для коррекции заголовка кэш-файла для версий python 3.7, 3.8"""

    def __init__(self):
        self.filename = None
        self.correct_bytes = b"\x00\x00\x00\x00"

    def set_file(self, filename):
        """Сохранение имени файла"""
        self.filename = filename

    def is_need_correct(self):
        """Проверка позиции контрольного байта"""
        with open(self.filename, mode="rb") as file:
            file.seek(12)
            if file.read(1) == b"\xe3":
                return True
            return False

    def correct_file(self):
        """Дописывает 4 нулевых байта в заголовок файла"""

        fp = open(self.filename, mode="rb")
        #
        data = io.BytesIO(fp.read())

        fp.close()

        with open(self.filename, mode="wb") as file:
            file.write(data.read(12))
            file.write(self.correct_bytes)
            file.write(data.read())


def decompile_pyc_file(filename: str, output_directory: str):
    """Расшифровка .pyc в скрипт .py"""

    # Заголовки кэш-файлов для разных версий python
    headers = utils.HEADERS
    corrector = HeaderCorrectorMainFiles(headers)
    corrector.set_file(filename)

    sys.argv = ["uncompile", "-o", output_directory, filename]

    stream_buffer = StreamBuffer()
    # Перехват потока sys.sdtout
    stream_buffer.intercept_stream(sys.stdout)

    if corrector.is_need_correct():
        for _ in corrector.get_range_iterations():
            corrector.correct_file()
            try:
                uncompile.main_bin()
            except:
                continue
            else:
                if stream_buffer.is_has_string("# Successfully decompiled file"):
                    break

    uncompile.main_bin()

    stream_buffer.release_stream()
    stream_buffer.write_data_to_file(
        os.path.join(utils.PATH_TO_LOG_DIR, utils.make_log_file_name())
    )

    return 201


def decompile_pyc_files(filenames: list, output_directory: str):
    """Декомпиляция списка кэш-файлов python"""
    if isinstance(filenames, list):
        for filename in filenames:
            decompile_pyc_file(filename, output_directory)

        return 203

    else:
        return 403


def decompile_sublibrarie(filename: str, output_directory: str):
    """Заголовки кэш-файлов библиотек для разных версий python"""
    corrector = HeaderCorrectorSubLibraries()
    corrector.set_file(filename)

    sys.argv = ["uncompile", "-o", output_directory, filename]

    stream_buffer = StreamBuffer()
    # Перехват потока sys.sdtout
    stream_buffer.intercept_stream(sys.stdout)

    try:
        uncompile.main_bin()
    except Exception:
        """Для python версии 3.6 заголовок файла на 4 байта короче, и поэтому сначала пытаемся декомпилировать байт-код без изменений,
        в случае возникновении ошибки, в заголовок файла дописывается 4 байта, для нормальной декомпиляции кэш-файлов версий 3.7, 3.8"""
        corrector.correct_file()
        uncompile.main_bin()

    finally:
        stream_buffer.release_stream()
        stream_buffer.write_data_to_file(
            os.path.join(utils.PATH_TO_LOG_DIR, utils.make_log_file_name())
        )

        return 202


def decompile_sublibraries(filenames: list, output_directory: str):
    """Декомпиляция под библиотек python"""
    if isinstance(filenames, list):
        for filename in filenames:
            decompile_sublibrarie(filename, output_directory)

        return 204

    else:
        return 404


def decompile_with_pyinstxtractor(filename: str, is_need_decompile_sub_libraries: bool):
    """Декомпиляция исполняемого приложения с помощью pyinstxtractor"""
    # Получение текущей директории
    current_directory = os.path.dirname(filename)
    # Папка для сохранения содержимого .ехе файла
    extract_directory = os.path.join(current_directory, utils.EXTRACTED_DIR)
    # Папка для байт-кода подключаемых модулей
    cache_directory = os.path.join(current_directory, utils.PYCACHE_DIR)
    # Папка для декомпилированных модулей
    modules_directory = os.path.join(current_directory, utils.MODULES_DIR)
    # Папка для основных скриптов программы
    scripts_directory = os.path.join(current_directory, utils.MAIN_DIR)
    # Создание нужных папок для распаковки программы
    utils.make_folders(
        [extract_directory, modules_directory, cache_directory, scripts_directory]
    )
    # Передача pyinstxtractor'у пути для сохранения кэша модулей
    pyinstxtractor.CACHE_DIRECTORY = cache_directory
    # Передача pyinstxtractor'у пути для сохранения содержимого .ехе файла
    pyinstxtractor.EXTRACTION_DIR = extract_directory

    if (len(sys.argv)) > 1:
        sys.argv[1] = filename
    else:
        sys.argv.append(filename)

    stream_buffer = StreamBuffer()
    # Перехват потока sys.sdtout
    stream_buffer.intercept_stream(sys.stdout)

    pyinstxtractor.main()
    # Получение списка возможных основных файлов
    files = pyinstxtractor.MAIN_FILES

    # Эти библиотеки всегда в списке основных библиотек, но не относятся к ним
    if "pyi_rth_multiprocessing" in files:
        files.remove("pyi_rth_multiprocessing")
    if "pyiboot01_bootstrap" in files:
        files.remove("pyiboot01_bootstrap")
    if "pyi_rth_qt4plugins" in files:
        files.remove("pyi_rth_qt4plugins")
    if "pyi_rth__tkinter" in files:
        files.remove("pyi_rth__tkinter")
    if "pyi_rth_pyqt5" in files:
        files.remove("pyi_rth_pyqt5")

    main_files = [os.path.join(extract_directory, filename) for filename in files]

    for filename in main_files:
        os.rename(filename, filename + ".pyc")
    # Добавление расширения к именам файлов
    main_files = [filename + ".pyc" for filename in main_files]

    stream_buffer.release_stream()
    stream_buffer.write_data_to_file(
        os.path.join(utils.PATH_TO_LOG_DIR, utils.make_log_file_name())
    )

    decompile_pyc_files(main_files, scripts_directory)

    if is_need_decompile_sub_libraries is True:
        cache_files = [
            os.path.join(cache_directory, file) for file in os.listdir(cache_directory)
        ]

        decompile_sublibraries(cache_files, modules_directory)


def decompile_with_unpy2exe(filename: str):
    """Декомпиляция исполняемого приложения с помощью unpy2exe"""
    # Получение текущей директории
    current_directory = os.path.dirname(filename)
    # Папка для сохранения содержимого .ехе файла
    extract_directory = os.path.join(current_directory, utils.EXTRACTED_DIR)
    # Папка для основных скриптов программы
    scripts_directory = os.path.join(current_directory, utils.MAIN_DIR)

    if utils.platform.system() == "Windows":
        # В названии присутствуют запрещенные символы символы  для windows '<, >'
        unpy2exe.IGNORE.append("<boot hacks>.pyc")
        # Делаем заглушку, поскольку с заголовками от функции unpy2exe._generate_pyc_header
        # байт-код не компилируется в чистый код
        unpy2exe._generate_pyc_header = utils._generate_pyc_header

    unpy2exe.unpy2exe(filename, "%s.%s" % sys.version_info[:2], extract_directory)
    # Поиск всех .pyc файлов в папке с распакованным содержимым .exe файла для
    # дальнейшей их декомпиляции в исходный код python
    main_files = utils.search_pyc_files(extract_directory)

    decompile_pyc_files(main_files, scripts_directory)


def decompile_python_cache_file(filename: str):
    """Главная функция для декомпиляции .pyc файлов"""
    output_directory = os.path.dirname(filename)

    try:
        status_code = decompile_pyc_file(filename, output_directory)
    except Exception:
        status_code = 501
    finally:
        return status_code


def decompile_python_cache_files(filenames: list):
    """Главная функция для декомпиляции .pyc файлов"""
    if len(filenames) == 0:
        return 405

    output_directory = os.path.dirname(filenames[0])

    try:
        status_code = decompile_pyc_files(filenames, output_directory)
    except Exception:
        status_code = 501
    finally:
        return status_code


def decompile_python_sublibrarie(filename: str):
    """Главная функция для декомпиляции дополнительной библиотеки"""
    output_directory = os.path.dirname(filename)

    try:
        status_code = decompile_sublibrarie(filename, output_directory)
    except Exception as exc:
        status_code = 503
    finally:
        return status_code


def decompile_python_sublibraries(filenames: list):
    """Главная функция для декомпиляции списка дополнительных библиотек"""
    if len(filenames) == 0:
        return 405

    output_directory = os.path.dirname(filenames[0])

    try:
        status_code = decompile_sublibraries(filenames, output_directory)
    except Exception:
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
):
    """Начало декомпиляции"""

    if filename.endswith(".pyc"):
        if is_need_decompile_sub_libraries is False:
            status_code = decompile_python_cache_file(filename)

        if is_need_decompile_sub_libraries is True:
            status_code = decompile_python_sublibrarie(filename)

        if is_need_open_output_folder is True:
            current_directory = os.path.dirname(filename)
            utils.open_output_folder(current_directory)

    elif filename.endswith(".exe"):
        status_code = decompile_executable(filename, is_need_decompile_sub_libraries)

        if is_need_open_output_folder is True:
            current_directory = os.path.dirname(filename)
            # Папка для основных скриптов программы
            scripts_directory = os.path.join(current_directory, utils.MAIN_DIR)
            utils.open_output_folder(scripts_directory)

    elif os.path.isdir(filename):
        filenames = utils.search_pyc_files(filename)

        if is_need_decompile_sub_libraries is False:
            status_code = decompile_python_cache_files(filenames)

        if is_need_decompile_sub_libraries is True:
            status_code = decompile_python_sublibraries(filenames)

        if is_need_open_output_folder is True:
            current_directory = os.path.dirname(filename)
            utils.open_output_folder(current_directory)

    elif not filename.endswith(".exe") and not filename.endswith(".pyc"):
        status_code = 400

    else:
        status_code = 402

    return status_code


def main():
    app = QApplication(sys.argv)

    if len(import_errors) > 0:
        message = "\n".join(import_errors)

        ui.show_error("Критическая ошибка", message)

    if not os.path.exists(utils.PATH_TO_LOG_DIR):
        utils.create_folder(utils.PATH_TO_LOG_DIR)

    widget = ui.MainWindow()
    widget.worker = start_decompile

    if len(sys.argv) == 2:
        widget.lineEdit.setText(sys.argv[1])

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

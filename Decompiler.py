# -*- coding: UTF-8 -*-
from os.path     import exists, join, basename, dirname, isdir, isfile, splitext, split
from os          import system, listdir, mkdir, rename
from progressbar import ProgresBar
from uuid        import uuid4
import sys
import io
import re
import shutil
import struct
import imp
import time

print('[>] Starting...')

errors = []

root = dirname(sys.argv[0])

try:
	from colorama import Fore, init
except ImportError:
	errors.append("Не найден модуль 'colorama'! \nУстановите модуль коммандой pip install colorama ")
except Exception as e:
	errors.append(e)

try:
	from uncompyle6.bin import uncompile
except ImportError:
	errors.append("Не найден модуль 'uncompyle6'! \nУстановите модуль коммандой pip install uncompyle6 ")
except Exception as e:
	errors.append(e)

try:
	import unpy2exe
except ImportError:
	errors.append("Не найден модуль 'unpy2exe'! \nУстановите модуль коммандой pip install unpy2exe")
except Exception as e:
	errors.append(e)

try:
	import extractor
except ImportError:
	errors.append("Не найден модуль 'extractor'!")
except Exception as e:
	errors.append(e)

if len(errors) > 0:
	for e in errors:
		print(e)
	exit(1)

else:
	print(Fore.GREEN + '[>] Decompiler 1.0: Started successfully!')

init(autoreset=True)

# Если этот параметр True программа автоматически декомпилирует все .pyc родключаймие библиотеки 
auto_lib_decompiling = None
lock_open_directory = False

def reset():
	global auto_lib_decompiling, lock_open_directory
	global current_directory, extract_directory, cache_directory, scripts_directory, main_files

	current_directory = extract_directory = cache_directory = scripts_directory = main_files = ''
	auto_lib_decompiling = None
	lock_open_directory = False

class Text_buffer(object):
	def __init__(self, output_stream):
		global sys
		self.buffer = []
		self.output = output_stream
		sys.stdout = self

	def write(self, text):
		self.buffer.append('\n' + str(text))

	def flush(self):
		pass

	def close(self, flag_print=False):
		global sys
		if flag_print == True:
			for value in self.buffer:
				self.output.write(value)
		sys.stdout = self.output

# Открывает папку с дэкомпилированым проектом
def open_directory(path):
	try:
		system('start %s' %  path)
		print(Fore.YELLOW + '[>] Opening folder...')
	except FileNotFoundError:
		print(Fore.RED + 'Could not find folder!')

# Создает папку для сохранения скриптов
def create_directory(*paths):
	# Проверка существует ли папка таким именем
	if exists(paths[0]):
		try:
			shutil.rmtree(paths[0])
		except:
			print(Fore.RED + '[!] Error removing folder: %s' % paths[0])
	for path in paths:
		if not exists(path[0]):
			try:
				mkdir(path)
			except:
				print(Fore.RED + '[!] Error creating folder: %s' % path)

# Корекция магического числа в бинарном файле
def magic_corection(files, scripts_directory):
	print(Fore.YELLOW + '\n[>] starting magic corection')
	temp_data = b''
	errors = []

	def __timestamp():
	    """Generate timestamp data for pyc header."""
	    today = time.time()
	    ret = struct.pack(b'=L', int(today))
	    return ret

	def __source_size(size):
	    """Generate source code size data for pyc header."""
	    ret = struct.pack(b'=L', int(size))
	    return ret

	def __current_magic():
	    """Current Python magic number."""
	    return imp.get_magic()

	def __build_magic(magic):
		"""Build Python magic number for pyc header."""
		return struct.pack(b'Hcc', magic, b'\r', b'\n')

	def __generate_pyc_header(python_version, size):
	    if python_version is None:
	        version = __current_magic()
	        version_tuple = sys.version_info
	    else:
	        version = PYTHON_MAGIC_WORDS.get(python_version[:3], __current_magic())
	        version_tuple = tuple(map(int, python_version.split('.')))

	    header = version + __timestamp()
	    if version_tuple[0] == 3 and version_tuple[1] >= 3:
	        # source code size was added to pyc header since Python 3.3
	        header += __source_size(size)
	    return header

	magic = {
	    # version magic numbers (see Python/Lib/importlib/_bootstrap_external.py)
	    '1.5': __build_magic(20121),
	    '1.6': __build_magic(50428),
	    '2.0': __build_magic(50823),
	    '2.1': __build_magic(60202),
	    '2.2': __build_magic(60717),
	    '2.3': __build_magic(62011),
	    '2.4': __build_magic(62061),
	    '2.5': __build_magic(62131),
	    '2.6': __build_magic(62161),
	    '2.7': __build_magic(62191),
	    '3.0': __build_magic(3000),
	    '3.1': __build_magic(3141),
	    '3.2': __build_magic(3160),
	    '3.3': __build_magic(3190),
	    '3.4': __build_magic(3250),
	    '3.5': __build_magic(3350),
	    '3.6': __build_magic(3360),
	    '3.7': __build_magic(3390),
	}

	for file in files:
		if not file.endswith('.pyc'):
			file += '.pyc'
		try:
			with open(join(scripts_directory, file), mode='rb') as f:
				temp_data = f.read()	
		except Exception as e:
			errors.append('[%s] - %s' % ( join(scripts_directory, file), e) )

		pyc_header = __generate_pyc_header(None, len(temp_data))

		try:
			with open(join(scripts_directory, file), mode='wb') as f:
				f.write(pyc_header)
				f.write(temp_data)
		except Exception as e:
			errors.append('[%s] - %s' % ( join(scripts_directory, file), e) )

	if len(errors) > 0:
		for e in errors:
			print(Fore.RED + e)
	else:
		print(Fore.GREEN + '[!] magic corection completed successfully!')
	return 1

# Расшифровка .pyc в скрипт .py
def pyc_decode(file_list, files_directory, output_directory=None):
	print(Fore.YELLOW + '[>] starting cache decoding')
	errors = []
	console = None

	if output_directory == None:
		output_directory = files_directory

	# Инициализируем прогрессбар
	progress  = ProgresBar(len(file_list), 40)

	# Запуск декомпиляции .pyc файлов .py
	for n, file in enumerate(file_list):

		if not file.endswith('.pyc'):
			file += '.pyc'

		sys.argv = ['uncompyle6', '-o', output_directory, join(files_directory, file)]

		try:
			Text_buffer(sys.stdout)
			uncompile.main_bin()	

		except Exception as e:
			Text_buffer(sys.stderr)
			errors.append('[%s] - %s' % ( file, e) )
			sys.stderr.close()
			raise Exception

		finally:
			sys.stdout.close()
			progress.call()

	if len(errors) > 0:
		for e in errors:
			print(Fore.RED + e)
	else:
		print(Fore.GREEN + '[>] decoding completed successfully!')

# Декомпиляция модулей с .pyc в .py
def cache_decompiler(modules_list, files_directory, output_directory=None, opendir=True):
	if modules_list is None:
		modules_list = listdir(files_directory)
	try:
		# Запуск декомпиляции главных скриптов
		pyc_decode(modules_list, files_directory, output_directory)
	except:
		# Коректировка числа 'magic'
		if magic_corection(modules_list, files_directory):
			# Запуск декомпиляции главных скриптов
			try:
				pyc_decode(modules_list, files_directory, output_directory)	
			except:
				print(Fore.RED + '\n[!] The script is running in a different python version than the one used to build the executable!')
				open_directory(output_directory)
		else:
			print(Fore.RED + '[!] An error occurred while modifying files!')

	if opendir is True and lock_open_directory is False:
		# Открытие папки из декомпилироваными скриптами
		open_directory(output_directory)

# Основная функция программы
# Сначала выполняется функция unpack потом decode
# flag определяет режим декомпиляции .ехе или .рус файлов
def main(flag):
	global current_directory, extract_directory, cache_directory, scripts_directory, main_files

	# Получение имени папки проекта
	file_name = re.findall(r'\\\w+\.[\.\w\d-]*$', sys.argv[1] )
	project_folder =  'Decompiled_' + file_name[0].split('.', 1)[0].replace('\\', '') +'_'+ str(uuid4())[:5]
	print(Fore.YELLOW + '[>] Project folder name: %s' % project_folder)

	# Получение текущей директории
	current_directory = join(root, project_folder)
	
	# Папка в которой будет содержимое ехе файла
	extract_directory = join(current_directory, 'Extracted')

	# Если установлен флаг ехе начнется распаковка приложения
	if flag == '.exe':
		# Папка в которой будет хранится байт-код подключаймых модулей
		cache_directory   = join(current_directory, 'Pycache')

		# Объявление папки для сохранения скриптов используймых модулей
		modules_directory = join(current_directory,'Modules')

		# Объявление папки для сохранения основных скриптов программы
		scripts_directory = join(current_directory, 'Main')

		# Создание папок
		create_directory(current_directory, extract_directory, modules_directory, cache_directory, scripts_directory)

		# Передача extractor'у пути для сохранения кеша модулей 
		extractor.set_cache_path(cache_directory)

		# Передача extractor'у пути для сохранения содержимого ехе файла
		extractor.set_extra_path(extract_directory)

		# Запуск декомпиляции проекта с помощью модуля extractor
		try:
			extractor.main()

			# Получениие списка возможних файлов 
			main_files = extractor.get_main_files()

			for f in main_files:
				rename(join(extract_directory, f), join(extract_directory, f + '.pyc'))

			# Декомпиляция файлов в скрипт
			cache_decompiler(main_files, extract_directory, scripts_directory)

			# Спрашивает нужно ли компилоровать все .pyc файлы 
			while True and auto_lib_decompiling is None:
				answer = input('[?] Decompile all pycache files? (y/n): ').lower()
				if answer == 'y':
					# Декомпиляция файлов в скрипт
					cache_decompiler(None, cache_directory, modules_directory)
					break
				if answer == 'n':
					break
		except:
			try:
				print(Fore.YELLOW + '[>] Beginning extraction with py2exe!')
				unpy2exe.unpy2exe(sys.argv[1], '%s.%s' % sys.version_info[0:2], extract_directory)
				print(Fore.GREEN + '[>] decoding completed successfully!')
				# Декомпиляция файлов в скрипт
				cache_decompiler(None, extract_directory, scripts_directory)
			except Exception as e: #Обычно возникает когда файл не той же версии что и питон!
				print(Fore.RED + '[!] %s' % e)
				print(Fore.RED + '[!] The program can not decompile the file!')
				open_directory(extract_directory)

	# Если установлен флаг 'pyc' начнется распаковка файлов кэша
	if flag == '.pyc':
		# Создание папки для сохранения основных скриптов программы
		create_directory(current_directory)

		# Получение файла для декеширования
		file = [sys.argv[1]]

		# Декомпиляция файлов в скрипты
		cache_decompiler(file, current_directory, current_directory)

# Ввод пути к файлам или папке
def entry_directory(path=None):
	while True:
		global auto_lib_decompiling, lock_open_directory
		if path is None:
			print(Fore.CYAN + '[>] Введите путь к файлу или папке:')
			path = input('[<] ').split(' ')
		if '--y' in path:
			path.remove('--y') 
			auto_lib_decompiling = True 
		if '--n' in path:
			path.remove('--n')  
			auto_lib_decompiling = False
		if '--h' in path:
			path.remove('--h')  
			lock_open_directory = True	
		if 'exit' in path:
			return []
		if len(path) == 1:
			path = path[0]
			if isdir(path):
				files = []
				directory = splitext(path)[0]
				for f in listdir(path):
					if isdir(join(directory,f)) is not True:
						if splitext(f)[1] in ('.pyc', '.exe'):
							files.append(directory + '\\' + f)	
				return [sys.argv[0]] + files

			elif exists(path):
				return [sys.argv[0]] + [path]
			else:
				print(Fore.RED + '[!] wrong way: ' + path)
		else:
			if type(path) is not list:
				path = [path]
			return [sys.argv[0]] + path


# Сюда передается список файлов, которые будут декомпилированы по очереди
def decompiler(argv):
	for num, arg in enumerate(argv[1:]):
		# Если файл существует передает аргумент в системный поток для дальнейшей работы
		#! Не удалять вторую проверку, будет ошибка на строке 264
		if exists(arg) and isdir(arg) is not True:
			flag = splitext(arg)[1]
			sys.argv = [argv[0]] + [arg]
			if num > 0:
				print(Fore.YELLOW + '[ ]')
			print(Fore.YELLOW + '[!] Step %i of %i' % (num + 1, len(argv)-1) )
			print(Fore.YELLOW + '[>] Starting decompilation...')
			main(flag)
		else:
			print(Fore.RED + '[!] Enter the correct list!')
	reset()

# Вызов справки
def help():
	command_list = [
	'Список комманд:',
	'exit      - завершает выполнение программы', 
	'help      - печатает подказку',
	'decompile - разпаковувает исполняймый файл',
	'',
	'Краткое описание:',
	'Для запуска декомпиляции после комманды \'decompile\' требуется ввести путь к файлам или папке.',
	'- Если ввести много вайлов программа декомпилирует их по очереди. ',
	'- ' + Fore.RED + 'Важно' + Fore.YELLOW + ', после декомпиляции основных скриптов прораммы нужно будет дать ответ нужно ли декомпилировать библиотеки,',
	'- или передать флажок --y/--n после директории программы.',
	'- Также если установить флажок --h после декомпиляции файлов директории с ними НЕ будут открыватся автоматически.',
	'- Если ввести путь к папке, программа попытается декомпилировать все \'.exe\' или \'.pyc\' файлы.',
	'Пример:',
	Fore.CYAN + '[>] Введите комманду:',
	Fore.WHITE + '[<] decompile или --d',
	Fore.CYAN + '[>] Введите путь к файлу или папке:',
	Fore.WHITE + '[<] C:\\...\\filename.exe --n --h' + Fore.MAGENTA + ' #Запуск декомпиляции \'filename.exe\' без декомпиляции библиотек \'--n\' ',
	Fore.MAGENTA + '\tи открытия конечной папки со скриптами \'--h\' ',
	'Или можно сделать так:',
	Fore.CYAN + '[>] Введите комманду:',
	Fore.WHITE + '[<] --d C:\\...\\filename.exe --n --h' + Fore.MAGENTA + ' #Комманда одной строкой',
	'Если вместо пути к файлу написать \'exit\' программа выйдет в основной цикл.']

	for line in command_list:
		print(Fore.YELLOW + '[i] ' + line )


if __name__ == '__main__':

	if len(sys.argv) >= 2:	
		decompiler(entry_directory(sys.argv[1:]))

	while True:
		print(Fore.CYAN + '[>] Введите комманду:')

		command = input('[<] ').lower().strip().split()

		if 'help' in command:
			help()
		elif 'exit' in command:
			exit()
		elif 'decompile' in command or '--d' in command:
			command.remove(command[0])
			for val in command:
				if exists(val) or isdir(val) is True:
					decompiler(entry_directory(command))
					break
			else:
				decompiler(entry_directory())

		else:
			print(Fore.RED+'[!] Не удалось распознать комманду \'%s\' !' % ' '.join(command))

	#python E:\Python\Decompiler\Decompiler.py E:\Python\Decompiler\f.exe E:\Python\Decompiler\progressbar.exe --n --h
	#python E:\Python\Decompiler\Decompiler.py E:\Python\Decompiler\progressbar.exe
	#python E:\Python\Decompiler\Decompiler.py E:\Python\Decompiler\dist\progressbar.exe
	#python E:\Python\Decompiler\Decompiler.py E:\Python\Decompiler\Instainspector.exe
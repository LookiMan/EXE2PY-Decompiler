# -*- coding: UTF-8 -*-
'''
Установка дополнительных библиотек:
pip install unpy2exe
pip install uncompyle6

Принцип работы скрипта:
В поле для ввода указываете путь к файлу .exe (скомпилированным с помощью pyinstaller или py2exe) или к байт-коду (.pyc) 
С помощью pyinstxtractor извлекается содержимое файла
После чего с помощью библиотеки uncompyle6 извлеченные файлы c расширением .pyc компилируются в код

Особенности работы скрипта:
Можно дэкомпилировать байт-код версий python 3.4, 3.6, 3.7 скомпилированы
'''

from tkinter import (Tk, StringVar, IntVar, Label, Button, Checkbutton)
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import (showinfo, showwarning, showerror)

import threading
import platform
import os
import sys
import time
import glob
import shutil

try:
	import keyboard
except Exception as exc:
	showerror(exc.msg)

try:
	from uncompyle6.bin import uncompile
except Exception as exc:
	showerror(exc.msg)

try:
	import unpy2exe
except Exception as exc:
	showerror(exc.msg)

try:
	import pyinstxtractor
except Exception as exc:
	showerror(exc.msg)

from popup_menu import EntryContextMenuWrapper



bg = '#0FA75F'
font_style = 'Verdana 11'
version = int('%i%i' % (sys.version_info[0], sys.version_info[1])) # формат версии 34, 36, 37, 38

root = Tk()
root.geometry('675x95')
root.title('Decompiller 2.0')
root.configure(bg=bg)
root.resizable(width=False, height=False)

file_variable = StringVar()
is_decompile_sublibraries = IntVar()

# 
def Thread(my_funk):
	def wrapper(*args, **kwargs):
		my_thread = threading.Thread(target=my_funk, daemon=True, args=args, kwargs=kwargs)
		my_thread.start()
	return wrapper

# Класс имитирующий sys.stdout для для перехвата данных 
class Buffer:
	def __init__(self):
		self._stream = None
		self._data = []


	def set_stream(self, stream):
		self._stream = stream


	def get_stream(self):
		return self._stream


	def write(self, text):
		self._data.append(text)


	def flush(self):
		pass


	def is_has_string(self, string):
		for line in self._data:
			if(string in line):
				return True

# Класс для коррекции заголовка .pyc файла 
class File_corrector:
	def __init__(self, headers):
		self._headers = [header for header in headers.values()]
		self._filename = None
		self._iter = 0


	def set_file(self, filename):
		self._filename = filename
		self._file_handler = open(self._filename, mode='rb')
		self._bytes = self._file_handler.read()
		self._file_handler.close()
		self._iter = 0


	def is_need_correct(self):
		with open(self._filename, mode='rb') as file:
			byte = file.read(1)
			if(byte == b'\xe3'):
				return True
			return False		


	def correct_file(self):
		with open(self._filename, mode='wb') as file:
			file.write(self._headers[self._iter])
			file.write(self._bytes)
		self._iter += 1


	def write_header(self, header):
		with open(self._filename, mode='wb') as file:
			file.write(header)
			file.write(self._bytes)

# Выполняет роль заглушки
def _generate_pyc_header(python_version, size):
	return b''

# Добавление гарячих клавиш полю для ввода
def add_hot_keys(element):
	keyboard.add_hotkey('ctrl+c', element.copy_selection)
	keyboard.add_hotkey('ctrl+x', element.cut_selection)
	keyboard.add_hotkey('ctrl+a', element.select_all)
	keyboard.add_hotkey('ctrl+v', element.paste_from_clipboard)
	keyboard.add_hotkey('ctrl+d', element.clearn)

# Диалог выбора файла
def select_file(variable: object):
	root.wm_attributes('-topmost', 1)
	if(platform.system() == "Darwin"):
		file_path = askopenfilename(parent=root)
	else:
		file_path = askopenfilename(parent=root, filetypes=[('All files', '*')])

	file_path = file_path.replace('/', '\\')
	
	if(file_path != ''):
		variable.set(file_path)

# Открывает папку с дэкомпилированым проектом
def open_output_folder(folder: str):
	if platform.system() == 'Windows':
		os.system('start "" "%s"' % folder)
	elif platform.system() == 'Linux':
		os.system('xdg-open "%s"' % folder)
	elif platform.system() == 'Darwin':
		os.system('open "%s"' % folder)

#
def remove_folder(folder: str):
	try:
		shutil.rmtree(folder)
	except:
		print('[!] Error removing folder: %s' % folder)

# Создает папку для сохранения скриптов
def create_folder(folder: str):
	try:
		os.mkdir(folder)
	except:
		print('[!] Error creating folder: %s' % folder)

# Расшифровка .pyc в скрипт .py
def pyc_decompile(filenames: list, output_directory: str, version: int=None):
	# Список заголовков для разных версий python
	headers = {
		34: b'\xee\x0c\r\n\x11;\x8d_\x93!\x00\x00',
		36: b'3\r\r\n0\x07>]a4\x00\x00',
		37: b'B\r\r\n\x00\x00\x00\x000\x07>]a4\x00\x00',
		38: b'U\r\r\n\x00\x00\x00\x000\x07>]a4\x00\x00',
	}
	
	step_size = 100 / len(filenames)
	header = headers.get(version)
	fc = File_corrector(headers)
	bf = Buffer()

	for i, filename in enumerate(filenames, 1):
		sys.argv = ['uncompile', '-o', output_directory, filename]

		root.title('Дэкомпиляция файла: %s (%i/%i)' % (filename, i, len(filenames)))
		fc.set_file(filename)
		if(fc.is_need_correct()):
			if(version):
				fc.write_header(header)
			else:
				bf.set_stream(sys.stdout)
				sys.stdout = bf
				for i in range(4):
					fc.correct_file()
					try:
						uncompile.main_bin()
					except:
						continue
					if(bf.is_has_string('# Successfully decompiled file')):
						sys.stdout = bf.get_stream()
						bf.close()
						break

		uncompile.main_bin()
		time.sleep(0.1)

# 
def test():
	filename = file_variable.get()
	if(not os.path.exists(filename)):
		return showwarning('Внимание', 'Неверно указан путь к файлу')
	elif(len(threading.enumerate()) > 3):
		return showwarning('Внимание', 'Идет процес дэкомпиляции')
	else:
		main()

# 
@Thread
def main():
	# Получение имени папки проэкта
	filename = file_variable.get()
	path, extention = os.path.splitext(filename)
	# Получение текущей директории
	current_directory = os.path.dirname(filename)
	# Папка в которой будет содержимое .ехе файла
	extract_directory = os.path.join(current_directory, 'Extracted')

	if(extention == '.pyc'):
		# Декомпиляция файлов в скрипты
		pyc_decompile([filename], path + '.py') 
		open_output_folder(current_directory)

	# Если установлен флаг ехе начнется распаковка приложения
	if(extention == '.exe'):
		# Папка в которой будет хранится байт-код подключаймых модулей
		cache_directory   = os.path.join(current_directory, 'Pycache')
		# Объявление папки для сохранения скриптов используймых модулей
		modules_directory = os.path.join(current_directory,'Modules')
		# Объявление папки для сохранения основных скриптов программы
		scripts_directory = os.path.join(current_directory, 'Main')
		
		# Создание папок
		for folder in (extract_directory, modules_directory, cache_directory, scripts_directory):
			
			if(os.path.exists(folder)):
				remove_folder(folder)

			create_folder(folder)

		# Передача pyinstxtractor'у пути для сохранения кэша модулей 
		pyinstxtractor.set_cache_path(cache_directory)
		# Передача pyinstxtractor'у пути для сохранения содержимого ехе файла
		pyinstxtractor.set_extra_path(extract_directory)
		# Запуск декомпиляции проекта с помощью модуля pyinstxtractor или unpy2exe
		try:
			if(len(sys.argv)) > 1:
				sys.argv[1] = filename
			else:
				sys.argv.append(filename)

			pyinstxtractor.main()
			# Получение списка возможных основных файлов
			files = pyinstxtractor.get_main_files()
			# Получение версии python в формате 34, 36, 37, 38
			pyver = pyinstxtractor.get_pyver()
			
			# Эти библиотеки всегда в списке основных библиотек, но не относятся к ним
			if('pyi_rth_multiprocessing' in files):
				files.remove('pyi_rth_multiprocessing')
			if('pyiboot01_bootstrap' in files):
				files.remove('pyiboot01_bootstrap')
			if('pyi_rth_qt4plugins' in files):
				files.remove('pyi_rth_qt4plugins')

			main_files = [os.path.join(extract_directory, filename) for filename in files]

			for filename in main_files:
				os.rename(filename, filename + '.pyc')
			# Добавление расширения к именам файлов
			main_files = [filename + '.pyc' for filename in main_files]

			# Декомпиляция файлов в скрипт
			pyc_decompile(main_files, scripts_directory, pyver)

			if(is_decompile_sublibraries.get() == 1):
				cache_files = [os.path.join(cache_directory, file) for file in os.listdir(cache_directory)]
				pyc_decompile(cache_files, modules_directory, pyver)
				open_output_folder(modules_directory)

		except:
			# По крайней мере у меня на винде не работает
			if(platform.system() == 'Windows'):
				# В названии присутствуют запрещенные символы '<>'
				unpy2exe.IGNORE.append('<boot hacks>.pyc')
				# Делаем заглушку, поскольку с заголовками от функции unpy2exe._generate_pyc_header 
				# байт-код не компилируется в чистый код
				unpy2exe._generate_pyc_header = _generate_pyc_header
			
			unpy2exe.unpy2exe(filename, '%s.%s' % sys.version_info[:2], extract_directory)
			main_files = glob.glob('%s\\*.pyc' % extract_directory)
			# Декомпиляция файлов в скрипт
			pyc_decompile(main_files, scripts_directory)

		finally:
			time.sleep(3)
			showinfo('Успех', 'Дэкомпиляция закончена')
			root.title('Decompiller 2.0')
			open_output_folder(scripts_directory)

# 
def ui():
	Label(root, text='Введите путь к дэкомпилируемой программе или скрипту', bg=bg, font=font_style).place(x=7, y=10)
	edit = EntryContextMenuWrapper(root=root, textvariable=file_variable, bd=0, font='Verdana 10', width=54)
	edit.place(x=10, y=35, width=630, height=20)
	add_hot_keys(edit)
	Button(root, text='...', bg='white', bd=0, font=font_style, command=lambda: select_file(file_var)).place(x=641, y=35, height=20)

	Checkbutton(root, text='Дэкомпилировать все дополнительные библиотеки', 
		variable=is_decompile_sublibraries, 
		onvalue=1, 
		offvalue=0, 
		bg=bg, 
		font=font_style).place(x=5, y=55)

	Button(root, text='Дэкомпилировать', bg='white', bd=0, font=font_style, command=test).place(x=520, y=60, height=20)

	if(len(sys.argv) > 1):
		file_variable.set(sys.argv[1])

	root.mainloop()

# 
if __name__ == '__main__':
	ui()

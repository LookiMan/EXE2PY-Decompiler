from tkinter import (Menu, Entry)
from tkinter import (END, SEL, SEL_FIRST, SEL_LAST, INSERT, TclError)

# 
class PopupMenu:
	def __init__(self, widget_class, *args, **kwargs):
		if kwargs.get('root'):
			self.__root = kwargs.pop('root') # НЕЛЬЗЯ НАЗЫВАТЬ self._root

		widget_class.__init__(self, *args, **kwargs)
		self.popup_menu = self.init_menu()
		self.bind('<3>', self.show_context_menu)

	def init_menu(self):
		menu = Menu(self.__root, tearoff=False)
		menu.add_command(label='Вырезать', command=self.cut_selection)
		menu.add_command(label='Копировать', command=self.copy_selection)
		menu.add_command(label='Вставить', command=self.paste_from_clipboard)
		menu.add_command(label='Удалить', command=self.delete_selection)
		menu.add_separator()
		menu.add_command(label='Выделить все', command=self.select_all)
		menu.add_command(label='Очистить поле', command=self.clearn)	
		return menu

	def copy_selection(self):
		try:
			selection_text = self.selection_get()
		except TclError:
			pass
		else:
			self.__root.clipboard_clear()
			self.__root.clipboard_append(selection_text)

	def delete_selection(self):
		try:
			self.delete('sel.first', 'sel.last')
		except TclError:
			pass

	def cut_selection(self):
		self.copy_selection()
		self.delete_selection()

	def paste_from_clipboard(self):
		try:
			clipboard_text = self.__root.clipboard_get()
		except TclError:
			pass
		else:
			self.delete_selection()
			self.insert(INSERT, clipboard_text)

	def select_all(self):
		try:
			self.tag_add(SEL, '1.0', END)
			self.mark_set(INSERT, '1.0')
			self.see(INSERT)
		except:
			self.select_range(0, END)

	def show_context_menu(self, event):
		pos_x = self.winfo_rootx() + event.x
		pos_y = self.winfo_rooty() + event.y
		self.popup_menu.tk_popup(pos_x, pos_y)

	def clearn(self):
		try:
			self.delete(0, END)
		except:
			self.delete('1.0', END)

#! При иницыализации экземпляра класса родительськое окно обизательно указывать c ключем root 
class EntryContextMenuWrapper(Entry, PopupMenu):
	def __init__(self, *args, **kwargs):
		PopupMenu.__init__(self, Entry, *args, **kwargs)

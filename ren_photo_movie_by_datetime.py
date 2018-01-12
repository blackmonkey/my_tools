# -*- coding: utf-8 -*-

import functools, os
from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import askopenfilename, askdirectory
import tkinter.messagebox as tmsgbox

PAD = 2.5

class ConfigPanel(Frame):
	def __init__(self, parent):
		super(ConfigPanel, self).__init__(parent)
		self._exif_path = StringVar(value = os.getcwd())
		self._photo_path = StringVar(value = os.getcwd())

		Label(self, text = 'ExifTool: ').grid(column = 0, row = 0, sticky = E, padx = PAD, pady = PAD)
		Label(self, text = 'Photo & Movie Folder: ').grid(column = 0, row = 1, sticky = E, padx = PAD, pady = PAD)
		Entry(self, textvariable = self._exif_path).grid(column = 1, row = 0, sticky = NSEW, padx = PAD, pady = PAD)
		Entry(self, textvariable = self._photo_path).grid(column = 1, row = 1, sticky = NSEW, padx = PAD, pady = PAD)
		Button(self, text = 'Browse ...', command = self._choose_exif).grid(column = 2, row = 0, sticky = NSEW, padx = PAD, pady = PAD)
		Button(self, text = 'Browse ...', command = self._choose_photo).grid(column = 2, row = 1, sticky = NSEW, padx = PAD, pady = PAD)

		self.grid_columnconfigure(1, weight = 1)

	def _choose_exif(self):
		fpath = self._exif_path.get()
		if not os.path.isdir(fpath):
			fpath = os.path.split(fpath)[0]
		fname = askopenfilename(initialdir = fpath)
		self._exif_path.set(fname.replace('/', os.sep))

	def _choose_photo(self):
		fpath = self._photo_path.get()
		if not os.path.isdir(fpath):
			fpath = os.path.split(fpath)[0]
		fname = askdirectory(initialdir = fpath)
		self._photo_path.set(fname.replace('/', os.sep))

	def get_exif_path(self):
		return self._exif_path.get()

	def get_photo_path(self):
		return self._photo_path.get()

EXT_BUTTON_WIDTH = 120

def cmp_ext_button(first_btn, second_btn):
	first_label = first_btn.cget('text')
	second_label = second_btn.cget('text')
	if len(first_label) != len(second_label):
		return len(first_label) - len(second_label)
	elif first_label == second_label:
		return 0
	elif first_label < second_label:
		return -1
	else:
		return 1

class FilterPanel(Frame):
	def __init__(self, parent, scan_fun, preview_fun, rename_run):
		super(FilterPanel, self).__init__(parent)

		self._filters_panel = LabelFrame(self, labelanchor = NW, labelwidget = Label(text = 'Found file extensions:'))
		self._filters_panel.grid(column = 0, row = 0, rowspan = 2, sticky = NSEW, padx = PAD, pady = PAD)
		self._filters_panel.bind('<Configure>', self._on_filter_panel_configure)

		Button(self, text = 'Scan', command = scan_fun).grid(column = 2, row = 0, columnspan = 2, sticky = NSEW, padx = PAD, pady = PAD)
		Button(self, text = 'Preview', command = preview_fun).grid(column = 2, row = 1, sticky = NSEW, padx = PAD, pady = PAD)
		Button(self, text = 'Rename', command = rename_run).grid(column = 3, row = 1, sticky = NSEW, padx = PAD, pady = PAD)

		self.grid_columnconfigure(0, weight = 1)

		self._filters = {}

	def show_extensions(self, ext_infos):
		for child in self._filters_panel.winfo_children():
			child.forget()
			child.destroy()
		self._filters.clear()

		for ext, count, chosen in ext_infos:
			self._filters[ext] = (count, BooleanVar(value = chosen))
			Checkbutton(self._filters_panel, text ='%s (%d)' % (ext, count), variable = self._filters[ext][1]).grid(column = 0, row = 0, sticky = NSEW, padx = PAD, pady = PAD)
			# TODO: find longest ext and calculate maximum item width by it.
		self._on_filter_panel_configure(None)

	def _on_filter_panel_configure(self, event):
		panel_width = self._filters_panel.winfo_width()
		c = r = btns_width = 0
		buttons = self._filters_panel.grid_slaves()
		buttons.sort(key=functools.cmp_to_key(cmp_ext_button))
		for btn in buttons:
			ginfo = btn.grid_info()
			if ginfo['column'] != c or ginfo['row'] != r:
				btn.grid_forget()
				btn.grid(column = c, row = r, sticky = NSEW, padx = PAD, pady = PAD)
			btns_width += EXT_BUTTON_WIDTH
			if btns_width >= panel_width:
				c = btns_width = 0
				r += 1
			else:
				c += 1

class RenameApp(Frame):
	def __init__(self):
		root = Tk()
		root.title('Rename Photo & Movie by Datetime - v3.0')
		root.state('zoomed')

		super(RenameApp, self).__init__(root)

		self._createWidgets()
		self.grid_columnconfigure(0, weight = 1)
		self.grid_rowconfigure(4, weight = 1)
		self.pack(fill = BOTH, expand = True)

		root.mainloop()

	def _createWidgets(self):
		self._config_panel = ConfigPanel(self)
		self._filter_panel = FilterPanel(self, self._scan_photos, self._preview_renaming, self._do_rename)

		self._config_panel.grid(column = 0, row = 0, sticky = NSEW, padx = PAD, pady = PAD)
		Separator(self).grid(column = 0, row = 1, sticky = NSEW, padx = PAD)
		self._filter_panel.grid(column = 0, row = 2, sticky = NSEW, padx = PAD, pady = PAD)
		Separator(self).grid(column = 0, row = 3, sticky = NSEW, padx = PAD)

		Label(self, text = 'TODO : found files and folders').grid(column = 0, row = 4, sticky = NSEW, padx = PAD, pady = PAD)

	def _scan_photos(self):
		ext_infos = []
		for i in range(20):
			ext_infos.append(('.jpg' + str(i), i * 10000, i % 2 == 0))
		self._filter_panel.show_extensions(ext_infos)

	def _preview_renaming(self):
		pass

	def _do_rename(self):
		pass

if __name__ == "__main__":
	RenameApp()

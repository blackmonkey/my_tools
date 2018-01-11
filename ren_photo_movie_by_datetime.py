# -*- coding: utf-8 -*-

import os
from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import askopenfilename, askdirectory
import tkinter.messagebox as tmsgbox

PAD = 2.5

class LabelButton(Label):
	def __init__(self, master, title = 'LabelButton', callback = None):
		super(LabelButton, self).__init__(master, text = title, relief = RAISED)
		self._callback = callback
		self.bind('<ButtonPress-1>', lambda event: event.widget.config(relief = SUNKEN))
		self.bind('<ButtonRelease-1>', lambda event: self._onBtnRelease1(event))

	def _onBtnRelease1(self, event):
		event.widget.config(relief = RAISED)
		if self._callback is not None:
			self._callback()

class ConfigPanel(Frame):
	def __init__(self, parent):
		super(ConfigPanel, self).__init__(parent)
		self._exif_path = StringVar(value = os.getcwd())
		self._photo_path = StringVar(value = os.getcwd())

		Label(self, text = 'ExifTool : ').grid(column = 0, row = 0, sticky = E, padx = PAD, pady = PAD)
		Label(self, text = 'Photo & Movie Folder : ').grid(column = 0, row = 1, sticky = E, padx = PAD, pady = PAD)
		Entry(self, textvariable = self._exif_path).grid(column = 1, row = 0, sticky = NSEW, padx = PAD, pady = PAD)
		Entry(self, textvariable = self._photo_path).grid(column = 1, row = 1, sticky = NSEW, padx = PAD, pady = PAD)
		Button(self, text = 'Browse ...', command = self.choose_exif).grid(column = 2, row = 0, sticky = NSEW, padx = PAD, pady = PAD)
		Button(self, text = 'Browse ...', command = self.choose_photo).grid(column = 2, row = 1, sticky = NSEW, padx = PAD, pady = PAD)

		self.grid_columnconfigure(1, weight = 1)
		self.pack(fill = BOTH, expand = True)

	def choose_exif(self):
		fpath = self._exif_path.get()
		if not os.path.isdir(fpath):
			fpath = os.path.split(fpath)[0]
		fname = askopenfilename(initialdir = fpath)
		self._exif_path.set(fname.replace('/', os.sep))

	def choose_photo(self):
		fpath = self._photo_path.get()
		if not os.path.isdir(fpath):
			fpath = os.path.split(fpath)[0]
		fname = askdirectory(initialdir = fpath)
		self._photo_path.set(fname.replace('/', os.sep))

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
		ConfigPanel(self).grid(column = 0, row = 0, sticky = NSEW, padx = PAD, pady = PAD)
		Separator(self).grid(column = 0, row = 1, sticky = NSEW)
		Label(self, text = 'TODO : file exts filters').grid(column = 0, row = 2, sticky = NSEW, padx = PAD, pady = PAD)
		Separator(self).grid(column = 0, row = 3, sticky = NSEW)
		Label(self, text = 'TODO : found files and folders').grid(column = 0, row = 4, sticky = NSEW, padx = PAD, pady = PAD)

if __name__ == "__main__":
	RenameApp()

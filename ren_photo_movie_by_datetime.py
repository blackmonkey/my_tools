# -*- coding: utf-8 -*-

import functools, os
from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import askopenfilename, askdirectory
from pprint import pprint
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

		for ext, count in ext_infos:
			self._filters[ext] = (count, BooleanVar(value = True))
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

SUPPORTED_SUFFIX = [
	'.3fr', '.3g2', '.3gp', '.3gp2', '.3gpp',
	'.aa', '.aax', '.acfm', '.acr', '.afm', '.aif', '.aifc', '.aiff', '.amfm', '.ape', '.arw', '.asf', '.avi',
	'.bmp', '.bpg', '.btf',
	'.ciff', '.cr2', '.crw', '.cs1',
	'.dc3', '.dcm', '.dcp', '.dcr', '.dfont', '.dib', '.dic', '.dicm', '.divx', '.djv', '.djvu', '.dng', '.dpx', '.dr4', '.ds2', '.dss', '.dv', '.dvb',
	'.eip', '.eps', '.epsf', '.erf', '.exif', '.exr', '.exv',
	'.f4a', '.f4b', '.f4p', '.f4v', '.fff', '.flac', '.flif', '.flv', '.fpf', '.fpx',
	'.gif', '.gpr',
	'.hdp', '.hdr', '.heic', '.heif',
	'.icc', '.icm', '.iiq', '.iso', '.itc',
	'.j2c', '.j2k', '.jng', '.jp2', '.jpc', '.jpe', '.jpeg', '.jpf', '.jpg', '.jpm', '.jpx', '.jxr',
	'.k25', '.kdc',
	'.la', '.lfp', '.lfr',
	'.m2t', '.m2ts', '.m2v', '.m4a', '.m4b', '.m4p', '.m4v', '.mef', '.mie', '.mif', '.miff', '.mka', '.mks', '.mkv', '.mng', '.modd', '.moi', '.mos', '.mov', '.mp3', '.mp4', '.mpc', '.mpeg', '.mpg', '.mpo', '.mqv', '.mrw', '.mts', '.mxf',
	'.nef', '.nrw',
	'.ofr', '.ogg', '.ogv', '.opus', '.orf', '.otf',
	'.pac', '.pbm', '.pcd', '.pct', '.pdb', '.pef', '.pfa', '.pfb', '.pfm', '.pgf', '.pgm', '.pict', '.plist', '.pmp', '.png', '.ppm', '.prc', '.ps', '.psb', '.psd', '.psdt', '.psp', '.pspimage',
	'.qif', '.qt', '.qti', '.qtif',
	'.r3d', '.ra', '.raf', '.ram', '.raw', '.riff', '.rm', '.rw2', '.rwl', '.rwz',
	'.seq', '.sr2', '.srf', '.srw', '.svg', '.swf',
	'.thm', '.tif', '.tiff', '.ts', '.ttc', '.ttf',
	'.vob', '.vrd', '.vsd',
	'.wav', '.wdp', '.webm', '.webp', '.wma', '.wmv', '.wv',
	'.x3f', '.xcf',
]

class RenameApp(Frame):
	def __init__(self):
		self._found_files = {}

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
		photo_folder = self._config_panel.get_photo_path()
		if not photo_folder:
			tmsgbox.showwarning('Oops', 'Please specify the photo folder at first!')
			return

		self._found_files.clear()
		found_count = 0
		for root, dirs, files in os.walk(photo_folder):
			for name in files:
				_base, ext = os.path.splitext(name)
				ext = ext.lower()
				if ext in SUPPORTED_SUFFIX:
					fname = os.path.join(root, name)
					if ext not in self._found_files:
						self._found_files[ext] = []
					self._found_files[ext].append((name, fname))
					found_count += 1

		ext_infos = []
		for ext in self._found_files.keys():
			ext_infos.append((ext, len(self._found_files[ext])))
		self._filter_panel.show_extensions(ext_infos)

		tmsgbox.showinfo('Done', 'Finished scaning photos, found %d files' % (found_count))

	def _preview_renaming(self):
		pass

	def _do_rename(self):
		pass

if __name__ == "__main__":
	RenameApp()

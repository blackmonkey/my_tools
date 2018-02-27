# -*- coding: utf-8 -*-
import codecs, functools, os, webbrowser
from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import askopenfilename, askdirectory
from idlelib.tooltip import ToolTip
from pprint import pprint
import tkinter.messagebox as tmsgbox

PAD = 2.5
EXIF_CMD = 'exiftool.exe'

class ConfigPanel(Frame):
	def __init__(self, parent):
		super(ConfigPanel, self).__init__(parent)
		self._exif_path = StringVar()
		self._photo_path = StringVar(value = os.getcwd())

		exif_label = Label(self, text = 'ExifTool: ', foreground = 'blue', cursor = 'hand2')
		exif_label.grid(column = 0, row = 0, sticky = E, padx = PAD, pady = PAD)
		exif_label.bind('<Button-1>', lambda evt: webbrowser.open_new(r'https://sno.phy.queensu.ca/~phil/exiftool/'), True)
		ToolTip(exif_label, r'   Download it from https://sno.phy.queensu.ca/~phil/exiftool/   ')
		Label(self, text = 'Photo & Movie Folder: ').grid(column = 0, row = 1, sticky = E, padx = PAD, pady = PAD)
		Entry(self, textvariable = self._exif_path).grid(column = 1, row = 0, sticky = NSEW, padx = PAD, pady = PAD)
		Entry(self, textvariable = self._photo_path).grid(column = 1, row = 1, sticky = NSEW, padx = PAD, pady = PAD)
		Button(self, text = 'Browse ...', command = self._choose_exif).grid(column = 2, row = 0, sticky = NSEW, padx = PAD, pady = PAD)
		Button(self, text = 'Browse ...', command = self._choose_photo).grid(column = 2, row = 1, sticky = NSEW, padx = PAD, pady = PAD)

		self.grid_columnconfigure(1, weight = 1)

		exif_path = os.path.join(os.getcwd(), EXIF_CMD)
		if os.path.isfile(exif_path):
			self._exif_path.set(exif_path)

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
	def __init__(self, parent, scan_fun, preview_fun, rename_run, callback):
		super(FilterPanel, self).__init__(parent)

		self._checkbutton_changed_callback = callback

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
			var = BooleanVar(value = True)
			chk_btn = Checkbutton(self._filters_panel, text ='%s (%d)' % (ext, count), variable = var, command = lambda ext = ext, var = var: self._checkbutton_changed_callback(ext, var.get()))
			chk_btn.grid(column = 0, row = 0, sticky = NSEW, padx = PAD, pady = PAD)
			self._filters[ext] = (count, var, chk_btn)
			# TODO: find longest ext and calculate maximum item width by it.
		self._on_filter_panel_configure()

	def _on_filter_panel_configure(self, event = None):
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

	def update_ext_selection(self, ext, state):
		if ext in self._filters:
			count, var, btn = self._filters[ext]
			if state == '':
				btn.state(['alternate'])
			else:
				btn.state(['!alternate'])
				var.set(state)

COL_SELECTED = '#0'
COL_NAME = 'Name'
COL_RENAME = 'Rename'
COL_TYPE = 'Type'
COL_FOLDER = 'Path'
COL_SELECTED_TITLE = 'Selected'
COL_NAME_TITLE = COL_NAME
COL_RENAME_TITLE = COL_RENAME
COL_TYPE_TITLE = COL_TYPE
COL_FOLDER_TITLE = COL_FOLDER

MARK_SELECTED = '☑'
MARK_UNSELECTED = '☐'

TAG_SELECTED = 'selected'
TAG_UNSELECTED = 'unselected'

class PreviewPanel(Frame):
	def __init__(self, parent, callback):
		super(PreviewPanel, self).__init__(parent)

		self._item_clicked_callback = callback

		self._tree_view = Treeview(self, columns = (COL_NAME, COL_RENAME, COL_TYPE, COL_FOLDER))
		self._tree_view.tag_configure(TAG_SELECTED, foreground = 'black')
		self._tree_view.tag_configure(TAG_UNSELECTED, foreground = 'lightgray')
		self._tree_view.column(COL_SELECTED, width = 60, stretch = False)
		self._tree_view.column(COL_NAME, width = 200, stretch = False, anchor = W)
		self._tree_view.column(COL_RENAME, width = 200, stretch = False, anchor = W)
		self._tree_view.column(COL_TYPE, width = 50, stretch = False, anchor = W)
		self._tree_view.column(COL_FOLDER, width = 800, stretch = False, anchor = W)
		self._init_column_headers()

		vbar = Scrollbar(self, orient = VERTICAL, command = self._tree_view.yview)
		self._tree_view.configure(yscrollcommand = vbar.set)

		self._tree_view.grid(row = 0, column = 0, sticky = NSEW)
		vbar.grid(row = 0, column = 1, sticky = NS)

		self.grid_columnconfigure(0, weight = 1)
		self.grid_rowconfigure(0, weight = 1)

		self._tree_view.bind('<Button-1>', self._treeview_on_clicked, True)

	def _init_column_headers(self):
		self._tree_view.heading(COL_SELECTED, text = COL_SELECTED_TITLE, command = lambda: self._treeview_sort_column(COL_SELECTED, False))
		self._tree_view.heading(COL_NAME, text = COL_NAME_TITLE, anchor = W, command = lambda: self._treeview_sort_column(COL_NAME, False))
		self._tree_view.heading(COL_RENAME, text = COL_RENAME_TITLE, anchor = W, command = lambda: self._treeview_sort_column(COL_RENAME, False))
		self._tree_view.heading(COL_TYPE, text = COL_TYPE_TITLE, anchor = W, command = lambda: self._treeview_sort_column(COL_TYPE, False))
		self._tree_view.heading(COL_FOLDER, text = COL_FOLDER_TITLE, anchor = W, command = lambda: self._treeview_sort_column(COL_FOLDER, False))

	def show_found_files(self, files):
		# reset all column headers
		self._init_column_headers()

		self._tree_view.delete(*self._tree_view.get_children())

		for ext in files.keys():
			for root, name, new_name in files[ext]:
				self._tree_view.insert('', 'end', text = MARK_SELECTED, values = [name, new_name, ext, root], tags = [TAG_SELECTED])

	def _treeview_on_clicked(self, event):
		x, y, widget = event.x, event.y, event.widget
		col = self._tree_view.identify_column(x)
		row = self._tree_view.identify_row(y) # if row is empty, then the column header is clicked.
		if col == COL_SELECTED and row: # if clicked on the first column and on the list item.
			item = self._tree_view.identify_row(y)
			unselected = self._tree_view.tag_has(TAG_UNSELECTED, item)
			if unselected:
				self._select_file(item)
			else:
				self._unselect_file(item)

			if self._item_clicked_callback:
				self._item_clicked_callback(unselected, self._tree_view.item(item, option = 'values'))

	def _treeview_sort_column(self, col, reverse):
		# get all the cell values on the specific column
		if col == COL_SELECTED:
			l = [(self._tree_view.tag_has(TAG_SELECTED, k), k) for k in self._tree_view.get_children()]
		else:
			l = [(self._tree_view.set(k, col), k) for k in self._tree_view.get_children()]

		# sort the cell values
		l.sort(reverse = reverse)

		# rearrange items in sorted positions
		for index, (val, k) in enumerate(l):
			self._tree_view.move(k, '', index)

		# reset all column headers
		self._init_column_headers()

		# get new column header label
		col_label = ''
		if col == COL_SELECTED:
			col_label = COL_SELECTED_TITLE
		elif col == COL_NAME:
			col_label = COL_NAME_TITLE
		elif col == COL_RENAME:
			col_label = COL_RENAME_TITLE
		elif col == COL_TYPE:
			col_label = COL_TYPE_TITLE
		elif col == COL_FOLDER:
			col_label = COL_FOLDER_TITLE

		col_label += ' ↓' if reverse else ' ↑'

		# reverse sort next time
		self._tree_view.heading(col, text = col_label, command = lambda col = col, reverse = reverse: self._treeview_sort_column(col, not reverse))

	def _select_file(self, row_id):
		self._tree_view.item(row_id, text = MARK_SELECTED, tags = [TAG_SELECTED])

	def _unselect_file(self, row_id):
		self._tree_view.item(row_id, text = MARK_UNSELECTED, tags = [TAG_UNSELECTED])

	def select_files(self, files):
		for k in self._tree_view.get_children():
			name, new_name, ext, root = self._tree_view.item(k, option = 'values')
			if (root, name, new_name) in files:
				self._select_file(k)

	def unselect_files(self, files):
		for k in self._tree_view.get_children():
			name, new_name, ext, root = self._tree_view.item(k, option = 'values')
			if (root, name, new_name) in files:
				self._unselect_file(k)

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

FOUND_FILES = 'files.txt'

class RenameApp(Frame):
	def __init__(self):
		root = Tk()
		root.title('Rename Photo & Movie by Datetime - v3.0')
		root.state('zoomed')

		super(RenameApp, self).__init__(root)

		self._selected_files = {}
		self._unselected_files = {}
		self._status_msg = StringVar(value = 'ready.')

		self._createWidgets()
		self.grid_columnconfigure(0, weight = 1)
		self.grid_rowconfigure(4, weight = 1)
		self.pack(fill = BOTH, expand = True)

		root.mainloop()

		# try:
		# 	os.remove(FOUND_FILES)
		# except OSError:
		# 	pass

	def _createWidgets(self):
		self._config_panel = ConfigPanel(self)
		self._filter_panel = FilterPanel(self, self._scan_photos, self._preview_renaming, self._do_rename, self._on_ext_selected)
		self._preview_panel = PreviewPanel(self, self._on_file_selected)
		self._status_bar = Label(self, textvariable = self._status_msg, borderwidth = 1, relief = 'solid')

		self._config_panel.grid(column = 0, row = 0, sticky = NSEW, padx = PAD, pady = PAD)
		Separator(self).grid(column = 0, row = 1, sticky = NSEW, padx = PAD)
		self._filter_panel.grid(column = 0, row = 2, sticky = NSEW, padx = PAD, pady = PAD)
		Separator(self).grid(column = 0, row = 3, sticky = NSEW, padx = PAD)
		self._preview_panel.grid(column = 0, row = 4, sticky = NSEW, padx = PAD, pady = PAD)
		self._status_bar.grid(column = 0, row = 5, sticky = NSEW, padx = PAD, pady = PAD)

	def _scan_photos(self):
		exif_path = self._config_panel.get_exif_path()
		if not exif_path or not os.path.isfile(exif_path):
			tmsgbox.showwarning('Oops', 'Please specify exif tool at first!')
			return

		photo_folder = self._config_panel.get_photo_path()
		if not photo_folder:
			tmsgbox.showwarning('Oops', 'Please specify the photo folder at first!')
			return

		self._selected_files.clear()
		self._unselected_files.clear()
		full_paths = []
		found_count = 0
		for root, dirs, files in os.walk(photo_folder):
			self._status_msg.set('scanning ' + root)
			for name in files:
				_base, ext = os.path.splitext(name)
				ext = ext.lower()
				if ext in SUPPORTED_SUFFIX:
					full_paths.append(os.path.join(root, name) + '\n')
					if ext not in self._selected_files:
						self._selected_files[ext] = []
						self._unselected_files[ext] = []
					self._selected_files[ext].append((root, name, ''))
					found_count += 1

		fp = codecs.open(FOUND_FILES, 'w')
		fp.writelines(full_paths)
		fp.close()

		ext_infos = []
		for ext in self._selected_files.keys():
			ext_infos.append((ext, len(self._selected_files[ext])))
		self._filter_panel.show_extensions(ext_infos)

		self._preview_panel.show_found_files(self._selected_files)

		self._status_msg.set('Done, found %d files!' % (found_count))

	def _on_file_selected(self, selected, values):
		name, new_name, ext, root = values
		item = (root, name, new_name)
		if selected and ext in self._unselected_files and item in self._unselected_files[ext]:
			self._unselected_files[ext].remove(item)
			if item not in self._selected_files[ext]:
				self._selected_files[ext].append(item)
		elif not selected and ext in self._selected_files and item in self._selected_files[ext]:
			self._selected_files[ext].remove(item)
			if item not in self._unselected_files[ext]:
				self._unselected_files[ext].append(item)

		if len(self._selected_files[ext]) == 0:
			self._filter_panel.update_ext_selection(ext, False)
		elif len(self._unselected_files[ext]) == 0:
			self._filter_panel.update_ext_selection(ext, True)
		else:
			self._filter_panel.update_ext_selection(ext, '')

	def _on_ext_selected(self, ext, selected):
		if selected and ext in self._unselected_files:
			self._preview_panel.select_files(self._unselected_files[ext])
			self._selected_files[ext].extend(self._unselected_files[ext])
			self._unselected_files[ext].clear()
		elif not selected and ext in self._selected_files:
			self._preview_panel.unselect_files(self._selected_files[ext])
			self._unselected_files[ext].extend(self._selected_files[ext])
			self._selected_files[ext].clear()

	def _preview_renaming(self):
		pass

	def _do_rename(self):
		pass

if __name__ == '__main__':
	RenameApp()

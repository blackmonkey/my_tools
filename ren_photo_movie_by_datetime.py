# -*- coding: utf-8 -*-
import codecs, functools, os, re, subprocess, threading, webbrowser
from datetime import datetime
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

	def show_extensions(self, files):
		for child in self._filters_panel.winfo_children():
			child.forget()
			child.destroy()

		ext_infos = {}
		exts = []
		for finfo in files:
			ext = finfo.ext()
			if ext not in ext_infos:
				ext_infos[ext] = [0, 0]
				exts.append(ext)
			if finfo.selected():
				ext_infos[ext][0] += 1
			else:
				ext_infos[ext][1] += 1

		exts.sort()
		for ext in exts:
			var = BooleanVar(value = True)
			count = sum(ext_infos[ext])
			chk_btn = Checkbutton(self._filters_panel, text ='%s (%d)' % (ext, count), variable = var, command = lambda ext = ext, var = var: self._checkbutton_changed_callback(ext, var.get()))
			chk_btn.grid(column = 0, row = 0, sticky = NSEW, padx = PAD, pady = PAD)

			chk_btn.state(['alternate'])
			if ext_infos[ext][0] == 0: # no selected files
				chk_btn.state(['!alternate'])
				var.set(False)
			elif ext_infos[ext][1] == 0: # no unselected files
				chk_btn.state(['!alternate'])
				var.set(True)

		# TODO: find longest ext and calculate maximum item width by it.
		self._on_filter_panel_configure()

	def _on_filter_panel_configure(self, event = None):
		panel_width = self._filters_panel.winfo_width()
		c = r = btns_width = 0
		buttons = self._filters_panel.grid_slaves()
		buttons.sort(key = functools.cmp_to_key(cmp_ext_button))
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

	def disable(self):
		for child in self.winfo_children():
			if isinstance(child, Button):
				child.config(state = DISABLED)
			elif isinstance(child, LabelFrame):
				for childd in child.winfo_children():
					if isinstance(childd, Checkbutton):
						childd.config(state = DISABLED)

	def enable(self):
		for child in self.winfo_children():
			if isinstance(child, Button):
				child.config(state = NORMAL)
			elif isinstance(child, LabelFrame):
				for childd in child.winfo_children():
					if isinstance(childd, Checkbutton):
						childd.config(state = NORMAL)

COL_SELECTED = '#0'
COL_NAME = '#1'
COL_RENAME = '#2'
COL_TYPE = '#3'
COL_FOLDER = '#4'
COL_SELECTED_TITLE = 'Selected'
COL_NAME_TITLE = 'Name'
COL_RENAME_TITLE = 'Rename'
COL_TYPE_TITLE = 'Type'
COL_FOLDER_TITLE = 'Path'

MARK_SELECTED = '☑'
MARK_UNSELECTED = '☐'

TAG_SELECTED = 'selected'
TAG_UNSELECTED = 'unselected'

class PreviewPanel(Frame):
	def __init__(self, parent, item_selected_callback, timestamp_callback, header_callback):
		super(PreviewPanel, self).__init__(parent)

		self._item_selected_callback = item_selected_callback
		self._timestamp_callback = timestamp_callback
		self._header_clicked_callback = header_callback

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
		self._tree_view.heading(COL_SELECTED, text = COL_SELECTED_TITLE, command = lambda: self._treeview_sort_column(COL_SELECTED))
		self._tree_view.heading(COL_NAME, text = COL_NAME_TITLE, anchor = W, command = lambda: self._treeview_sort_column(COL_NAME))
		self._tree_view.heading(COL_RENAME, text = COL_RENAME_TITLE, anchor = W, command = lambda: self._treeview_sort_column(COL_RENAME))
		self._tree_view.heading(COL_TYPE, text = COL_TYPE_TITLE, anchor = W, command = lambda: self._treeview_sort_column(COL_TYPE))
		self._tree_view.heading(COL_FOLDER, text = COL_FOLDER_TITLE, anchor = W, command = lambda: self._treeview_sort_column(COL_FOLDER))

	def show_files(self, files, sorted_header, asc):
		# reset all column headers
		self._init_column_headers()

		# update sorted header
		if sorted_header:
			# get new column header label
			col_label = ''
			if sorted_header == COL_SELECTED:
				col_label = COL_SELECTED_TITLE
			elif sorted_header == COL_NAME:
				col_label = COL_NAME_TITLE
			elif sorted_header == COL_RENAME:
				col_label = COL_RENAME_TITLE
			elif sorted_header == COL_TYPE:
				col_label = COL_TYPE_TITLE
			elif sorted_header == COL_FOLDER:
				col_label = COL_FOLDER_TITLE

			col_label += ' ↓' if asc else ' ↑'
			self._tree_view.heading(sorted_header, text = col_label)

		self._tree_view.delete(*self._tree_view.get_children())

		for info in files:
			values = [info.fname(), info.new_fname(), info.ext(), info.path()]
			if info.selected():
				text, tag = MARK_SELECTED, TAG_SELECTED
			else:
				text, tag = MARK_UNSELECTED, TAG_UNSELECTED
			self._tree_view.insert('', 'end', text = text, values = values, tags = [tag])

	def _treeview_on_clicked(self, event):
		x, y, widget = event.x, event.y, event.widget
		col_id = self._tree_view.identify_column(x)
		row_id = self._tree_view.identify_row(y) # if row is empty, then the column header is clicked.
		if row_id:
			if col_id == COL_SELECTED: # if clicked on the first column and on the list item.
				unselected = self._tree_view.tag_has(TAG_UNSELECTED, row_id)
				if unselected:
					self._select_file(row_id)
				else:
					self._unselect_file(row_id)

				if self._item_selected_callback:
					self._item_selected_callback(unselected, self._tree_view.index(row_id))
			elif col_id == COL_RENAME and self._timestamp_callback:
				self._tree_view.selection_set(row_id)
				self._timestamp_callback(self._tree_view.index(row_id), event.x_root, event.y_root)

	def _treeview_sort_column(self, col):
		if self._header_clicked_callback:
			self._header_clicked_callback(col)

	def _select_file(self, row_id):
		self._tree_view.item(row_id, text = MARK_SELECTED, tags = [TAG_SELECTED])

	def _unselect_file(self, row_id):
		self._tree_view.item(row_id, text = MARK_UNSELECTED, tags = [TAG_UNSELECTED])

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

FILES_TIMESTAMPS = 'files_timestamps.txt'
EXIF_CMD_ARGS = r'%s "-*Date*" "-*Time*" "--*Run*" "--*Sub*" "--*Exposure*" "--*Timer*" "--*Region*" "--*Scale*" -r %s > ' + FILES_TIMESTAMPS

class TimestampInfo():
	def __init__(self, tag, timestamp):
		self._tag = tag
		self._timestamp = timestamp

	def __str__(self):
		return 'TimestampInfo("%s", %s)' % (self._tag, self._timestamp)

	def __repr__(self):
		return self.__str__()

	def __eq__(self, other):
		return isinstance(other, TimestampInfo) and self._tag == other.tag() and self._timestamp == other.timestamp()

	def tag(self):
		return self._tag

	def timestamp(self):
		return self._timestamp

class FileInfo():
	def __init__(self, fname = '', ext = '', path = ''):
		self._fname = fname
		self._new_fname = ''
		self._ext = ext
		self._path = path
		self._abs_path = os.path.join(path, fname)
		self._timestamps = []
		self._selected = True

	def fname(self):
		return self._fname

	def new_fname(self):
		return self._new_fname

	def ext(self):
		return self._ext

	def path(self):
		return self._path

	def abs_path(self):
		return self._abs_path

	def timestamps(self):
		return self._timestamps

	def selected(self):
		return self._selected

	def select(self):
		self._selected = True

	def unselect(self):
		self._selected = False

	def set_timestamps(self, timestamps):
		# print('-' * 80)
		# print(self._abs_path)
		# print(self._timestamps)
		# pprint(timestamps)
		self._timestamps.clear()
		self._timestamps.extend(timestamps)
		self._gen_new_fname()

	def _gen_new_fname(self):
		if self._timestamps:
			ts = self._timestamps[0].timestamp().strftime('%Y%m%d_%H%M%S')
			self._new_fname = ts + self._ext

	def set_new_fname(self, new_ts):
		self._new_fname = new_ts + self._ext

class TimestampList(Menu):
	def __init__(self, root, cur_ts, timestamps, callback):
		super(TimestampList, self).__init__(root, tearoff = 0)

		# find maximum tag length
		max_len = max([len(ts.tag()) for ts in timestamps])
		for i, ts in enumerate(timestamps):
			if ts.timestamp().microsecond != 0:
				ts_str = ts.timestamp().strftime('%Y%m%d_%H%M%S_%f')
			else:
				ts_str = ts.timestamp().strftime('%Y%m%d_%H%M%S')

			label = ('%' + str(max_len) + 's : %s') % (ts.tag(), ts.timestamp())
			cmd = lambda ts = ts_str, callback = callback: callback(ts)

			# initialize a individual variable for each check button, to avoid they using same one, i.e. the default one.
			self.add_checkbutton(label = label, font = 'Consolas 8', variable = BooleanVar())

			# The method invoke() will trigger the command as well as set the select mark.
			# Therefore, set command after execute invoke().
			if ts_str.startswith(cur_ts):
				self.invoke(i)
			self.entryconfigure(i, command = cmd)

class RenameApp(Frame):
	def __init__(self):
		self._root = Tk()
		self._root.title('Rename Photo & Movie by Datetime - v3.0')
		self._root.state('zoomed')

		super(RenameApp, self).__init__(self._root)

		self._found_files = []
		self._files_sort_col = None
		self._files_sort_asc = False

		self._status_msg = StringVar(value = 'ready.')

		self._createWidgets()
		self.grid_columnconfigure(0, weight = 1)
		self.grid_rowconfigure(4, weight = 1)
		self.pack(fill = BOTH, expand = True)

		self._root.mainloop()

		# try:
		# 	os.remove(FILES_TIMESTAMPS)
		# except OSError:
		# 	pass

	def _createWidgets(self):
		self._config_panel = ConfigPanel(self)
		self._filter_panel = FilterPanel(self, self._scan_photos, self._preview_renaming, self._do_rename, self._on_ext_selected)
		self._preview_panel = PreviewPanel(self, self._on_file_selected, self._on_timestamp_clicked, self._on_header_clicked)
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

		self._found_files.clear()
		for root, dirs, files in os.walk(photo_folder):
			self._status_msg.set('scanning ' + root)
			for name in files:
				_base, ext = os.path.splitext(name)
				ext = ext.lower()
				if ext in SUPPORTED_SUFFIX:
					self._found_files.append(FileInfo(name, ext, root))
		self._sort_files()

		self._status_msg.set('Fetching timestamps of all supported files under %s ...' % (photo_folder))
		cmds = EXIF_CMD_ARGS % (exif_path, photo_folder)
		self._timestamp_thread = threading.Thread(target = self._get_timestamps, kwargs = {'cmds' : cmds})
		self._timestamp_thread.start()

		self._filter_panel.disable()
		self._root.after(100, self._check_timestamp_thread)

	def _sort_files(self):
		if not self._files_sort_col:
			return

		key = None
		if self._files_sort_col == COL_SELECTED:
			key = lambda x: (x.selected(), x.abs_path())
		elif self._files_sort_col == COL_NAME:
			key = lambda x: (x.fname(), x.path())
		elif self._files_sort_col == COL_RENAME:
			key = lambda x: (x.new_fname(), x.abs_path())
		elif self._files_sort_col == COL_TYPE:
			key = lambda x: (x.ext(), x.abs_path())
		elif self._files_sort_col == COL_FOLDER:
			key = lambda x: x.abs_path()

		self._found_files.sort(key = key, reverse = self._files_sort_asc)

	def _get_timestamps(self, cmds):
		subprocess.call(cmds, shell = True)

	def _check_timestamp_thread(self):
		if self._timestamp_thread.is_alive():
			self._root.after(100, self._check_timestamp_thread)
		else:
			size = 0
			try:
				size = os.path.getsize(FILES_TIMESTAMPS)
			except OSError:
				pass
			if size == 0:
				tmsgbox.showwarning('Oops', 'Failed to get timestamps of the files!')
				return

			timestamps = self._parse_timestamps()
			# pprint(timestamps)
			self._assign_timestamps(timestamps)

			self._filter_panel.show_extensions(self._found_files)
			self._filter_panel.enable()
			self._preview_panel.show_files(self._found_files, self._files_sort_col, self._files_sort_asc)
			self._status_msg.set('Done, found %d files!' % (len(self._found_files)))

	def _parse_timestamps(self):
		fp = codecs.open(FILES_TIMESTAMPS, 'r')
		lines = fp.readlines()
		fp.close()

		file_timestamps = {}
		last_fpath = None
		for l in lines:
			if l.startswith(' '):
				continue
			elif l.startswith('======== '):
				if last_fpath:
					self._merge_timestamps(file_timestamps, last_fpath)
				last_fpath = l[9:].strip().replace('/', os.path.sep)
				file_timestamps[last_fpath] = []
			else:
				info = self._parse_timestamp(l.strip())
				if info:
					file_timestamps[last_fpath].append(info)
		self._merge_timestamps(file_timestamps, last_fpath)
		return file_timestamps

	def _assign_timestamps(self, timestamps):
		for finfo in self._found_files:
			fpath = finfo.abs_path()
			if finfo.abs_path() in timestamps:
				finfo.set_timestamps(timestamps[fpath])

	def _parse_timestamp(self, text):
		tag, value = [part.strip() for part in text.split(':', 1)]
		ts, suffix = re.findall(r'^([0-9: .]+)(.*)$', value)[0]
		if ':' not in ts:
			return None

		is_utc0 = True if (suffix and suffix[0] == 'Z') or tag.startswith('GPS ') else False

		parts = re.split(r'[ :.]', ts)
		if len(parts) == 7:
			# valid date time
			pass
		elif len(parts) == 6:
			parts.append('0')
		elif len(parts) == 3 and len(parts[0]) == 4:
			# it is a date, append 0 time
			parts.extend(['0', '0', '0', '0'])
		elif len(parts) in [3, 4] and len(parts[0]) == 2:
			# it is a time, insert 0 date
			parts = ['1970', '1', '1'] + parts
		else:
			print('invalid ts:', text, '->', parts)
			return None

		ts = [int(s) for s in parts]
		ts = datetime(ts[0], ts[1], ts[2], ts[3], ts[4], ts[5], ts[6] * 1000)
		if is_utc0:
			ts = self._utc0_to_local(ts)

		return TimestampInfo(tag, ts)

	def _utc0_to_local(self, ts):
		return ts + (datetime.now() - datetime.utcnow())

	def _local_to_utc0(self, ts):
		return ts - (datetime.now() - datetime.utcnow())

	def _merge_local_date_time(self, date, time):
		date = self._local_to_utc0(date)
		time = self._local_to_utc0(time)
		ts = date + (time - datetime(1970, 1, 1))
		return self._utc0_to_local(ts)

	# FIXME: The merged timestamps still contain duplicated ones
	def _merge_timestamps(self, timestamps, key):
		# merge GPS Date with GPS Time
		gps_date, gps_time, full_ts = [], [], []
		for info in timestamps[key]:
			if info.tag() == 'GPS Date Stamp':
				gps_date.append(info.timestamp())
			elif info.tag() == 'GPS Time Stamp':
				gps_time.append(info.timestamp())
			else:
				full_ts.append(info)
		full_ts.extend([TimestampInfo('GPS Date/Time', self._merge_local_date_time(d, t)) for d in gps_date for t in gps_time])

		# return unique (tag, timestamp)
		full_ts.sort(key = lambda x: x.timestamp())
		timestamps[key].clear()
		for info in full_ts:
			if not timestamps[key] or info != timestamps[key][-1]:
				timestamps[key].append(info)

	def _on_file_selected(self, selected, item_idx):
		if item_idx < 0 or item_idx >= len(self._found_files):
			print('wrong index of clicked row:', item_idx)
			return

		info = self._found_files[item_idx]
		if selected:
			info.select()
		else:
			info.unselect()
		self._filter_panel.show_extensions(self._found_files)

	def _on_timestamp_clicked(self, item_idx, x, y):
		info = self._found_files[item_idx]
		ts, ext = os.path.splitext(info.new_fname())
		menu = TimestampList(self._root, ts, info.timestamps(), lambda new_ts, item_idx = item_idx: self._update_file_new_name(new_ts, item_idx))
		try:
			menu.post(x, y)
		finally:
			# make sure to release the grab (Tk 8.0a1 only)
			menu.grab_release()

	def _update_file_new_name(self, new_ts, item_idx):
		info = self._found_files[item_idx]
		info.set_new_fname(new_ts)

		# TODO:
		# 1. The microseconds is appended to the new name, convert it to milliseconds, or remove it if possible.
		# 2. Append sequence number for those images with same timestamps in seconds, then show the updated files.

		self._preview_panel.show_files(self._found_files, self._files_sort_col, self._files_sort_asc)

	def _on_header_clicked(self, col):
		if not self._files_sort_col:
			self._files_sort_asc = True
		else:
			self._files_sort_asc = not self._files_sort_asc
		self._files_sort_col = col
		self._sort_files()
		self._preview_panel.show_files(self._found_files, self._files_sort_col, self._files_sort_asc)

	def _on_ext_selected(self, ext, selected):
		for info in self._found_files:
			if info.ext() == ext:
				if selected:
					info.select()
				else:
					info.unselect()
		self._preview_panel.show_files(self._found_files, self._files_sort_col, self._files_sort_asc)

	def _preview_renaming(self):
		# TODO: it seems this method is useless, remove it and the bound button.
		pass

	def _do_rename(self):
		# TODO: implement the concrete renaming.
		pass

if __name__ == '__main__':
	RenameApp()

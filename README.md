# My Tools
This repository stores tools used in my daily life

## dl_novel.py
This script downloads pure text of specific novels, and stores them into .txt files. So that I can read them on my mobile phone.

## ren_photo_movie_by_datetime.py
I have dozen GB of home photos and movies. I've tried organizing them in several ways, while I choose the most simple way currently, i.e. rename those files by their created datetime.

I found several tools to read the created datetime from EXIF information, and [ExifTool](https://sno.phy.queensu.ca/~phil/exiftool/) is the one who supports all the formats.

To make it convenient, I implement a GUI for this script, which works with ExifTool and provides filtering files, previewing renaming and execute renaming.
 
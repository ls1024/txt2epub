#!/usr/bin/env python
# coding:utf-8

#
# Turn a Siyavula cnxmlplus.html book repo into an epub file.
# Assume each cnxmlplus file has been converted to html,
# and contains a chapter

import sys
import os
import time
import mimetypes
import shutil
import re
import zipfile
import codecs

from lxml import etree
from docopt import docopt

# uncomment to debug
#import pudb; pu.db

usage_info = """Usage: bookrepo2epub.py  --output <outputfolder>  --name <name> | --help


Arguments:
    --output  folder where EPUB will be created or updated
    --name    name of content that will be displayed in epub
    --help    display this message

"""

def make_new_epub_folder(options):
    '''given docopt's arguments dict: create an empty epub folder if it does not exist'''
    epubdir = os.path.abspath(os.path.join(os.curdir, options['<outputfolder>']))

    name = options['<name>'].replace(' ', '-')
    EPUBdir = os.path.join(epubdir, 'EPUB')
    METAdir = os.path.join(epubdir, 'META-INF')

    if not os.path.isdir(epubdir):
        os.makedirs(epubdir)
    if not os.path.isdir(EPUBdir):
        os.mkdir(EPUBdir)
    if not os.path.isdir(METAdir):
        os.mkdir(METAdir)

    return True

def is_chapter_title(line):
    if re.match(ur"[正文]*\s*[第终][0123456789一二三四五六七八九十百千万零 　\s]*[章部集节卷]", unicode(line,'utf-8')) :
        return True
    else: 
        return False

def makechapterhtml(filepath, chapter, chapnum):
    filepath = os.path.join(filepath, 'EPUB') 
    with open(os.path.join(filepath, '{:0>4d}.html'.format(chapnum)), 'w') as f:
        f.write(r'<?xml version="1.0" encoding="UTF-8"?>')
        f.write("""<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">
<head>
<title>"""+bookname+"""</title>
<meta content="http://www.w3.org/1999/xhtml; charset=utf-8" http-equiv="Content-Type"/>
<link rel="stylesheet" href="stylesheet.css" type="text/css" />
</head>
<body>
""")
        f.write(chapter[0] + '\n')
        f.write(chapter[1] + '\n')
        f.write("""</body>
</html>""")
        f.close()


if __name__ == "__main__":
    arguments = docopt(usage_info, sys.argv[1:])
    outputfolder = arguments['<outputfolder>']
    bookname = arguments['<name>']
    make_new_epub_folder(arguments)

    chapters = []
    chaptercontent = ''
    chaptername = ''
    frontpage = 0
    chapternum = 0

    bookfile = open('{bname}.txt'.format(bname = bookname),'r')
    for linenum,line in enumerate(bookfile.readlines()):
        line = line.strip()
        if  len(line):
            if is_chapter_title(line):
                    chaptername = '<h2>'+line+'</h2>'
                    if linenum <> 0 and not frontpage :
                        frontpage = 1
                        chaptername = '<h2>前言</h2>'                    
                    #chapterfiles.append(chaptercontent)
                    #chapters.append((chaptername, chaptercontent))
                    chapters.append((chaptername, chaptercontent))
                    #chapters[chapternum][0] = chaptername
                    #chapters[chapternum][1] = chaptercontent
                    chapternum += 1
                    chaptercontent = ''
            else:
                chaptercontent += '<p>'+line+'</p>\n'

    chapters.append((chaptername, chaptercontent))
    #chapters[chapternum][0] = chaptername
    #chapters[chapternum][1] = chaptercontent

    for chapternum, chapter in enumerate(chapters):
        makechapterhtml(outputfolder, chapter, chapternum)

                
    

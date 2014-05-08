#!/usr/bin/env python
# coding:utf-8

#
# Convert Chinese novel text file into an epub file.
# Assume each chapter has been converted to html,

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

usage_info = """Usage: txt2epub.py  --output <outputfolder>  --name <name> | --help


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

def writeopffile(filepath, manifest, spine):
    index_tpl = '''<package version="2.0" xmlns="http://www.idpf.org/2007/opf">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:identifier id="uid">Andy Lau txt2epub.1.0</dc:identifier>
        <dc:title>%(bname)s</dc:title>
        <dc:creator>Andy Lau</dc:creator>
        <dc:language>en</dc:language>
    </metadata>
    <manifest>
        %(manifest)s
    </manifest>
    <spine toc="ncx">
        %(spine)s
    </spine>
</package>'''

    with open(os.path.join(filepath, 'content.opf'), 'w') as f:
        f.write(index_tpl % {
            'bname': bookname,
            'manifest': manifest,
            'spine': spine,
        })

def writencxfile(filepath, navpoint):
    index_ncx = '''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
     <meta name="dtb:uid" content="Andy Lau txt2epub.1.0"/>
     <meta name="dtb:depth" content="1"/>
     <meta name="dtb:totalPageCount" content="0"/>
     <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>%(bname)s</text>
  </docTitle>
  <navMap>
    %(navpoint)s
  </navMap>
</ncx>'''

    with open(os.path.join(filepath, 'toc.ncx'), 'w') as f:
        f.write(index_ncx % {
            'bname': bookname,
            'navpoint': navpoint,
        })


def make_container(docoptions):
    epubfolder = docoptions['<outputfolder>']
    metafolder = os.path.join(epubfolder, 'META-INF')

    if not os.path.exists(metafolder):
        os.makedirs(metafolder)
    containerpath = os.path.join(metafolder, "container.xml")
    if os.path.exists(containerpath):
        try:
            container = etree.parse(containerpath)
        except etree.XMLSyntaxError:
            container = etree.XML('<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>\n</rootfiles></container>')
    else:
        container = etree.XML('<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>\n</rootfiles></container>')

    packagefilepath = "content.opf"
    current_rootfiles = [r.attrib['full-path'] for r in container.findall('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')]
    if packagefilepath not in current_rootfiles:
        rootfile = etree.Element('rootfile', attrib={'media-type':"application/oebps-package+xml", 'version':'1.0', 'full-path':packagefilepath})
        rootfile.tail = '\n'
        container.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfiles').append(rootfile)

    return container


if __name__ == "__main__":
    arguments = docopt(usage_info, sys.argv[1:])
    outputfolder = arguments['<outputfolder>']
    bookname = arguments['<name>']
    make_new_epub_folder(arguments)

    chapters = []
    chaptercontent = ''
    chaptername = ''
    frontpage = 0

    bookfile = open('{bname}.txt'.format(bname = bookname),'r')
    for linenum,line in enumerate(bookfile.readlines()):
        line = line.strip()
        if  len(line):
            if is_chapter_title(line):
                    chaptername = '<h2>'+line+'</h2>'
                    if linenum <> 0 and not frontpage :
                        frontpage = 1
                        chaptername = '<h2>前言</h2>'                    
                    chapters.append((chaptername, chaptercontent))
                    chaptercontent = ''
            else:
                chaptercontent += '<p>'+line+'</p>\n'

    chapters.append((chaptername, chaptercontent))

    manifest = '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>\n'
    spine = ''
    navpoint = ''

    for chapternum, chapter in enumerate(chapters):
        makechapterhtml(outputfolder, chapter, chapternum)
        manifest += '<item id="chapter_{:0>4d}" href="/EPUB/{:0>4d}.html" media-type="application/xhtml+xml"/>\n'.format(chapternum, chapternum)
        spine += '<itemref idref="chapter_{:0>4d}" />\n'.format(chapternum)

        navpoint += '''  <navPoint class="chapter" id="chapter_{seq}" playOrder="{seq}">
    <navLabel>
      <text>{chaptitle}</text>
    </navLabel>
    <content src="/EPUB/{seq}.html"/>
  </navPoint>
'''.format(seq = '{:0>4d}'.format(chapternum), chaptitle = chapter[0])

    #write package.opf
    writeopffile(outputfolder, manifest, spine)

    #write toc.ncx
    writencxfile(outputfolder, navpoint)

    #write container.xml
    epubfolder = arguments['<outputfolder>']
    metafolder = os.path.join(epubfolder, 'META-INF')
    containerpath = os.path.join(metafolder, "container.xml")
    container = make_container(arguments)
    with open(containerpath, 'w') as f:
        f.write(etree.tostring(container, pretty_print=True))

    # write mimetype
    with open(os.path.join(epubfolder, 'mimetype'), 'w') as f:
        f.write('application/epub+zip')
        f.close()

    ## finally zip everything into the destination
    out = zipfile.ZipFile(os.path.join(epubfolder, '{bname}.epub'.format(bname = bookname)), "w", zipfile.ZIP_DEFLATED)
    out.write(epubfolder + "/mimetype", "mimetype", zipfile.ZIP_STORED)
    
    for root, dirs, files in os.walk(os.path.join(epubfolder,'.')):  
        for name in files:  
            if name <> 'mimetype' :
               fname = os.path.join(root, name)
               new_path = os.path.normpath(fname.replace(epubfolder,''))
               out.write(fname, new_path)  

    out.close()

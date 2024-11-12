#!/usr/bin/env python3

# Appie2 is based on the original Appie from z25.org and makesite.py
#
# The MIT License (MIT)
#
# Copyright (c) 2025 Arnaud Loonstra
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""Make static site with Python."""


import os
import shutil
import re
import glob
import sys
import json
import datetime
import markdown
from PIL import Image

# Load jinja templates
from jinja2 import Environment, FileSystemLoader
# Create a Jinja2 environment and specify the template directory
env = Environment(loader=FileSystemLoader('./templates'))

def fread(filename):
    """Read file and close the file."""
    with open(filename, 'r') as f:
        return f.read()

def fwrite(filename, text):
    """Write content to file and close the file."""
    basedir = os.path.dirname(filename)
    if not os.path.isdir(basedir):
        os.makedirs(basedir)

    with open(filename, 'w') as f:
        f.write(text)

def fix_meta(meta):
    for k,v in meta.items():
        if len(v) == 1:
            meta[k] = v[0]
    
def walk_directory(directory, **params):
    """
    Walk through a directory and collect file meta data.
    Return a dict containing all entries
    """
    file_times = {}
    folders = set()
    tree = {}

    for foldername, subfolders, filenames in os.walk(directory):
        folders.add(foldername)
        relfolder = os.path.relpath(foldername, directory)
        d = { "_type": "dir", "_path": relfolder, "_srcpath": foldername }
        for filename in filenames:
            filepath = os.path.join(foldername, filename)
            userfilename, ext = os.path.splitext(filename)
            relfile = os.path.join(relfolder, filename) # same? os.path.relpath(filepath, directory)
            mtime = os.path.getmtime(filepath)
            f = { 
                "_type": "file", 
                "_mtime": mtime,
                "_srcpath": filepath,
                "_sitedir": relfolder,
                "_filename": userfilename,
                "_ext": ext,
                "_sitepath": relfile
            }
            d[filename] = f
            
            file_times[filepath] = { "mtime": mtime }
        tree[relfolder] = d
            
    return file_times, tree #dict((k,v) for k,v in zip(folders, [None]*len(folders)))

def read_first_paragraph(html_content):
    """return the first paragraph found in the html content"""
    # Assuming paragraphs are separated by double line breaks in HTML
    paragraphs = html_content.split('<p>')
    if len(paragraphs) > 1:
        first_paragraph = paragraphs[1].split('</p>')[0]
        return first_paragraph
    else:
        return None

def read_headers(html_content):
    """Parse headers in text and yield (key, value, end-index) tuples."""
    for match in re.finditer(r'\s*<!--\s*(.+?)\s*:\s*(.+?)\s*-->\s*|.+', html_content):
        if not match.group(1):
            break
        yield match.group(1), match.group(2), match.end()


def read_first_img(html_content):
    """
    Find the first <img> tag in the HTML and return it or None if 
    none found
    """
    # Assuming images are done with <img> tag in HTML
    match = re.search(r'<img[^>]*src=["\'](.*?)["\']', html_content)
    # Return the src attribute if found
    if match:
        return match.group(1)
    else:
        return None

def parse_dir(tree, **params):
    """Parse a directory (tree) recursively"""
    for k, v in tree.items():
        # don't parse leaves
        if type(v) != dict:
            continue
        elif v["_type"] == "dir":
            os.makedirs(os.path.join("_site", v["_path"]), exist_ok=True)
            parse_dir(v, **params)  #recurse
            generate_index(v, **params)
        else:
            parse_path(v, **params)
    if params.get("_tags"):
        generate_tags(params["_tags"], **params)


def parse_path(file, **params):
    """
    Parse the filepath in the folder, we use the folder name to match a 
    jinja template
    """
    sitedir = file["_sitedir"]
    folder = os.path.dirname(file["_sitedir"])
    filename = file["_filename"]
    ext = file["_ext"]
    dirname = os.path.basename(folder)
    outfilepath = os.path.join( "_site", file["_sitedir"], filename )
    
    # try to load a corresponding template
    try:
        template = env.get_template('{}.html'.format(dirname))
        print("using the {} template for {}".format(dirname, file["_srcpath"]))
    except Exception as e:
        template = env.get_template('default.html')
        
    # match file extensions
    if ext == ".md": # Parse Markdown file
        siteurl = os.path.join( file["_sitedir"], filename )+".html"
        md = markdown.Markdown(
                        extensions=[
                            'tables',
                            'meta',
                            'codehilite',
                            'toc'
                            ]
                        )
        # generate the html from the .md file
        html = md.convert(fread(file["_srcpath"]))
        fix_meta(md.Meta)
        if not md.Meta.get('img'):
            md.Meta['img'] = read_first_img(html)
        if not md.Meta.get('summary'):
            md.Meta['summary'] = read_first_paragraph(html)
        file.update(md.Meta)
        file.update({
                    "content": html,
                    "url": siteurl
                    })
        sitehtml = template.render(**file, **params)
        fwrite( "{}.html".format(outfilepath), sitehtml)
    elif ext == ".html": # Parse HTML file
        siteurl = os.path.join( file["_sitedir"], filename )+".html"
        html = fread(file["_srcpath"])
        # try to find meta data (<!--) in html
        for key, val, end in read_headers(html):
            file[key] = val
        firstimg = read_first_img(html)
        summary = read_first_paragraph(html)
        file.update({
            "content": html,
            "img": firstimg, 
            "summary": summary, 
            "url": siteurl
            })
        sitehtml = template.render(**file, **params)
        fwrite( "{}.html".format(outfilepath), sitehtml)
        summary = read_first_paragraph(html)
        if summary:
            return {"summary": summary, "url": siteurl }
        return {"url": siteurl}
    elif ext == ".jpg":
        parse_jpg(file, outfilepath, **params)
    elif ext == ".png":
        parse_png(file, outfilepath, **params)
    else:
        # just copy
        shutil.copy(file["_srcpath"], outfilepath + ext)
    # save any tags we found to params
    for t in file.get("tags", []):
        if not params.get("_tags").get(t): params["_tags"][t] = []
        taglist = params["_tags"].get(t)
        taglist.append(file)

def parse_png(file, outfilepath, **params):
    """parse png image, save its mimetype and create thumbnails"""
    shutil.copy(file["_srcpath"], outfilepath + ".png")
    outfilepath = os.path.join("_site", os.path.splitext(file["_sitepath"])[0])
    file['mimetype'] = 'image/png'   # https://www.w3.org/Graphics/PNG/
    file['url'] = os.path.join( file["_sitedir"], file["_filename"] )+".png"
    resize_img(file, outfilepath, **params)

def parse_jpg(file, outfilepath, **params):
    """parse jpg image, save its mimetype and create thumbnails"""
    shutil.copy(file["_srcpath"], outfilepath + ".jpg")
    outfilepath = os.path.join("_site", os.path.splitext(file["_sitepath"])[0])
    file['mimetype'] = 'image/jpg'
    file['url'] = os.path.join( file["_sitedir"], file["_filename"] )+".jpg"
    resize_img(file, outfilepath, **params)

def resize_img(file, outfilepath, **params):
    """create different sized images of the provided image"""
    jpg_filename = outfilepath + "_web.jpg"
    thumb_filename = outfilepath + "_thumb.jpg"

    img = Image.open(file["_srcpath"])
    size = img.size
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    if img.mode in ('RGB', 'CMYK', 'I'):
        img.thumbnail(params.get('jpg_size', (1280, 720)), Image.LANCZOS)
        img.save(jpg_filename, "JPEG", quality=80,
                    optimize=True, progressive=True)
        img.thumbnail(params.get('thumb_size', (384, 216)), Image.LANCZOS)
        img.save(thumb_filename, "JPEG", quality=80,
                    optimize=True, progressive=True)
    else:
        log("Image {0} is not a valid color image (mode={1})"
                       .format(filepath, img.mode))

    # update the file's meta data in the dictionary
    file.update({
            'size': size,              # tuple (width,height)
            'web': jpg_filename,
            'thumb': thumb_filename,
            'md5': 'todo'
            })

def generate_index(folder, **params):
    """Generate an index file for the provided folder"""
    foldername = os.path.dirname(folder["_path"]) or folder["_path"]
    try:
        tpl = env.get_template('{}_index.html'.format(foldername))
        print("using the {} template for {}".format(foldername, folder["_srcpath"]))
    except Exception as e:
        tpl = env.get_template('index.html')
    entries = tuple(v for k, v in folder.items() if type(v) == dict)
    sitehtml = tpl.render(entries=entries, **folder, **params)
    fwrite( os.path.join("_site", folder["_path"], "index.html"), sitehtml)    

def generate_tags(taglist, **params):
    """Generate a tags index for the provided taglist"""
    try:
        tpl = env.get_template('tags_index.html')
        print("using the tags_index template")
    except Exception as e:
        tpl = env.get_template('index.html')

    alltags = []
    # write a html doc for every tag
    for tag, entries in taglist.items():
        alltags.append({ "title": tag, "url": "tags/"+tag})
        foldername = os.path.join("tags", tag)
        sitehtml = tpl.render(title=tag, content="<h1>tagged with "+tag+"</h1>",
                                entries=entries, **params)
        fwrite( os.path.join("_site", "tags", tag + ".html"), sitehtml)
    # finally write the tag index
    sitehtml = tpl.render(title="tags", content="<h1>All tags</h1>",
                                entries=alltags, **params)
    fwrite( os.path.join("_site", "tags", "index.html"), sitehtml)

def main():
    # Create a new _site directory from scratch.
    if os.path.isdir('_site'):
        shutil.rmtree('_site/')
    shutil.copytree('static', '_site')

    # Default parameters.
    params = {
        'base_path': '/',
        'subtitle': 'Lorem Ipsum',
        'author': 'Admin',
        'site_url': 'http://localhost:8000',
        'current_year': datetime.datetime.now().year,
        '_tags': {},
    }

    # If params.json exists, load it.
    if os.path.isfile('params.json'):
        params.update(json.loads(fread('params.json')))

    # walk the content dir to a dict and list of folders
    file_times, tree = walk_directory("./content")
                    
    # get nav entries from the root dir:
    if not params.get("nav"):
        nav = []
        for k,v in tree.items():
            if type(v) != dict:
                continue
            if v.get("_type") == "dir":
                nav.append(k)

        params["nav"] = nav

    # process all the dirs files in the tree
    parse_dir(tree, **params)


if __name__ == '__main__':
    main()

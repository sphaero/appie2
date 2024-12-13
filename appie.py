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


helpmsg ="""
Appie is a minimal python static site generator. Just read the source!

-h      This help message
-f      Rebuild the site from scratch (rm -rf _site dir before run)
"""

import os
import shutil
import re
import sys
import json
import datetime
import markdown
from PIL import Image
# A very simple plugin system. Just create a plugins.py file
# with the match_dir and match_file function. If the file doesn't
# exist we create an empty plugin as a class
if os.path.isfile("plugins.py") and __name__ == "__main__":
    import plugins
else:
    class plugins:
        def match_dir(*args, **kwargs):
            pass
        def match_file(*args, **kwargs):
            pass

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

def is_source_newer(source: str, target: str) -> bool:
    """
    Checks if the source file is newer than the target file.
    """
    try:
        # Check if the source file exists
        if not os.path.exists(source):
            raise FileNotFoundError(f"Source file '{source}' does not exist.")
        
        # Check if the target file exists
        if not os.path.exists(target):
            # If the target doesn't exist, consider source as newer
            return True
        
        # Get the modification times
        source_mtime = os.path.getmtime(source)
        target_mtime = os.path.getmtime(target)
        
        # Compare the modification times
        return source_mtime > target_mtime
    except Exception as e:
        print(f"Error: {e}")
        return False
    
def walk_directory(directory, basepath=None, **params):
    """
    Walk through a directory and collect file meta data.
    Return a dict containing all entries
    """
    if basepath == None:
        basepath=directory
        
    dir_dict = {'_path': '',
                '_srcpath': directory,
                '_type': 'dir',
                }
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                # entry.name filename
                # entry.path fullpath relative to called directory
                relpath = os.path.relpath(entry.path, basepath)
                relfolder = os.path.dirname(relpath)
                if entry.is_dir():
                    # Recursively include subdirectory
                    d = walk_directory(entry.path, 
                                       basepath,
                                       **params)
                    d.update({ "_type": "dir", 
                               "_path": relpath, 
                               "_srcpath": entry.path })

                    dir_dict[entry.name] = d
                else:
                    # Include file as a leaf
                    filepath = os.path.join(directory, entry.name)
                    userfilename, ext = os.path.splitext(entry.name)
                    relfile = os.path.join(relfolder, entry.name) # same? os.path.relpath(filepath, directory)
                    dir_dict[entry.name] = { 
                        "_type": "file", 
                        "_srcpath": entry.path,
                        "_sitedir": relfolder,
                        "_filename": userfilename,
                        "_ext": ext,
                        "_sitepath": relfile
                    }
    except PermissionError:
        dir_dict["error"] = "Permission Denied"
    return dir_dict

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
    # first check if plugins.py wants this dir
    if not plugins.match_dir(tree, **params):
        for k, v in tree.items():
            # don't parse leaves
            if type(v) != dict:
                continue
            elif v["_type"] == "dir":
                os.makedirs(os.path.join(params["output_path"], v["_path"]), exist_ok=True)
                parse_dir(v, **params)  #recurse
            else:
                # first check if a plugin wants this file
                if not plugins.match_file(v, **params):
                    parse_path(v, **params)
                # save any tags we found to params
                for t in v.get("tags", []):
                    if not params.get("_tags").get(t): 
                        params["_tags"][t] = []
                    taglist = params["_tags"].get(t)
                    taglist.append(v)
    # generate an index for the dir
    generate_index(tree, **params)
    if params.get("_tags"):
        generate_tags(params["_tags"], **params)

def parse_path(file, **params):
    """
    Parse the filepath in the folder, we use the folder name to match a 
    jinja template
    """
    sitedir = file["_sitedir"]
    folder = os.path.dirname(file["_sitepath"])
    filename = file["_filename"]
    ext = file["_ext"]
    dirname = os.path.normpath(folder).split(os.sep)[0] # for templates we use the first dir!
    outfilepath = os.path.join(params["output_path"], file["_sitedir"], filename )

    # try to load a corresponding template
    try:
        template = env.get_template('{}.html'.format(dirname))
        print("using the {}.html template for {}".format(dirname, file["_srcpath"]))
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
        if not file.get('thumbnail'):
            if not md.Meta.get('thumbnail') and md.Meta.get('images'):
                if md.Meta.get('images')[0]:
                    file['thumbnail'] = md.Meta.get('images')[0]
            if not file.get('thumbnail'):
                img = read_first_img(html)
                if img:
                    file['thumbnail'] = img
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
        if firstimg:
            file["thumbnail"] = firstimg
        summary = read_first_paragraph(html)
        file.update({
            "content": html,
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
        if is_source_newer(file.get("_srcpath"), outfilepath + ext):
           # just copy
            shutil.copy(file["_srcpath"], outfilepath + ext)

def parse_png(file, outfilepath, **params):
    """parse png image, save its mimetype and create thumbnails"""
    if is_source_newer(file.get("_srcpath"), outfilepath + ".png"):
        shutil.copy(file["_srcpath"], outfilepath + ".png")
    outfilepath = os.path.join(params["output_path"], os.path.splitext(file["_sitepath"])[0])
    file['mimetype'] = 'image/png'   # https://www.w3.org/Graphics/PNG/
    file['url'] = os.path.join( file["_sitedir"], file["_filename"] )+".png"
    resize_img(file, outfilepath, **params)

def parse_jpg(file, outfilepath, **params):
    """parse jpg image, save its mimetype and create thumbnails"""
    if is_source_newer(file.get("_srcpath"), outfilepath + ".jpg"):
        shutil.copy(file["_srcpath"], outfilepath + ".jpg")
    outfilepath = os.path.join(params["output_path"], os.path.splitext(file["_sitepath"])[0])
    file['mimetype'] = 'image/jpg'
    file['url'] = os.path.join( file["_sitedir"], file["_filename"] )+".jpg"
    resize_img(file, outfilepath, **params)

def resize_img(file, outfilepath, **params):
    """create different sized images of the provided image"""
    jpg_filename = outfilepath + "_web.jpg"
    thumb_filename = outfilepath + "_thumb.jpg"
    img = Image.open(file["_srcpath"])
    size = img.size
    if (is_source_newer(file.get("_srcpath"), jpg_filename) or
        is_source_newer(file.get("_srcpath"), thumb_filename)):
    
        if img.mode == 'RGBA' or img.mode == 'P':
            img = img.convert('RGB')
        if img.mode in ('RGB', 'CMYK', 'I'):
            print("saving", jpg_filename)

            img.thumbnail(params.get('jpg_size', (1280, 720)), Image.LANCZOS)
            img.save(jpg_filename, "JPEG", quality=80,
                        optimize=True, progressive=True)
            img.thumbnail(params.get('thumb_size', (384, 216)), Image.LANCZOS)
            img.save(thumb_filename, "JPEG", quality=80,
                        optimize=True, progressive=True)
        else:
            print("Image {0} is not a valid color image (mode={1})"
                           .format(file["_srcpath"], img.mode))

    img.close()
    # update the file's meta data in the dictionary
    file.update({
            'size': size,              # tuple (width,height)
            'web': file["_filename"] + "_web.jpg",
            'thumb': file["_filename"] + "_thumb.jpg",
            'md5': 'todo'
            })

def generate_index(folder, **params):
    """Generate an index file for the provided folder"""
    # Trick to debug jinja2 parsing
    #from jinja2 import Template
    #tpl = Template("Item1: {{ folder['test.jpg'] }}, Item2: {{ ['bewogen.md'] }}, Param1: {{folder['_srcpath'] }}")
    #sitehtml = tpl.render(entries=entries, folder=folder, **params)
    #print(sitehtml)
    if folder.get("_skipindex"):
        print("Skip index requested for {}".format(folder["_srcpath"]))
        return # skip index requested so return
    foldername = os.path.dirname(folder["_path"]) or folder["_path"]
    try:
        tpl = env.get_template('{}_index.html'.format(foldername))
        print("using the {}_index.html template for {}".format(foldername, folder["_srcpath"]))
    except Exception as e:
        tpl = env.get_template('index.html')

    entries = tuple(v for k, v in folder.items() if type(v) == dict)
    try:    #try to sort on a date key but filename if it fails
        entries = sorted(entries, key=lambda x: x["date"], reverse=True)
        print("Index for {} is sorted by the date key".format(foldername))
    except:
        entries = sorted(entries, key=lambda x: x.get("_filename", ""))
    # save latest nav entries
    if folder["_path"] in params.get("nav", []):
        params["_latest"].append(entries[0])

    sitehtml = tpl.render(entries=entries, folder=folder, **params)
    fwrite( os.path.join(params["output_path"], folder["_path"], "index.html"), sitehtml)    

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
        fwrite( os.path.join(params["output_path"], "tags", tag + ".html"), sitehtml)
    # finally write the tag index
    sitehtml = tpl.render(title="tags", content="<h1>All tags</h1>",
                                entries=alltags, **params)
    fwrite( os.path.join(params["output_path"], "tags", "index.html"), sitehtml)

def main():
    # Default parameters.
    params = {
        'base_path': '/',
        'output_path': '_site',
        'input_path': 'content',
        'subtitle': 'Lorum Ipsum',
        'site_url': 'http://localhost:8000',
        'current_year': datetime.datetime.now().year,
        '_tags': {},
        '_latest': []
    }
    # If params.json exists, load it.
    if os.path.isfile('params.json'):
        params.update(json.loads(fread('params.json')))
        
    from_scratch = False
    for arg in sys.argv:
        if arg == "-f" :
            from_scratch = True
        if arg == "-h":
            print(helpmsg)         
            sys.exit(0)

    if from_scratch or not os.path.isdir(params['output_path']):
        # Create a new _site directory from scratch.
        if os.path.isdir(params['output_path']):
            shutil.rmtree(params['output_path'])
    shutil.copytree('static', params['output_path'], dirs_exist_ok=True)

    # walk the content dir to a dict and list of folders
    tree = walk_directory(params["input_path"], **params)
                    
    # get nav entries from the root dir:
    if not params.get("nav"):
        nav = []
        for k in sorted(tree):
            if type(tree[k]) != dict:
                continue
            if tree[k].get("_type") == "dir":
                nav.append(k)

        params["nav"] = nav

    # process all the dirs files in the tree
    parse_dir(tree, **params)


if __name__ == '__main__':
    main()

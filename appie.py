#!/usr/bin/env python

# Appie2 is based on the original Appie from z25.org and makesite.py
#
# The MIT License (MIT)
#
# Copyright (c) 2018-2022 Sunaina Pai
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

# Load jinja templates
from jinja2 import Environment, FileSystemLoader
# Create a Jinja2 environment and specify the template directory
env = Environment(loader=FileSystemLoader('./templates'))


def get_file_mtime(file_path):
    """Get the modification time of a file."""
    return os.path.getmtime(file_path)

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

def walk_directory(directory):
    """
    Walk through a directory and collect file modification times.
    and an empty dict with folder keys
    """
    file_times = {}
    folders = set()

    for foldername, subfolders, filenames in os.walk(directory):
        folders.add(foldername)
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            mtime = get_file_mtime(file_path)
            file_times[file_path] = { "mtime": mtime }
    
    return file_times, dict((k,v) for k,v in zip(folders, [None]*len(folders)))

def log(msg, *args):
    """Log message with specified arguments."""
    sys.stderr.write(msg.format(*args) + '\n')

def rfc_2822_format(date_str):
    """Convert yyyy-mm-dd date string to RFC 2822 format date string."""
    d = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    return d.strftime('%a, %d %b %Y %H:%M:%S +0000')

def read_first_paragraph(html_content):
    # Assuming paragraphs are separated by double line breaks in HTML
    paragraphs = html_content.split('<p>')
        
    if len(paragraphs) > 1:
        first_paragraph = paragraphs[1].split('</p>')[0]
        return first_paragraph
    else:
        return None

def parse_md(filepath, **params):
    pass

def parse_png(filepath, outfilepath, **params):
    shutil.copy(filepath, outfilepath + ".png")
    resize_img(filepath, outfilepath, **params)
    
def parse_jpg(filepath, outfilepath, **params):
    shutil.copy(filepath, outfilepath + ".jpg")
    resize_img(filepath, outfilepath, **params)
    
def resize_img(filepath, outfilepath, **params):
    #file = os.path.basename(filepath)
    #filename, ext = os.path.splitext(filepath)
    #folder = os.path.dirname(filepath)
    #dirname = os.path.basename(folder)
    #rootdir, remaining_path = os.path.split(folder)
    #outfilepath = os.path.join( "_site", "{}.jpg".format(filename) ) 
    jpg_filename = outfilepath + "_web.jpg"
    thumb_filename = outfilepath + "_thumb.jpg"

    img = Image.open(filepath)
    size = img.size
    if img.mode in ('RGB', 'RGBA', 'CMYK', 'I'):
        img.thumbnail(params.get('jpg_size', (1280, 720)), Image.ANTIALIAS)
        img.save(jpg_filename, "JPEG", quality=80, 
                    optimize=True, progressive=True)
        img.thumbnail(params.get('thumb_size', (384, 216)), Image.ANTIALIAS)
        img.save(thumb_filename, "JPEG", quality=80, 
                    optimize=True, progressive=True)
    else:
        log("Image {0} is not a valid color image (mode={1})"
                       .format(filepath, img.mode))
    shutil.copy(filepath, outfilepath + ".jpg")

    return {
            'mimetype': 'image/jpg',   # https://www.w3.org/Graphics/PNG/
            'size': size,              # tuple (width,height)
            'web': jpg_filename,
            'thumb': thumb_filename,
            'path': dest_path,
            'md5': 'todo'
            }

def parse_path(filepath, **params):
    """
    Parse the filepath in the folder, we use the folder name to match a jinja
    template
    """
    sitepath = os.path.relpath(filepath, "./content")
    sitedir = os.path.dirname(sitepath)
    file = os.path.basename(filepath)
    folder = os.path.dirname(filepath)
    filename, ext = os.path.splitext(file)
    dirname = os.path.basename(folder)
    outfilepath = os.path.join( "_site", sitedir, filename )
    
    #import pdb
    #pdb.set_trace()
    # try to load a corresponding template
    try:
        template = env.get_template('{}.html'.format(dirname))
    except Exception as e:
        template = env.get_template('base.html')
        
    # first try to match dirs
    #if dirname == "img":
    #    print("parse images")
        
    # then file extensions
    if ext == ".md":
        siteurl = os.path.join( "/", sitedir, filename )+".html"
        md = markdown.Markdown(
                        extensions=[
                            'tables',
                            'meta',
                            'codehilite',
                            'toc'
                            ]
                        )
        # generate the html from the .md file
        html = md.convert(fread(filepath))
        # TODO: parse tags
        summary = read_first_paragraph(html)
        meta = md.Meta #copy?
        meta.update({"summary": summary})
        meta.update({"url": siteurl})
        params.update(md.Meta)
        params.update({"content": html})
        sitehtml = template.render(**params)
        fwrite( "{}.html".format(outfilepath), sitehtml)
        return meta
    elif ext == ".html":
        siteurl = os.path.join( "/",  sitedir, filename )+".html"
        html = fread(filepath)
        params.update({"content": html})
        sitehtml = template.render(**params)
        fwrite( "{}.html".format(outfilepath), sitehtml)
        summary = read_first_paragraph(html)
        if summary:
            return {"summary": summary, "url": siteurl }
        return {"url": siteurl}
    elif ext == ".jpg":
        return parse_jpg(filepath, outfilepath, **params)
    elif ext == ".png":
        return parse_png(filepath, outfilepath **params)

def generate_index(folder, file_items, **params):
    sitepath = os.path.relpath(folder, "./content")
    if sitepath != ".": # we don't need to parse the root
        projects = []
        for filepath, meta in file_items.items():
            if folder in os.path.dirname(filepath):
                projects.append(meta)
                #print(folder, filepath)

        #print("bla", folder)
        if projects:
            sitepath = os.path.relpath(folder, "./content")
            try:
                tpl = env.get_template('{}.html'.format(sitepath))
                print("using the {} template".format(sitepath))
            except Exception as e:
                print("using the base template for {}".format(sitepath))
                tpl = env.get_template('base.html')
            context = {"subtitle": "blalaal"}
            context.update({"projects":projects})
            import pprint
            pprint.pprint(context)
            sitehtml = tpl.render(**context)
            print("writing", sitepath, params)
            fwrite( os.path.join("_site", sitepath, "index.html"), sitehtml)    
    
def make_pages(src, dst, layout, **params):
    """Generate pages from page content."""
    items = []

    for src_path in glob.glob(src):
        content = read_content(src_path)

        page_params = dict(params, **content)

        # Populate placeholders in content if content-rendering is enabled.
        if page_params.get('render') == 'yes':
            rendered_content = render(page_params['content'], **page_params)
            page_params['content'] = rendered_content
            content['content'] = rendered_content

        items.append(content)

        dst_path = render(dst, **page_params)
        output = render(layout, **page_params)

        log('Rendering {} => {} ...', src_path, dst_path)
        fwrite(dst_path, output)

    return sorted(items, key=lambda x: x['date'], reverse=True)


def make_list(posts, dst, list_layout, item_layout, **params):
    """Generate list page for a blog."""
    items = []
    for post in posts:
        item_params = dict(params, **post)
        item_params['summary'] = truncate(post['content'])
        item = render(item_layout, **item_params)
        items.append(item)

    params['content'] = ''.join(items)
    dst_path = render(dst, **params)
    output = render(list_layout, **params)

    log('Rendering list => {} ...', dst_path)
    fwrite(dst_path, output)


def main():
    # Create a new _site directory from scratch.
    if os.path.isdir('_site'):
        shutil.rmtree('_site/')
    shutil.copytree('static', '_site')

    # Default parameters.
    params = {
        'base_path': '',
        'subtitle': 'Lorem Ipsum',
        'author': 'Admin',
        'site_url': 'http://localhost:8000',
        'current_year': datetime.datetime.now().year
    }

    # If params.json exists, load it.
    if os.path.isfile('params.json'):
        params.update(json.loads(fread('params.json')))


    # Load the template by name
    template = env.get_template('base.html')
    
    # walk the content dir to a dict and list of folders
    file_times, folders = walk_directory("./content")
    
    # process all the files
    for filepath, meta in file_times.items():
        #print(filepath, meta)
        newmeta = parse_path(filepath, **params)
        if newmeta:
            meta.update(newmeta)
        folders[filepath] = newmeta
        
    # generate an index for every folder
    #import pprint
    #pprint.pprint(folders)
    for path in folders:
        generate_index(path, file_times, **params)
        
    #for foldername, subfolders, filenames in os.walk("content"):
    #    for filename in filenames:
    #        make_page(foldername, filename, **params)
    sys.exit(0)

    page_layout = fread('layout/page.html')
    post_layout = fread('layout/post.html')
    list_layout = fread('layout/list.html')
    item_layout = fread('layout/item.html')
    feed_xml = fread('layout/feed.xml')
    item_xml = fread('layout/item.xml')

    # Combine layouts to form final layouts.
    post_layout = render(page_layout, content=post_layout)
    list_layout = render(page_layout, content=list_layout)

    # Create site pages.
    make_pages('content/_index.html', '_site/index.html',
               page_layout, **params)
    make_pages('content/[!_]*.html', '_site/{{ slug }}/index.html',
               page_layout, **params)

    # Create blogs.
    blog_posts = make_pages('content/blog/*.md',
                            '_site/blog/{{ slug }}/index.html',
                            post_layout, blog='blog', **params)
    news_posts = make_pages('content/projects/*.html',
                            '_site/projects/{{ slug }}/index.html',
                            post_layout, blog='projects', **params)

    # Create blog list pages.
    make_list(blog_posts, '_site/blog/index.html',
              list_layout, item_layout, blog='blog', title='Blog', **params)
    make_list(news_posts, '_site/news/index.html',
              list_layout, item_layout, blog='news', title='News', **params)

    # Create RSS feeds.
    make_list(blog_posts, '_site/blog/rss.xml',
              feed_xml, item_xml, blog='blog', title='Blog', **params)
    make_list(news_posts, '_site/news/rss.xml',
              feed_xml, item_xml, blog='news', title='News', **params)


# Test parameter to be set temporarily by unit tests.
_test = None


if __name__ == '__main__':
    main()

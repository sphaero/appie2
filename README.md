appie.py
========

A minimal, lightweight static website/blog generator. Just a single file which you can modify to your liking.

TL;DR
-----

* Clone or download this repository to your computer
* Modify/add static files to the static dir
* Modify/add content in the content dir
* Run python3 appie.py, the site is generated in the _site dir
* Upload to some webhosting platform

See the example [here](http://pong.hku.nl/~arnaud.loonstra/appie2/)
Contents
--------

* [Introduction](#introduction)
* [Usage](#usage)
* [The Code](#the-code)
* [Credits](#credits)
* [License](#license)
* [Support](#support)

Introduction
------------

In this repository you will find an example website with a MarkDown blog 
and some static .html pages. You can generate this into a functioning 
website using the provided `appie.py` python script.

The idea behind this stems from [Permacomputing](http://permacomputing.net)
in which we aim for minimal systems. You can do what you want with Appie but
the example is a very minimal HTML site without any Javascript and other bloat.

The name Appie comes from the initial website generator which was in use at
[z25.org](http://www.z25.org). This second version is a complete minimalized
rewrite.

Usage
-----

1: Clone the repository using git (you can also 
[download the .zip](https://codeload.github.com/sphaero/appie2/zip/refs/heads/master))

```sh
git clone https://github.com/sphaero/appie2
```

2: Install the dependencies (only jinja2, pillow and markdown). Might be best 
to do in a [virtual env](https://docs.python.org/3/tutorial/venv.html)
From appie2's root directory run:

```sh
pip install -r requirements.txt
```

3: Do a first run:

```sh
python3 appie.py
```

You will now have the full website in the '_site' directory.

You can host a webserver using python to preview the site:

```sh
cd _site
python3 -m http.server
```

Now open a browser and go to [http://localhost:8000](http://localhost:8000)

4: Upload the _site directory to a website hosting platform.

The Code
--------

If you managed to generate the provided example site you can now modify it 
to your liking.

The code is quite simple. From the `main()` function we first setup some
parameters we can use while generating the site. You can add/replace 
parameters by creating a simple params.json file containing the 
dictionary of keys and values. 

We then check the command line arguments.

Next first action is to setup the output directory (`_site`) and copy all files
and directories from the `static` directory.

We then walk through the input directory (`content`) and return a nested dictionary
of all entries in there. For example the dictionary could look like this:

```python
{
    '_path': '',
    '_srcpath': './test',
    '_type': 'dir',
    'bla.md': 
    {
          '_ext': '.md',
          '_filename': 'bla',
          '_sitedir': '',
          '_sitepath': 'bla.md',
          '_srcpath': './test/bla.md',
          '_type': 'file'
    },
    'test.png': 
    {
        '_ext': '.png',
        '_filename': 'test',
        '_sitedir': '',
        '_sitepath': 'test.png',
        '_srcpath': './test/test.png',
        '_type': 'file'
    },
    'testdir': 
    {
        '_path': 'testdir',
        '_srcpath': './test/testdir',
        '_type': 'dir',
        'test.jpg': 
        {
            '_ext': '.jpg',
            '_filename': 'test',
            '_sitedir': 'testdir',
            '_sitepath': 'testdir/test.jpg',
            '_srcpath': './test/testdir/test.jpg',
            '_type': 'file'
        },
        'test.md': 
        {
            '_ext': '.md',
            '_filename': 'test',
            '_sitedir': 'testdir',
            '_sitepath': 'testdir/test.md',
            '_srcpath': './test/testdir/test.md',
            '_type': 'file'
        }
    }
}
```

The navigation is then setup from directories found in the content directory.

Finally we recursively run the `parse_dir()` method on the tree
dictionary. So `parse_dir()` is called for every directory entry
in the tree. If an entry is not a directory but a file then
`parse_path()` is called on the entry. Finally for every dir 
we call `generate_index()` which will generate an index.html page 
for the directory.

`parse_path()` parses markdown, plain html, and images. It will
parse them through jinja2 and finally copies to the '_site' dir.
All meta data and params are passed to jinja2. If it can't match 
a file to parse it will just copy it to the '_site' dir.

In `parse_path()` you will also notice a plugin being called. A plugin
is a python file `plugins.py` in which you can add your own code in case
you do not want to modify appie.py. Here's an example plugin which just
prints the file name and directory. 

```python
def match_dir(tree, **params):
    print(tree['_srcpath'])

def match_file(file, **params):
    print(file['_srcpath'])
```
If the `match_dir()` or `match_file()` function returns True appie will
skip the directory or file. Otherwise it will handle it normally.

# Credits

Appie's iteration was inspired by [MAkesite](https://github.com/sunainapai/makesite)

# License

MPLv2 licensed. Do whatever you like with it.

# Support

File an issue or rather a pull request for improvements and bug fixes.

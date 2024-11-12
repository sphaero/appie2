import unittest
import os
from appie import walk_directory, parse_path, parse_dir

from pprint import pprint

rettgt = {
            '.': 
            {
                '_path': '.',
                '_srcpath': './test',
                '_type': 'dir',
                'bla.md': 
                {
                      '_ext': '.md',
                      '_filename': 'bla',
                      '_sitedir': '.',
                      '_sitepath': './bla.md',
                      '_srcpath': './test/bla.md',
                      '_type': 'file'
                },
                'test.png': 
                {
                    '_ext': '.png',
                    '_filename': 'test',
                    '_sitedir': '.',
                    '_sitepath': './test.png',
                    '_srcpath': './test/test.png',
                    '_type': 'file'
                }
            },
            'testdir': 
            {
                '_path': 'testdir',
                '_srcpath': './test/testdir',
                '_type': 'dir',
                'test.jpg': {'_ext': '.jpg',
                          '_filename': 'test',
                          '_sitedir': 'testdir',
                          '_sitepath': 'testdir/test.jpg',
                          '_srcpath': './test/testdir/test.jpg',
                          '_type': 'file'},
             'test.md': {'_ext': '.md',
                         '_filename': 'test',
                         '_sitedir': 'testdir',
                         '_sitepath': 'testdir/test.md',
                         '_srcpath': './test/testdir/test.md',
                         '_type': 'file'}}}



rettgt2 = {'.': {'_path': '.',
       '_srcpath': './test',
       '_type': 'dir',
       'bla.md': {'_ext': '.md',
                  '_filename': 'bla',
                  '_sitedir': '.',
                  '_sitepath': './bla.md',
                  '_srcpath': './test/bla.md',
                  '_type': 'file'},
       'test.png': {'_ext': '.png',
                    '_filename': 'test',
                    '_sitedir': '.',
                    '_sitepath': './test.png',
                    '_srcpath': './test/test.png',
                    '_type': 'file'}},
 'testdir': {'_path': 'testdir',
             '_srcpath': './test/testdir',
             '_type': 'dir',
             'test.jpg': {'_ext': '.jpg',
                          '_filename': 'test',
                          '_sitedir': 'testdir',
                          '_sitepath': 'testdir/test.jpg',
                          '_srcpath': './test/testdir/test.jpg',
                          '_type': 'file'},
             'test.md': {'_ext': '.md',
                         '_filename': 'test',
                         '_sitedir': 'testdir',
                         '_sitepath': 'testdir/test.md',
                         '_srcpath': './test/testdir/test.md',
                         '_type': 'file',
                          'authors': ['Waylan Limberg', 'John Doe'],
                          'base_url': 'http://example.com',
                          'blank-value': '',
                          'content': '<p>This is the first paragraph of the document.</p>',
                          'date': 'October 2, 2007',
                          'img': None,
                          'summary': 'A brief description of my document.',
                          'title': 'My Document',
                          'url': 'testdir/test.html'}}
}


rettgt3 = {'.': {'_path': '.',
       '_srcpath': './test',
       '_type': 'dir',
       'bla.md': {'_ext': '.md',
                  '_filename': 'bla',
                  '_sitedir': '.',
                  '_sitepath': './bla.md',
                  '_srcpath': './test/bla.md',
                  '_type': 'file',
                  'content': '',
                  'img': None,
                  'summary': None,
                  'url': './bla.html'},
       'test.png': {'_ext': '.png',
                    '_filename': 'test',
                    '_sitedir': '.',
                    '_sitepath': './test.png',
                    '_srcpath': './test/test.png',
                    '_type': 'file'}},
 'testdir': {'_path': 'testdir',
             '_srcpath': './test/testdir',
             '_type': 'dir',
             'test.jpg': {'_ext': '.jpg',
                          '_filename': 'test',
                          '_sitedir': 'testdir',
                          '_sitepath': 'testdir/test.jpg',
                          '_srcpath': './test/testdir/test.jpg',
                          '_type': 'file'},
             'test.md': {'_ext': '.md',
                         '_filename': 'test',
                         '_sitedir': 'testdir',
                         '_sitepath': 'testdir/test.md',
                         '_srcpath': './test/testdir/test.md',
                         '_type': 'file',
                         'authors': ['Waylan Limberg', 'John Doe'],
                         'base_url': 'http://example.com',
                         'blank-value': '',
                         'content': '<p>This is the first paragraph of the '
                                    'document.</p>',
                         'date': 'October 2, 2007',
                         'img': None,
                         'summary': 'A brief description of my document.',
                         'title': 'My Document',
                         'url': 'testdir/test.html'}}}


rettgt4 = {'.': {'_path': '.',
       '_srcpath': './test',
       '_type': 'dir',
       'bla.md': {'_ext': '.md',
                  '_filename': 'bla',
                  '_sitedir': '.',
                  '_sitepath': './bla.md',
                  '_srcpath': './test/bla.md',
                  '_type': 'file',
                  'content': '',
                  'img': None,
                  'summary': None,
                  'url': './bla.html'},
       'test.png': {'_ext': '.png',
                    '_filename': 'test',
                    'url': './test.png',
                    '_sitedir': '.',
                    '_sitepath': './test.png',
                    '_srcpath': './test/test.png',
                    '_type': 'file',
                    'md5': 'todo',
                    'mimetype': 'image/png',
                    'size': (200, 200),
                    'thumb': '_site/./test_thumb.jpg',
                    'web': '_site/./test_web.jpg'}},
 'testdir': {'_path': 'testdir',
             '_srcpath': './test/testdir',
             '_type': 'dir',
             'test.jpg': {'_ext': '.jpg',
                          '_filename': 'test',
                          '_sitedir': 'testdir',
                          '_sitepath': 'testdir/test.jpg',
                          '_srcpath': './test/testdir/test.jpg',
                          '_type': 'file',
                          'url': 'testdir/test.jpg',
                          'md5': 'todo',
                          'mimetype': 'image/jpg',
                          'size': (200, 200),
                          'thumb': '_site/testdir/test_thumb.jpg',
                          'web': '_site/testdir/test_web.jpg'},
             'test.md': {'_ext': '.md',
                         '_filename': 'test',
                         '_sitedir': 'testdir',
                         '_sitepath': 'testdir/test.md',
                         '_srcpath': './test/testdir/test.md',
                         '_type': 'file',
                         'authors': ['Waylan Limberg', 'John Doe'],
                         'base_url': 'http://example.com',
                         'blank-value': '',
                         'content': '<p>This is the first paragraph of the '
                                    'document.</p>',
                         'date': 'October 2, 2007',
                         'img': None,
                         'summary': 'A brief description of my document.',
                         'title': 'My Document',
                         'url': 'testdir/test.html'}}}


#ret = walk_directory("./test")[1]
#pprint(ret)
#parse_path(rettgt["testdir"]["test.md"])
#pprint(ret)
#parse_path(ret["."]["bla.md"])
#pprint(ret)
#parse_path(ret["."]["test.png"])
#pprint(ret)
#parse_path(ret["testdir"]["test.jpg"])
#pprint(ret)
def remove_mtime(d):
    #print(d)
    for k in list(d.keys()):
        if type(d[k]) == dict:
            remove_mtime(d[k])
        elif k == "_mtime":
            del d[k]       

class AppieTest(unittest.TestCase):

    def test1_walkdir(self):
        self.maxDiff = None
        d = walk_directory("./test")[1]
        remove_mtime(d)
        self.assertDictEqual(d, rettgt)

    def test2_parse_path(self):
        self.maxDiff = None
        parse_path(rettgt["testdir"]["test.md"])
        self.assertDictEqual(rettgt["testdir"], rettgt2["testdir"])

    def test3_parse_path(self):
        self.maxDiff = None
        parse_path(rettgt["."]["bla.md"])
        self.assertDictEqual(rettgt, rettgt3)

    def test4_parse_dir(self):
        self.maxDiff = None
        parse_dir(rettgt)
        self.assertDictEqual(rettgt, rettgt4)
        def checkdir(d):
            for k,v in d.items():
                if type(v) != dict:
                    continue
                elif v.get("_type") == "dir":
                    checkdir(v)
                else:
                    filepath = os.path.join("_site", v.get("url"))
                    self.assertTrue(os.path.exists(filepath))

        checkdir(rettgt)

if __name__ == '__main__':
    unittest.main()


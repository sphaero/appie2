#!/usr/bin/python3
# 
# Copyright (c) 2015, Arnaud Loonstra, All rights reserved.
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License v3 for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library.

import argparse
import logging
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer
import os
import subprocess

def run_appie():
    command = "{} -u appie.py".format(sys.executable)
    print("running: {} in {}".format(command, cwd))
    try:
        process = subprocess.Popen(command,shell=True,cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

        # Poll process.stdout to show stdout live
        while True:
          output = process.stdout.readline()
          #err = process.stderr.readline()
          if process.poll() is not None:
            break
          if output:
            print(output.strip())
          #if err:
          #  print(err.strip())
        rc = process.poll()
    finally:
        running = False
    return rc

class WatchEventHandler(FileSystemEventHandler):

    timer = None
        
    def on_any_event(self, event, *args, **kwargs):
        if event.event_type != "opened":
            # Cancel the previous timer if it exists
            print(WatchEventHandler.timer)
            if WatchEventHandler.timer:
                WatchEventHandler.timer.cancel()
            # Create a new timer to execute the command after a delay
            WatchEventHandler.timer = Timer(1.0, run_appie)
            WatchEventHandler.timer.start()
        
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dev server for Appie2 Static HTML generator')
    parser.add_argument('-w','--www', help='after generating serve the files through a http server', default=False, required=False, action='store_true')
    parser.add_argument('-p','--port', help='port for the http server', default=8000, type=int, required=False)
    parser.add_argument('-v','--verbose', help="verbose output", default=False, required=False, action='store_true')
    args = vars(parser.parse_args())
    if args.get('verbose'):
        logging.basicConfig(level=logging.DEBUG)
    
    # generate the site
    run_appie()

    # serve files if requested
    if args.get('www'):
        import http.server
        import socketserver
        import os
        import select
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory="./_site", **kwargs)
        
        # setup filesystem watches
        observer = Observer()
        for path in ('./content', './static', './templates'):
            observer.schedule(WatchEventHandler(), path, recursive=True)
        observer.start()
        
        # setup http server
        #os.chdir("_site") #
        PORT = args.get('port')
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            httpd.allow_reuse_address = True
            print("Serving on port {0}...     press CTRL-C to quit".format(PORT))
            httpd.serve_forever()
                    
        observer.stop()
        observer.join()

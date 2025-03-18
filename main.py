#!/usr/bin/python3.10

import logging
import DarwinGroundPeer

from datetime import datetime

import os 
import sys
import rich
import time
import socket
import uuid
import click
import dataclasses
import argparse

from rich import print
from rich import inspect
from rich.pretty import pprint
from rich import box
from rich.align import Align
from rich.progress import Progress
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Prompt
from rich.prompt import Confirm
from rich.text import Text
from rich.markdown import Markdown
from collections import deque

import socketio
from flask import Flask

import threading
import random

VERSION = "snapshot-20221013a"
DEBUG = (socket.gethostname() != "endeavour-ground")

cons = Console(record=True)


import os


logging.basicConfig(format='[%(asctime)s] %(levelname)s %(funcName)-18s   %(message)s', level=logging.DEBUG)
logging.addLevelName(logging.WARNING, "\033[1;31m%s\033[1;0m " % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m   " % logging.getLevelName(logging.ERROR))
logging.addLevelName(logging.INFO, "\u001b[34m%s\033[1;0m    " % logging.getLevelName(logging.INFO))
logging.addLevelName(logging.DEBUG, "\u001b[38;5;109m%s\033[1;0m   " % logging.getLevelName(logging.DEBUG))
_l = logging.getLogger('main')

# ------------------------------------------------
# External event queue system
# ------------------------------------------------


# ------------------------------------------------
# Hack to make Flask stfu with its startup message
# ------------------------------------------------

def secho(text, file=None, nl=None, err=None, color=None, **styles):
    pass

def echo(text, file=None, nl=None, err=None, color=None, **styles):
    pass

click.echo = echo
click.secho = secho

app = Flask(__name__)
sio = socketio.Server(cors_allowed_origins="*")
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

@sio.on('connect')
def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.on('disconnect')
def disconnect(sid):
    print(f"Client disconnected: {sid}")

def run_index():
    shell = str(os.environ['SHELL'])
    shell = shell[shell.rfind("/")+1:]
    os.system(f"lxterminal -e '{shell} -c \"pwd; python3 ~/GUI/index.py; {shell}\" '")

def main():
    with cons.status("Starting Test Ground Station...", spinner="earth"):
        parser = argparse.ArgumentParser(description="Start the Darwin ground station receiver.")
        parser.add_argument('freq', type=float, help='the transceiver frequency in MHz')
        parser.add_argument('debugMode', type=int, help='Start station in debug mode, no radio')

        args = parser.parse_args()

        print(Panel(Text(f"Welcome to the Test Ground Station.", justify="center"), title="[bold blue] GROUND STATION"))

        frequency = float(args.freq)

        cons.log(f"Continuing with {frequency} MHz.")

        debug_mode = int(args.debugMode)


        radio = DarwinGroundPeer.DarwinGroundPeer(cons, frequency, name="TEST", is_debug=debug_mode)

    setup = Prompt.ask("[bold red]Start Set up phase?", choices=["y", "n"])
    if setup == 'y':
        cons.rule("[bold blue]Setting up Connection.")
        radio.setup()
        setup = 'n'
    while True: 
        cons.rule("[bold blue]Listening for Packets.")
        with cons.status(f"[bold white]Searching for rocket on {frequency} mHz... ", spinner="arc"):
            if not debug_mode: 
                threading.Thread(target = radio.listen_packets, daemon=True).start()
                app.run(host='0.0.0.0', port=5000)
        time.sleep(1)
            

if __name__ == "__main__":
    main()

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

import csv
from flask import Flask, redirect, request, Response, url_for, render_template
from queue import Queue

import threading
import random


app = Flask(__name__, template_folder='templates')

data_queue = Queue()


VERSION = "snapshot-20221013a"
DEBUG = (socket.gethostname() != "endeavour-ground")

cons = Console(record=True)


import os

import subprocess
import pickle

# from cmd import Cmd

# # Add this class after the existing imports
# class GroundStationTerminal(Cmd):
#     def __init__(self, radio):
#         super().__init__()
#         self.radio = radio
#         self.prompt = 'Enter LoRa Packet > '
#         self.intro = 'Send packets to the LoRa'

#     def do_send(self, arg):
#         if arg:
#             self.radio.send_packet(arg)
#             print(f"Sent message")
#         else:
#             print("Please provide a command to send")

#     def do_quit(self, arg):
#         """Exit the terminal"""
#         return True

# def start_command_terminal(radio):
#     terminal = GroundStationTerminal(radio)
#     terminal.cmdloop()


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

radio = DarwinGroundPeer.DarwinGroundPeer(cons, 433, name="TEST", is_debug=1)

@app.route('/')
def test():
    if request.headers.get('accept') == 'text/event-stream':
        print("Request for event stream")
        def events():
            while True:
                data = radio.listen_packets_GUI()
                if data is not None:
                    yield f"data: {data}\n\n"
                    with open('./log.csv','w') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(str(data))
        return Response(events(), content_type='text/event-stream')
    return render_template('index.html')

# def run_index():
#     shell = str(os.environ['SHELL'])
#     shell = shell[shell.rfind("/")+1:]
#     os.system(f"lxterminal -e '{shell} -c \"pwd; python3 ~/GUI/index.py; {shell}\" '")


def handle_terminal_commands(radio):
    if not os.path.exists('/tmp/ground_station_pipe'):
        os.mkfifo('/tmp/ground_station_pipe')
    
    while True:
        with open('/tmp/ground_station_pipe', 'rb') as f:
            try:
                command = pickle.load(f)
                # threading.Thread(target=radio.send_packet, args=(str(command),), daemon=True).start()
                if command == "DISARM":
                    # radio.console.log(radio.armed)
                    radio.send_packet(str(command))
                #     print(f"Sent command: {command}")
                # if command == "ARM":
                #     main()
                #     return
                # return
            except EOFError:
                continue
            except Exception as e:
                print(f"Error processing command: {e}")

def launch_terminal():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    terminal_script = os.path.join(script_dir, 'test.py')
    try:
        subprocess.Popen(['lxterminal', '-e', f'python3 {terminal_script}'])
    except FileNotFoundError:
        print("Could not find a suitable terminal emulator")


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
    else:
        radio.launch_GUI()

    command_thread = threading.Thread(target=handle_terminal_commands, args=(radio,), daemon=True)
    command_thread.start()

    # Launch the terminal interface in a new window
    launch_terminal()
    
    while True: 
        cons.rule("[bold blue]Listening for Packets.")
        with cons.status(f"[bold white]Searching for rocket on {frequency} mHz... ", spinner="arc"):
            if not debug_mode: 
                # threading.Thread(target = radio.listen_packets, daemon=True).start()
                if radio.GUI:
                    app.run(host='0.0.0.0', port=8000)
                else:
                    radio.listen_packets()
        time.sleep(1)
            

if __name__ == "__main__":
    main()

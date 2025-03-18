from curses import raw
from dataclasses import dataclass
from queue import Queue
import time
import logging
import sys
import array
from rich import print
from rich.pretty import pprint
from rich import inspect

from rich.prompt import Prompt
from rich.prompt import Confirm

from threading import Thread, Lock
from main import sio, run_index
import socketio

flight_states = ["INITIALIZING", "READY", "BOOSTING", "COASTING", "APOGEE", "DESCENT", "LANDING", "DONE"]
packet_types = ["", "state", "acc"]
endeavour_pkt = 0xED

rocket_addr = 17

sensor_ok = 0x10
sensor_not_ok = 0x13
connection_check = 0x50
ready_signal = 0x61

mutex = Lock()
send_signal = False

try: 
    import digitalio
    from digitalio import DigitalInOut, Direction, Pull
    import board
    import adafruit_rfm9x
    import busio
except NotImplementedError as e:
    print(f"NotImplementedError! Maybe not running in right env? {e}")
except ModuleNotFoundError as e:
    print(f"ModuleNotFoundError! Maybe not running in right env? {e}")

import socket
import binascii
import random

class DarwinGroundPeer:
    """Singleton class which holds connection state to a Darwin rocket. """

    def __init__(self, console, frequency: float, name="Test", connection_timeout=50, is_debug=False, disable_timeout=False):
        """Constructor."""

        self._name = name
        self.frequency = frequency
        self.last_datagram_time = time.time()
        self.connection_timeout = connection_timeout
        self.last_time_offset = 0
        self.is_debug = is_debug
        self.disable_timeout = disable_timeout
        self.queued_radio_frames = []
        self.has_tx_window = False
        self.connected = False
        self.GUI = False

        # Initialise other variables.
        self._l = logging.getLogger("DarwinGroundPeer")
        self.console = console

        try:
            # Create the I2C interface.
            self.i2c = busio.I2C(board.SCL, board.SDA)

            # Configure LoRa Radio
            CS = DigitalInOut(board.CE1)
            RESET = DigitalInOut(board.D25)
            spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
            self.rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, frequency)
            self.rfm9x.tx_power = 23
            self.rfm9x.spreading_factor = 7
            self.rfm9x.high_power = True
            self.rfm9x.signal_bandwidth = 125000
            self.rfm9x.enableconsolerc = True
            self.rfm9x.xmit_timeout = 5
            self.rfm9x.node = 29
            self.rfm9x.destination = rocket_addr
            #self.rfm9x.ack_delay = 0.1
            #self.rfm9x.ack_retries = 2
            #self.rfm9x.ack_wait = 0.2
        except Exception as e:
            if self.is_debug:
                self.console.print(":cross_mark: Failed to initialise radio (ignoring as we're in debug)", style="bold dark_orange3")
            else:
                self.console.log(e)
                self.console.print(":cross_mark: Failed to initialise radio, abort.", style="bold red")
                sys.exit()

    def check_connection(self):
        global send_signal
        start = time.time()
        finished = False
        while(not finished):
             if time.time() - start > 10:
                 with mutex:
                     if not send_signal:
                        self.console.log("Checking connection with radio ....")
                        self.rfm9x.send_with_ack(connection_check.to_bytes(connection_check, 'little'))
                     else:
                         finished = True 
                 start = time.time()

    def send_signal_menu(self):

        confirmed = False
        global send_signal
        while(not confirmed):
            self.console.input("Send ready signal?")
            password = Prompt.ask("Type in Endeavour to confirm: ", password=True)
            if password == "endeavour":
                confirmed = True
                with mutex:
                    send_signal = True
                    self.console.log("Sending [red]READY SIGNAL[/red] entering packet listening mode!")
                    self.rfm9x.send_with_ack(connection_check.to_bytes(ready_signal, 'little'))
                 # if sensors ok radio will now wait on signal from gs when its nearly time for launch, while waiting will exchange messages back and forth to make sure connection is still up.
                return True 

        
    def connect(self):
        while True:
            self.rfm9x.send(0xed.to_bytes(1, "little") + ("ARM").encode("ascii"))
            packet = self.rfm9x.receive(timeout=10)
            while packet is None or packet[0] != 0xed:
                self.console.log("Nothing...")
                self.rfm9x.send(0xed.to_bytes(1,"little") + ("ARM").encode("ascii"))
                packet = self.rfm9x.receive(timeout=10)
            break
        conf = packet[1:].decode("ascii")
        prmpt = Prompt.ask(conf, choices=["y", "n"])
        if prmpt == "y":
            prmpt = Prompt.ask("Launch GUI?", choices=["y", "n"])
            self.rfm9x.send(0xed.to_bytes(1, "little") + ("y").encode("ascii"))
            self.console.log("Connected to rocket")
            self.connected = True
            if prmpt == "y":
                self.GUI = True
        else:
            self.rfm9x.send(0xed.to_bytes(1, "little") + ("n").encode("ascii"))
            self.console.log("Failed to connect to rocket")
            # elif packet[0] != self.rfm9x.node:
            #     self.console.log("Received packet not addressed to us.")
            #     self.console.log(self.rfm9x.node)
            # elif packet[0] == self.rfm9x.node and packet[1] == rocket_addr and packet[4] == 237 :
            #     self.console.log("Got init packet from radio")
            #     connected = True
            # elif connected and len(packet) != 5:
            #     self.console.log("finished connecting")
            #     return packet
            # else:
            #     self.console.log(packet)

    def printIMU(self, packet):
        #8 bytes in a double, want 6 doubles, dont want headers
        if len(packet) != 48:
            self.console.log(len(packet))
            self.console.log("Invalid IMU packet")
        else :
            doubles = array.array('d', packet)
            self.console.log("ax: " + str(doubles[0]) + " ay: " + str(doubles[1]) + " az: " + str(doubles[2]))
            self.console.log("gx: " + str(doubles[3]) + " gy: " + str(doubles[4]) + " gz: " + str(doubles[5]))

    def printBaro(self, packet):
        #4 bytes in a float, want 6 doubles, dont want headers
        if len(packet) != 24:
            self.console.log(len(packet))
            self.console.log("Invalid Baro packet")
        else :
            readings = array.array('f', packet)
            self.console.log("temperature " + str(readings[0]) + " pressure : " + str(readings[1]))
            self.console.log("temperature " + str(readings[2]) + " pressure : " + str(readings[3]))
            self.console.log("temperature " + str(readings[4]) + " pressure : " + str(readings[5]))


    def imu_loop(self, packet):
        while True:
            while packet is None:
                packet = self.rfm9x.receive(with_ack=True)
            try:
                self.printIMU(packet[:48])
                self.printIMU(packet[48:96])
                self.printIMU(packet[96:])          
            except Exception as e:
                packet = None
                self.console.log(packet)
                self.console.log(e)
            else:
                return

    def baro_loop(self, packet):
        while True:
            while packet is None:
                packet = self.rfm9x.receive(with_ack=True)
            try:
                self.printBaro(packet)
            except Exception as e:
                packet = None
                self.console.log(packet)
                self.console.log(e)
            else:
                return

    
    def imu_set_up(self, packet):
        while True:
            try:
                imu_init = packet[:3].decode("ascii")
                self.console.log(imu_init)
            except Exception as e:
                self.console.log(e)
                self.console.log(packet)
                imu_init = "none"
                packet = None
            if imu_init == "YES":
                self.console.log("IMU initialized") 
                packet = self.rfm9x.receive(with_ack=True)
                self.imu_loop(packet)
            elif imu_init == "NOO":
                self.console.log("IMU not initialised")
            else :
                self.console.log("invalid packet")
                self.console.log(packet)
            
            if imu_init != "none":
                ok = False
                p = ""
                while(not ok):
                    p = Prompt.ask("IMU OK?", choices=["yes", "no"])
                    password = Prompt.ask("Type in ok to confirm: ", password=True)
                    if password == "ok":
                        ok = True
                        if p == "yes":
                            self.rfm9x.send_with_ack(sensor_ok.to_bytes(1, 'little'))
                            packet = self.rfm9x.receive(with_ack=True)
                            return packet
                        elif p == "no":
                            self.rfm9x.send_with_ack(sensor_not_ok.to_bytes(1, 'little'))
            packet = self.rfm9x.receive(with_ack=True)

    def baro_set_up(self, packet):
        while True:
            try:
                baro_init = packet[:3].decode("ascii")
                self.console.log(baro_init)
            except Exception as e:
                self.console.log(e)
                self.console.log(packet)
                baro_init = "none"
                packet = None
            if baro_init == "YES":
                self.console.log("Barometer initialized") 
                packet = self.rfm9x.receive(with_ack=True)
                self.baro_loop(packet)
            elif baro_init == "NOO":
                self.console.log("Barometer not initialised")
            else :
                self.console.log("invalid packet")
                self.console.log(packet)
            
            if baro_init != "none":
                ok = False
                p = ""
                while(not ok):
                    p = Prompt.ask("BAROMETER OK?", choices=["yes", "no"])
                    password = Prompt.ask("Type in ok to confirm: ", password=True)
                    if password == "ok":
                        ok = True
                        if p == "yes":
                            self.rfm9x.send_with_ack(sensor_ok.to_bytes(1, 'little'))
                            packet = self.rfm9x.receive(with_ack=True)
                            return packet
                        elif p == "no":
                            self.rfm9x.send_with_ack(sensor_not_ok.to_bytes(1, 'little'))
            packet = self.rfm9x.receive(with_ack=True)


     
    #wait for sensor packets: IMU, Baro, GPS
    def get_sensors(self, packet):
        packet = self.imu_set_up(packet)
        packet = self.baro_set_up(packet)
         
    def setup(self):
        self.connect()
        # self.console.log("Waiting for message from rocket...")
        # self.get_sensors(packet)
        # t1 = Thread(target=self.check_connection)
        # t2 = Thread(target=self.send_signal_menu)
        # t1.start()
        # t2.start()
        # t1.join()
        # t2.join()

             
    def handle_endeavour_packet(self, payload, packet_type, packet):
        if packet_types[packet_type] == "state":
            if payload[0] < len(flight_states):
                state = flight_states[payload[0]]
                self.console.rule("[bold green]CURRENT STATE: " + state)

            else :
                self.console.log(f"Invalid state: {payload[0]}")
          
        elif packet_types[packet_type] == "acc":
            doubles = array.array('d', packet)
            self.console.log("gx: " + str(doubles[0]) + " gy: " + str(doubles[1]) + " gz: " + str(doubles[2]))
                
        else:
            self.console.log("hmmm")
            self.console.log(packet)
    
    def listen_packets(self):
        if self.GUI:
            run_index()
            
        while True : 
            self.console.log("Waiting for radio packet...")
            #txt = self.console.export_text()
            #f = open("test.txt", "a")
            #f.write(txt)
            #f.close()

            packet = self.rfm9x.receive(with_header=False, timeout=5)

            if packet is None:
                self.console.log("No packet received, maybe another time...")
                #continue

            elif len(packet) > 2 and packet[0] == endeavour_pkt: # Want the Endeavour identifier, packet type and payload, 3 bytes min
                # if packet[1] < len(packet_types):
                #     self.handle_endeavour_packet(packet[2:], packet[1], packet)
                # else:
                #     self.console.log(f"Invalid packet type: {int(packet[1])}")
                decoded = packet[1:].decode("ascii")
                self.console.log(decoded)

                if(self.GUI):
                    sio.emit("rocket_data", decoded)
                  
            elif packet[0] != endeavour_pkt:
                self.console.log(packet)
                self.console.log("Received non Endeavour packet")
            elif len(packet) <= 1:
                self.console.log(packet)
                self.console.log("Received no payload data")
            else:
                self.console.log("Invalid packet")
                self.console.log(packet)



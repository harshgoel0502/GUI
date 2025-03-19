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

data_packet = ("0," * 30)[:-1]

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

        self.no_packets = 0
        self.ms_since_start = 0

        self.gX, self.gY, self.gZ = 0, 0, 0
        self.aX, self.aY, self.aZ = 0, 0, 0
        self.mX, self.mY, self.mZ = 0, 0, 0
        self.qX, self.qY, self.qZ, self.qW = 0, 0, 0, 0
        self.imuTemp = 0
        self.baroPress, self.aglAlt, self.baroTemp, self.baroVel = 0, 0, 0, 0
        self.gpsLat, self.gpsLong, self.gpsAlt, self.gpsSats, self.gpsSpd, self.gpsHdg = 0, 0, 0, 0, 0, 0

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
            self.connect()

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
    
    def log(self, value, type):
        self.console.log(type + ": " + value)
        return value

             
    def handle_endeavour_packet(self, payload):
        values = payload.split(",")
        self.no_packets = self.log(values[0], "No. of packets")
        self.ms_since_start = self.log(values[1], "Time since start")
        self.gx, self.gy, self.gz = self.log(values[2:5], "Gyro")
        self.ax, self.ay, self.az = self.log(values[5:8], "Accel")
        self.mx, self.my, self.mz = self.log(values[8:11], "Mag")
        self.qx, self.qy, self.qz, self.qw = self.log(values[11:15], "Quat")
        self.imu_temp = self.log(values[15], "IMU Temp")
        self.baro_press = self.log(values[16], "Pressure")
        self.agl_alt = self.log(values[17], "Altitude")
        self.baro_temp = self.log(values[18], "Temperature")
        self.baro_vel = self.log(values[19], "Velocity")
        self.gps_lat, self.gps_long = self.log(values[20:22], "GPS Coordinates:")
        self.gps_alt = self.log(values[22], "GPS Altitude")
        self.gps_sats = self.log(values[23], "GPS Sats")
        self.gps_spd = self.log(values[24], "GPS Speed")
        self.gps_hdg = self.log(values[25], "GPS")

    
    def listen_packets(self):
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
                self.handle_endeavour_packet(decoded)

            elif packet[0] != endeavour_pkt:
                self.console.log(packet)
                self.console.log("Received non Endeavour packet")
            elif len(packet) <= 1:
                self.console.log(packet)
                self.console.log("Received no payload data")
            else:
                self.console.log("Invalid packet")
                self.console.log(packet)
        
    def listen_packets_GUI(self):
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
                return (decoded + ",0,0,0,0")
            elif packet[0] != endeavour_pkt:
                self.console.log(packet)
                self.console.log("Received non Endeavour packet")
            elif len(packet) <= 1:
                self.console.log(packet)
                self.console.log("Received no payload data")
            else:
                self.console.log("Invalid packet")
                self.console.log(packet)

            return None



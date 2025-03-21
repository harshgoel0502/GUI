# import serial.tools.list_ports as port_list
# ports = list(port_list.comports())
# for p in ports:
#     print (p)


# import numpy as np

# timestamp = [1,2,3,4,5,6]
# print(timestamp)
# delta_time = np.diff(timestamp, prepend=timestamp[0])
# print(delta_time)

#!/usr/bin/python3.10

from cmd import Cmd
import sys
import pickle

class GroundStationTerminal(Cmd):
    def __init__(self):
        super().__init__()
        self.prompt = 'Enter LoRa Packet > '
        self.intro = 'Send packets to the LoRa'

    def do_send(self, arg):
        if arg:
            print(f"Sending: {arg}")
            # Write command to the pipe
            with open('/tmp/ground_station_pipe', 'wb') as f:
                pickle.dump(arg, f)
        else:
            print("Please provide a command to send")

    def do_quit(self, arg):
        """Exit the terminal"""
        return True

if __name__ == "__main__":
    terminal = GroundStationTerminal()
    terminal.cmdloop()
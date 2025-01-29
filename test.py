# import serial.tools.list_ports as port_list
# ports = list(port_list.comports())
# for p in ports:
#     print (p)
import numpy as np

timestamp = [1,2,3,4,5,6]
print(timestamp)
delta_time = np.diff(timestamp, prepend=timestamp[0])
print(delta_time)
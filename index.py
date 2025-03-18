import itertools
import time
from flask import Flask, redirect, request, Response, url_for, render_template
import numpy as np
import serial
import math
import socketio

from queue import Queue

app = Flask(__name__, template_folder='templates')

serial_used = False

sio = socketio.Client()

data_queue = Queue()

@sio.on('rocket_data')
def on_message(data):
    data_queue.put(data)

# try:
#     serial_port = '/dev/ttyUSB0'  
#     baud_rate = 115200
#     ser = serial.Serial(serial_port, baud_rate)
#     serial_used = True
# except:
#     f = open("STARSCOUTDATA(1).txt", "r")
#     serial_used = False

# lineNumber = 0

@app.route('/')
def test():
    # if request.method == 'GET':
    if request.headers.get('accept') == 'text/event-stream':
        def events():
            lineNumber = 0
            # for i, c in enumerate(itertools.cycle('\|/-')):
            #     yield "data: %s %d\n\n" % (c, i)
            #     time.sleep(.1)
            # temp = 60
            while True:
                if(data_queue.qsize() > 0):
                    data = data_queue.get()
                    yield "data: %s\n\n" % data
                # if(serial_used):
                #     if ser.in_waiting > 0:
                #         # print(ser.readline().decode('utf-8'))
                #         line = ser.readline().decode('utf-8').strip()
                #         if line:
                #             # Emit the data to connected clients
                #             print(f"{line}")
                #             yield "data: %s\n\n" % line
                #     time.sleep(0.04)
                # else:
                #     line = f.readline().strip()
                #     if line:
                #         values = line.split(" ")
                #         lineAsString = str(lineNumber) + ','
                #         lineNumber += 1
                #         lineAsString += str(values[len(values) - 1]) + ','
                #         lineAsString += str(values[11]) + ','
                #         lineAsString += str(values[12]) + ','
                #         lineAsString += str(values[13]) + ','
                #         lineAsString += str(values[1]) + ','
                #         lineAsString += str(values[2]) + ','
                #         lineAsString += str(values[3]) + ','
                #         lineAsString += str(values[8]) + ','
                #         lineAsString += str(values[9]) + ','
                #         lineAsString += str(values[10]) + ','
                #         lineAsString += "0,0,0,0,"
                #         lineAsString += str(values[0]) + ','
                #         lineAsString += str(values[4]) + ','
                #         lineAsString += "0,0,0,"
                #         sinValue = 55.946726 + 0.007 * math.sin(math.radians((lineNumber/10)%360))
                #         cosValue = -3.180958 + 0.007 * math.cos(math.radians((lineNumber/10)%360))
                #         lineAsString += (str(sinValue)) + ','
                #         lineAsString += (str(cosValue)) + ','
                #         lineAsString += "0,0,0,0,0,0,0,0"
                #         print(f"{lineAsString}")
                #         yield "data: %s\n\n" % lineAsString
                #     time.sleep(0.05)
        return Response(events(), content_type='text/event-stream')
    return render_template('index.html')

if __name__ == '__main__':
    sio.connect('http://localhost:5000')
    app.run(host='0.0.0.0', port='8000', debug=True)
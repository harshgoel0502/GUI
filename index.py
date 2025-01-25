import itertools
import time
from flask import Flask, redirect, request, Response, url_for, render_template
import numpy as np
import serial
# import socketio

app = Flask(__name__, template_folder='templates')

serial_port = '/dev/ttyUSB0'  
baud_rate = 115200
ser = serial.Serial(serial_port, baud_rate)

@app.route('/')
def test():
    # if request.method == 'GET':
    if request.headers.get('accept') == 'text/event-stream':
        def events():
            # for i, c in enumerate(itertools.cycle('\|/-')):
            #     yield "data: %s %d\n\n" % (c, i)
            #     time.sleep(.1)
            temp = 60
            while True:
                
                if ser.in_waiting > 0:
                    # print(ser.readline().decode('utf-8'))
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        # Emit the data to connected clients
                        print(f"{line}")
                        yield "data: %s\n\n" % line
                    time.sleep(0.04)
        return Response(events(), content_type='text/event-stream')
    return render_template('test2.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8000', debug=True)
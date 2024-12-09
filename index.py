import itertools
import time
from flask import Flask, redirect, request, Response, url_for, render_template
import numpy as np

app = Flask(__name__, template_folder='templates')

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
                # temp = ((np.random.random_sample() * 20) + 100)
                temp += 1.2 + (np.random.random_sample() * 4) - 3
                if temp > 135:
                    temp = 90
                # if int(temp) == 112:
                #     temp = None
                yield "data: %s\n\n" % temp
                # if temp == None:
                #     time.sleep(20)
                time.sleep(.02)
        return Response(events(), content_type='text/event-stream')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8000', debug=True)
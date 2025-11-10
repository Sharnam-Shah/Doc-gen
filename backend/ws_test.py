import json
import time
from websocket import create_connection

ws_url = 'ws://localhost:8000/ws/document/6910a447ba10e245c89b8e70/'
print('Connecting to', ws_url)
try:
    ws = create_connection(ws_url, timeout=10)
    print('Connected')
    msg = {
        'type': 'comment',
        'user': 'AutomatedTester',
        'content': 'Hello from automated WS test',
        'position': None
    }
    ws.send(json.dumps(msg))
    print('Sent:', msg)
    # Receive for a few seconds
    start = time.time()
    while time.time() - start < 5:
        try:
            m = ws.recv()
            print('Received:', m)
        except Exception as e:
            # no more messages right now
            # print('recv error', e)
            break
    ws.close()
    print('Closed')
except Exception as e:
    print('Connection failed:', e)

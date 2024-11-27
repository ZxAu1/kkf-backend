
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import supabase
from flask_cors import CORS
from asyncua import Client
import asyncio
import threading
import logging
import queue
opc_queue = queue.Queue()
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

SUPABASE_URL = "https://rtuzjfbjcqovplkxhorx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ0dXpqZmJqY3FvdnBsa3hob3J4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzIzMzA5NjMsImV4cCI6MjA0NzkwNjk2M30.Aa58wddnRy7pKcskuw1Nlh9tDHLkHCQX_iZPbkh4fzU"
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
CORS(app, resources={r"/*": {"origins": "*"}})
latest_opc_data = None

@app.route("/")
def index():
    return "Hello, Flask!"

@app.route('/get_users', methods=['GET'])
def get_users():
    response = supabase_client.table('users').select('*').execute()
    return jsonify(response.data), 200

@app.route('/get_crane', methods=['POST'])
def get_crane():
    data = request.json
    site_id = data.get('site_id')
    if not site_id: 
        return jsonify({'error': 'site_id is required'}), 400
    response = supabase_client.table('crane').select('*').eq('site_id', site_id).execute()
    if not response.data:
        return jsonify({'error': 'No cranes found for the given site_id'}), 404
    return jsonify(response.data), 200

@app.route('/check_activate', methods=['POST'])
def check_activate():
    data = request.json
    crane_id = data.get('crane_id')
    if not crane_id:
        return jsonify({'error': 'crane_id is required'}), 400
    response = supabase_client.table('camera').select('*').eq('crane_id', crane_id).execute()
    if not response.data:
        return jsonify({'error': 'No cameras found for the given crane_id'}), 404
    camera = response.data[0]
    if camera['camera_activate'] != 1:
        return jsonify({'error': 'Camera not activated'}), 200
    return jsonify({'status': 'Camera activated'}), 200

@app.route('/get_bank', methods=['POST'])
def get_bank():
    data = request.json
    crane_id = data.get('crane_id')
    if not crane_id:
        return jsonify({'error': 'crane_id is required'}), 400
    response = supabase_client.table('bank').select('*').eq('crane_id', crane_id).execute()
    if not response.data:
        return jsonify({'error': 'No banks found for the given crane_id'}), 404
    return jsonify(response.data), 200

@app.route('/get_level', methods=['POST'])
def get_level():
    data = request.json
    bank_id = data.get('bank_id')
    if not bank_id:
        return jsonify({'error': 'bank_id is required'}), 400
    response = supabase_client.table('bank').select('*').eq('bank_id', bank_id).execute()
    if not response.data:
        return jsonify({'error': 'No levels found for the given bank_id'}), 404
    return jsonify(response.data), 200

@app.route('/serway_palletId', methods=['POST'])
def serway_palletId():
    data = request.json
    return jsonify({'status': 'success'}), 200

@app.route('/crane-log', methods=['POST'])
def crane_log():
    data = request.json
    if not data:
        return jsonify({'status': 0}), 404
    return jsonify({'status': 1}), 200

@app.route('/serway_bank', methods=['POST'])
def serway_bank():
    data = request.json
    return jsonify({'status': 'success'}), 200

@socketio.on('send_data')
def handle_send_data(data):
    response_data = {
        "message": "Data received successfully",
        "received_data": data
    }
    emit('receive_data', response_data)
def start_opc_thread():
    opc_thread = threading.Thread(target=opc_worker, daemon=True)
    opc_thread.start()
    
def opc_worker():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(async_opc())

async def async_opc():
    while True:
        try:
            async with Client(url='opc.tcp://191.20.80.102:49320', timeout=10) as client:
                while True:
                    dist_x = await client.get_node('ns=2;s=LINE04-MP.ASRS.Distance_X').read_value()
                    dist_y = await client.get_node('ns=2;s=LINE04-MP.ASRS.Distance_Y').read_value()

                    data = {"dist_x": str(dist_x), "dist_y": str(dist_y)}
                    opc_queue.put(data)  # ใส่ข้อมูลใน Queue
                    await asyncio.sleep(0.4)

        except Exception as e:
            await asyncio.sleep(5)  # Wait before retrying
def socketio_worker():
    while True:
        try:
            data = opc_queue.get(timeout=1)  # รอข้อมูลจาก Queue
            socketio.emit('receive_data', data)
        except queue.Empty:
            continue  # ไม่มีข้อมูลให้ทำงานต่อ

if __name__ == '__main__':
    threading.Thread(target=opc_worker, daemon=True).start()
    threading.Thread(target=socketio_worker, daemon=True).start()

    # Run Flask-SocketIO
    socketio.run(app, host='191.20.207.115', port=5339, debug=True, use_reloader=False)
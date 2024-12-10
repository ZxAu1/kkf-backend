
from flask import Flask, request, jsonify, Response, render_template, send_from_directory, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
from supabase import create_client, Client
from flask_cors import CORS
from asyncua import Client, ua
import asyncio
import threading
import logging
import queue
import os
import cv2
from ultralytics import YOLO
from datetime import datetime, timezone
import time
from functools import wraps
opc_queue = queue.Queue()
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
 
 
CORS(app, resources={r"/*": {"origins": "*"}})
latest_opc_data = None
current_opc_path = None
output_dir = r"D:\work\kkf\kkf-backend-old\app\static\KKFMiniLoad"
yolo_model = YOLO(r"D:\work\kkf\kkf-backend-old\best.pt")

# API ENDPOINT 
from app.config.supabase_client import supabase

# @app.route('/iho', methods=['POST'])
# @app.route('/serway_bank', methods=['POST'])
# def serway_bank():
#     data = request.get_json()
#     print("Received data:", data)  # Debugging line
#     path_opc = data.get('path_opc')
#     bay = data.get('bay')
#     level = data.get('level')
#     if data and 'bank' in data:
#         try:
#             # ใช้ timezone-aware UTC datetime
#             current_datetime = datetime.now(timezone.utc)

#             # บันทึกข้อมูลลงใน Supabase
#             response = supabase.table('input_report').insert({
#                 'crane_id': data.get('crane_id'),
#                 'bank': data.get('bank'),
#                 'bay': data.get('bay'),
#                 'level': data.get('level'),
#                 'path_opc': data.get('path_opc'),
#                 'site_id': data.get('site_id'),
#                 'date_time': current_datetime.isoformat()  # ISO 8601 format
#             }).execute()

#             # ตรวจสอบว่าบันทึกสำเร็จ
#             if response.data:
#                 inserted_data = response.data[0]  # Supabase จะคืนข้อมูลของ row ที่เพิ่งบันทึก
#                 inserted_id = inserted_data.get('in_id')  # ดึง id ของ row ที่บันทึก
                

#                 # เรียกใช้ฟังก์ชัน async_opc_write_iho
#                 asyncio.run(async_opc_write_iho(path_opc, bay, level))

#                 return jsonify({
#                     "message": "Data inserted successfully",
#                     "inserted_id": inserted_id,
#                     "data": inserted_data
#                 }), 201
#             else:
                
#                 return jsonify({"error": "Failed to insert data", "details": response}), 500
#         except Exception as e:
            
#             return jsonify({"error": "Server error", "details": str(e)}), 500
#     else:
#         return jsonify({"error": "Invalid data"}), 400

# async def async_opc_write_iho(path_opc , bay , level):

#     try:
#         bay = int(bay)
#         level = int(level)
#         async with Client(url='opc.tcp://191.20.80.102:49320', timeout=10) as client:
           
#             node_bay = client.get_node(f'ns=2;s={path_opc}.ASRS.D0131')
#             await node_bay.write_value(ua.DataValue(ua.Variant(bay , ua.VariantType.UInt32)))
#             logger.info(f"Successfully wrote value to node {node_bay}")

            
#             node_level = client.get_node(f'ns=2;s={path_opc}.ASRS.D0133')
#             await node_level.write_value(ua.DataValue(ua.Variant(level, ua.VariantType.Int16)))
#             logger.info(f"Successfully wrote value to node {node_level}")

            
#             node_cmd = client.get_node(f'ns=2;s={path_opc}.ASRS.D0148')
#             await node_cmd.write_value(ua.DataValue(ua.Variant(10, ua.VariantType.Int16)))
#             logger.info(f"Successfully wrote value 10 to node {node_cmd}")

#     except Exception as e:
#         logger.error(f"Failed to write value to node: {str(e)}", exc_info=True)

@app.route('/command_opc', methods=['POST'])
async def command_opc():
    try:
        data = request.get_json()
        path_opc = data.get("path_opc")
        command = data.get("command")
        command_number = int(command)

        async with Client(url='opc.tcp://191.20.80.102:49320', timeout=10) as client:
            node_bay = client.get_node(f'ns=2;s={path_opc}.ASRS.D0148')
            await node_bay.write_value(ua.DataValue(ua.Variant(command_number, ua.VariantType.Int16)))
            logger.info(f"Successfully wrote value to node {node_bay}")

        return jsonify({"status": "success", "message": f"Command '{command}' processed"})
    except Exception as e:
        logger.error(f"Failed to write value to node: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/static/<path:filename>')
def serve_static2(filename):
    print(f"Serving file: {filename}")
    print(f"Full path: {output_dir}")
    try:
        return send_from_directory(output_dir, filename)
    except FileNotFoundError:
        return "File not found", 404
        
@app.route("/<path:filename>")
def serve_static(filename):
    print(f"Serving file: {filename}")
    print(f"Full path: {output_dir}")
    try:
        return send_from_directory(output_dir, filename)
    except FileNotFoundError:
        return "File not found", 404

@app.route("/process_video", methods=["POST"])
def process_video():
    try:
        # Get input_id from request
        data = request.get_json()
        input_id = data.get('input_id')
        ids = int(input_id)
        print(ids)
        if not input_id:
            return jsonify({"error": "Input ID is required."}), 400

        # Video path (RTSP stream)
        # video_path = r'D:\automotionworks\kkf\kkf-backend\app\static\vid\test.mp4'
        video_path = 'rtsp://admin:@mwte@mp@55@192.168.202.163/Streaming/channels/101'
        # Initialize video capture
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return jsonify({"error": "Cannot open video stream."}), 500

        # Read the first frame
        success, frame = cap.read()
        if not success:
            cap.release()
            return jsonify({"error": "Cannot fetch the first frame."}), 500

        # Get frame dimensions
        frame_height, frame_width = frame.shape[:2]
        centerline_x = frame_width // 2

        # Run YOLO model
        results = yolo_model(frame, conf=0.8, iou=0.7, verbose=False)

        # Extract detection results
        obb_coordinates = results[0].boxes.xyxy.cpu().numpy()
        cls = results[0].boxes.cls.cpu().numpy()
        confidences = results[0].boxes.conf.cpu().numpy()

        # Define colors and labels
        colors = {0: (255, 0, 0), 1: (0, 255, 0), 2: (0, 0, 255), 3: (255, 255, 0)}
        class_names = {0: "Barcode", 1: "Information", 2: "Net", 3: "Type"}

        # Draw centerline
        cv2.line(frame, (centerline_x, 0), (centerline_x, frame_height), (0, 255, 255), 2)

        # Initialize variables for barcode image
        barcode_filename = None
        has_barcode = False

        # Process detected objects
        for bbox, class_id, confidence in zip(obb_coordinates, cls, confidences):
            x1, y1, x2, y2 = map(int, bbox)
            color = colors.get(int(class_id), (255, 255, 255))
            label = class_names.get(int(class_id), "Unknown")
            confidence_percentage = f"{confidence * 100:.2f}%"

            # Draw bounding box and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"{label} ({confidence_percentage})", 
                       (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Handle Net class
            if class_id == 2:
                bbox_center_x = (x1 + x2) // 2
                pixel_shift = bbox_center_x - centerline_x
                shift_direction = "Left" if pixel_shift < 0 else "Right" if pixel_shift > 0 else "Centered"
                formatted_pixel_shift = abs(pixel_shift)
                
                cv2.putText(frame, f"Shift: {shift_direction} ({formatted_pixel_shift} px)",
                           (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                cv2.line(frame, (bbox_center_x, 0), (bbox_center_x, frame_height), (0, 0, 255), 2)

            # Handle Barcode class
            if class_id == 0:
                has_barcode = True
                barcode_image = frame[y1:y2, x1:x2]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                barcode_filename = f"barcode_{timestamp}.jpg"
                barcode_path = os.path.join(output_dir, barcode_filename)
                cv2.imwrite(barcode_path, barcode_image)

        # Save annotated frame
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        annotated_filename = f"Annotated_{timestamp}.jpg"
        annotated_frame_path = os.path.join(output_dir, annotated_filename)
        cv2.imwrite(annotated_frame_path, frame)

        # Release resources
        cap.release()

        # Save to database
        try:
            response = supabase.table('image_processing').insert({
                'in_id': ids,
                'annotated_image': annotated_filename,
                'barcode_image': barcode_filename if has_barcode else None,
                'date_time': datetime.now(timezone.utc).isoformat(),
                'shift_direction':shift_direction,
                'formatted_pixel_shift':formatted_pixel_shift
            }).execute()

            return jsonify({
                "message": "Process completed successfully",
                "annotated_image": annotated_filename,
                "barcode_image": barcode_filename if has_barcode else None,
                "input_id": response.data[0]['in_id'] if response.data else None
            }), 200

        except Exception as e:
            print("Error saving to database:", str(e))
            return jsonify({"error": "Database error", "details": str(e)}), 500

    except Exception as e:
        print("Error processing video:", str(e))
        return jsonify({"error": "Processing error", "details": str(e)}), 500

@app.route('/get_users', methods=['GET'])
def get_users():
    response = supabase.table('users').select('*').execute()
    return jsonify(response.data), 200

@app.route('/get_crane', methods=['POST'])
def get_crane():
    data = request.json
    site_id = data.get('site_id')
    if not site_id: 
        return jsonify({'error': 'site_id is required'}), 400
    response = supabase.table('crane').select('*').eq('site_id', site_id).execute()
    if not response.data:
        return jsonify({'error': 'No cranes found for the given site_id'}), 404
    return jsonify(response.data), 200

@app.route('/check_activate', methods=['POST'])
def check_activate():
    data = request.json
    crane_id = data.get('crane_id')
    if not crane_id:
        return jsonify({'error': 'crane_id is required'}), 400
    response = supabase.table('camera').select('*').eq('crane_id', crane_id).execute()
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
    response = supabase.table('bank').select('*').eq('crane_id', crane_id).execute()
    if not response.data:
        return jsonify({'error': 'No banks found for the given crane_id'}), 404
    return jsonify(response.data), 200

@app.route('/get_level', methods=['POST'])
def get_level():
    data = request.json
    bank_id = data.get('bank_id')
    if not bank_id:
        return jsonify({'error': 'bank_id is required'}), 400
    response = supabase.table('bank').select('*').eq('bank_id', bank_id).execute()
    if not response.data:
        return jsonify({'error': 'No levels found for the given bank_id'}), 404
    return jsonify(response.data), 200

@app.route('/get_input_report/<int:ids>', methods=['GET'])
def get_input_report(ids):
    try:
        # Query input_report
        input_response = supabase.table('input_report')\
            .select('*')\
            .eq('in_id', ids)\
            .execute()

        print("Input Response:", input_response.data)  # Debug log

        if not input_response.data:
            return jsonify({"error": "Report not found"}), 404

        input_data = input_response.data[0]

        # Query image_processing using input_id
        image_response = supabase.table('image_processing')\
            .select('annotated_image, barcode_image , formatted_pixel_shift, shift_direction ')\
            .eq('in_id', ids)\
            .execute()

        print("Image Response:", image_response.data)  # Debug log

        # Combine the data
        result = {
            **input_data,
            'annotated_image': None,
            'barcode_image': None
        }

        # Add image data if exists
        if image_response.data and len(image_response.data) > 0:
            result['annotated_image'] = image_response.data[0].get('annotated_image')
            result['barcode_image'] = image_response.data[0].get('barcode_image')
            result['formatted_pixel_shift'] = image_response.data[0].get('formatted_pixel_shift')
            result['shift_direction'] = image_response.data[0].get('shift_direction')

        print("Final Result:", result)  # Debug log

        return jsonify(result), 200

    except Exception as e:
        print("Error fetching report:", str(e))
        print("Exception details:", type(e).__name__, str(e))  # More detailed error info
        return jsonify({"error": "Server error", "details": str(e)}), 500

@app.route('/serway_palletId', methods=['POST'])
def serway_palletId():
    data = request.json
    return jsonify({'status': 'success'}), 200

@app.route('/getCraneDetail', methods=['POST'])
def getCraneDetail():
    try:
        data = request.get_json()
        crane_id = data.get('crane_id')
        print(data)
        
        # Query the crane table
        crane_query = supabase.table('crane').select('*').eq('crane_id', crane_id).execute()
        crane_data = crane_query.data[0] if crane_query.data else None
        
        if not crane_data:
            return jsonify({"error": "Crane not found"}), 404
        
        # Query the camera table for the crane
        camera_query = supabase.table('camera').select('*').eq('crane_id', crane_id).execute()
        crane_data['camera'] = camera_query.data if camera_query.data else []
        
        # Query the bank table for the crane
        bank_query = supabase.table('bank').select('*').eq('crane_id', crane_id).execute()
        crane_data['bank'] = bank_query.data if bank_query.data else []
        
        result = {
            "craneData": crane_data,
            "msg": "get Crane Completed"
        }
        
        return jsonify(result), 201
    except Exception as e:
        print("Error 'Get Crane Detail':", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500 
    
@socketio.on('send_data')
def handle_send_data(data):
    response_data = {
        "message": "Data received successfully",
        "received_data": data
    }
    emit('receive_data', response_data)
@app.route('/set_opc_path', methods=['POST'])
def set_opc_path():
    global current_opc_path
    data = request.json
    path = data.get('path')
    if not path:
        return jsonify({'error': 'Path is required'}), 400
    current_opc_path = path
    return jsonify({'message': f'OPC path updated to {current_opc_path}'}), 200

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
    global current_opc_path
    while True:
        try:
            async with Client(url='opc.tcp://191.20.80.102:49320', timeout=10) as client:
                while True:
                    if current_opc_path:
                        # Dynamically use the selected path
                        dist_x = await client.get_node(f'ns=2;s={current_opc_path}.ASRS.Distance_X').read_value()
                        dist_y = await client.get_node(f'ns=2;s={current_opc_path}.ASRS.Distance_Y').read_value()
                        D0148 = await client.get_node(f'ns=2;s={current_opc_path}.ASRS.D0148').read_value()
                        data = {"dist_x": str(dist_x), "dist_y": str(dist_y), "D0148": str(D0148)}
                        opc_queue.put(data)  
                    await asyncio.sleep(0.4)
        except Exception as e:
            await asyncio.sleep(5)  # Retry after failure

def socketio_worker():
    while True:
        try:
            data = opc_queue.get(timeout=1)  # Wait for data from the queue
            socketio.emit('receive_data', data)
        except queue.Empty:
            continue  # If no data, keep waiting

# Routes Registration 
from app.router.site_config_route import site_config_route
app.register_blueprint(site_config_route)

if __name__ == '__main__':
    threading.Thread(target=opc_worker, daemon=True).start()
    threading.Thread(target=socketio_worker, daemon=True).start()

    # Run Flask-SocketIO 
    socketio.run(app, host='191.20.203.26', port=5556, debug=True, use_reloader=False)
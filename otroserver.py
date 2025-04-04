# GPIO control
# http://hostname:5005/gpio/set?pin=6&state=HIGH

# Camera feed (can be used for Octoprint)
# http://otrozone:5005/camera_feed

# References
# https://RandomNerdTutorials.com/raspberry-pi-mjpeg-streaming-web-server-picamera2/
# https://picamera.readthedocs.io/en/release-1.13/recipes2.html


from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from picamera2 import Picamera2
from gpiozero import LED
import cv2
import socket
import struct
from otroconfig import otroconfig

app = Flask(__name__)
# CORS(app) # Allow all endpoints
CORS(app, resources={r"/*": {"origins": "*"}})
# CORS(app, resources={r"/camera_feed": {"origins": "*"}})

# Keep the instances, so it keeps its state (HIGH/LOW) active
# and do not restarts the states when the instance is released
gpio_pins = {}

picam2 = None
streaming_clients = 0

def start_camera():
    global picam2
    if picam2 is None:
        picam2 = Picamera2()
        print(picam2.sensor_modes)
        otroconfig_cam = otroconfig["camera"]
        capture_width = otroconfig_cam["capture_width"]
        capture_height = otroconfig_cam["capture_height"]
        capture_format = otroconfig_cam["capture_format"]
        config = picam2.create_video_configuration({"size": (capture_width, capture_height), "format": capture_format})
        picam2.configure(config)
    picam2.start()
    print("Camera started.")

def stop_camera():
    global picam2
    if picam2 is not None:
        picam2.stop()
        print("Camera stopped.")

def gen_frames():
    try:
        while True:
            frame = picam2.capture_array()
            otroconfig_pp = otroconfig["postprocessing"]
            if (otroconfig_pp["resize"]):
                resize_width = otroconfig_pp["resize_width"]
                resize_height = otroconfig_pp["resize_height"]
                frame = cv2.resize(frame, (resize_width, resize_height))
            
            if (otroconfig_pp["rgb_to_bgr"]):
                # If red is blue, swap the channels
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
    except GeneratorExit:  # Client disconnected
        global streaming_clients
        streaming_clients -= 1
        print(f"Client disconnected. Total clients: {streaming_clients}")
        if streaming_clients == 0:
            stop_camera()

@app.route('/camera_feed')
def camera_feed():
    global streaming_clients
    if streaming_clients == 0:
        start_camera()

    streaming_clients += 1
    print(f"Client connected. Total clients: {streaming_clients}")

    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera')
def camera():
    return send_from_directory('static', 'camera.html')

@app.route('/gpio/switches')
def serve_static_html():
    return send_from_directory('static', 'switches.html')

@app.route('/gpio/get', methods=['GET'])
def gpio_get():
    pin = int(request.args.get('pin'))

    if pin in gpio_pins:
        state = 'HIGH' if gpio_pins[pin].is_active else 'LOW'
    else:
        state = 'HIGH'
    
    return jsonify({'state': state})

# Let's keep it simple and use get method even for set operation
@app.route('/gpio/set', methods=['GET']) 
def gpio_set():
    try:
        pin = int(request.args.get('pin'))
        state = request.args.get('state').lower()

        if pin not in gpio_pins:
            gpio_pins[pin] = LED(pin)
        
        if state == 'high':
            gpio_pins[pin].on()
            return jsonify({'pin': pin, 'state': state}), 200
        elif state == 'low':
            gpio_pins[pin].off()
            return jsonify({'pin': pin, 'state': state}), 200
        else:
            return jsonify({'error': 'Invalid state. Use "HIGH" or "LOW".'}), 400
        
    except ValueError:
        return jsonify({'error': 'Invalid pin number or state.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def send_magic_packet(mac):
    if len(mac) == 17:
        sep = mac[2]
        mac_bytes = bytes.fromhex(mac.replace(sep, ''))
    elif len(mac) == 12:
        mac_bytes = bytes.fromhex(mac)
    else:
        raise ValueError('Invalid MAC address format')

    magic_packet = b'\xff' * 6 + mac_bytes * 16

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, ('<broadcast>', 9))

@app.route('/wol/send', methods=['GET'])
def wol_send():
    try:
        mac = request.args.get('mac')
        if not mac:
            return jsonify({'error': 'MAC address is required.'}), 400

        send_magic_packet(mac)
        return jsonify({'message': f'Magic packet sent to {mac}'}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
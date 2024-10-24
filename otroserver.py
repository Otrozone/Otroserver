# http://10.0.1.100:5005/gpio/set?pin=6&state=HIGH

from flask import Flask, request, jsonify, send_from_directory, Response
from picamera2 import Picamera2
from gpiozero import LED
import cv2

app = Flask(__name__)

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
        config = picam2.create_video_configuration({"size": (1640, 1232), "format": "RGB888"})
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
            # frame = cv2.resize(frame, (640, 480))
            frame = cv2.resize(frame, (800, 600))
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

@app.route('/')
def serve_static_html():
    return send_from_directory('static', 'index.html')

@app.route('/gpio/get', methods=['GET'])
def gpio_get():
    pin = int(request.args.get('pin'))

    if pin in gpio_pins:
        state = 'HIGH' if gpio_pins[pin].is_active else 'LOW'
    else:
        state = 'HIGH'
    
    return jsonify({'state': state})

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
            return jsonify({'error': 'Invalid state. Use "on" or "off".'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid pin number or state.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
# Otroserver
Raspberry Pi 5 Python Flask HTTP server to control GPIO and camera.

## Installation
Because of the camera compatibility I recommend to use global python packeges (w/o venv).
```
sudo apt install python3-gpiozero python3-picamera2 python3-pyqt5 python3-opengl python3-opencv python3-flask python3-flask-cors
```

To make the scripts executable:
```
sudo chmod +x *.sh
```

## Tested environments
Tested on 
* Raspberry Pi 5 with Raspberry Pi Camera V2.1 (CSI ribbon)
* Raspberry Pi 4B with Genius USB Camera
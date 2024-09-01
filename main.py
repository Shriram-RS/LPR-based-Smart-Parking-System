import cv2
import imutils
import pytesseract
from flask import Flask, render_template, request, jsonify
import winsound
import numpy as np
import os
import requests
import time

app = Flask(__name__)

pytesseract.pytesseract.tesseract_cmd = r"D:\Tess\tesseract.exe"

# Function to capture and process number plate
def capture_number_plate(slot):
    # Ensure 'static' directory exists
    os.makedirs('static', exist_ok=True)
    vid = cv2.VideoCapture(0)
    timeout = time.time() + 20  # 10 seconds timeout
    while True:
        ret, image = vid.read()
        if not ret:
            print("Failed to capture image")
            break
        cv2.imshow('image', image)
        if cv2.waitKey(1) & 0xFF == ord('q') or time.time() > timeout:
            image_path = os.path.join('static', f'car_{slot}.jpg')
            cv2.imwrite(image_path, image)
            break
    vid.release()
    cv2.destroyAllWindows()
    return process_image(image_path)

# Function to process the captured image and extract number plate text
def process_image(image_path):
    image = cv2.imread(image_path)
    image = imutils.resize(image, width=500)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(gray, 170, 200)

    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]
    NumberPlateCount = None

    for i in cnts:
        perimeter = cv2.arcLength(i, True)
        approx = cv2.approxPolyDP(i, 0.02 * perimeter, True)
        if len(approx) == 4:
            NumberPlateCount = approx
            x, y, w, h = cv2.boundingRect(i)
            crp_img = image[y:y + h, x:x + w]

            crp_img_gray = cv2.cvtColor(crp_img, cv2.COLOR_BGR2GRAY)
            crp_img_gray = cv2.resize(crp_img_gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
            crp_img_thresh = cv2.adaptiveThreshold(crp_img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            crp_img_sharp = cv2.filter2D(crp_img_thresh, -1, kernel)

            cv2.imwrite('1.png', crp_img_sharp)
            break

    custom_config = r'--oem 3 --psm 8'
    text = pytesseract.image_to_string('1.png', config=custom_config)
    text = ''.join(e for e in text if e.isalnum())
    return text

# Route to fetch sensor status
@app.route('/get_sensor_status')
def get_sensor_status():
    sensor_data = fetch_sensor_status()
    return jsonify({
        "sensor1": sensor_data[0],
        "sensor2": sensor_data[1]
    })

# Route to capture number plate when triggered by AJAX
@app.route('/capture_number_plate', methods=['POST'])
def capture_number_plate_route():
    slot = request.form['slot']
    number_plate = capture_number_plate(slot)
    return jsonify({"number_plate": number_plate})

# Function to fetch sensor status from the NodeMCU
def fetch_sensor_status():
    try:
        response = requests.get(f"{NODEMCU_IP}/status")
        if response.status_code == 200:
            sensor_statuses = response.text.split(',')
            sensor_status_1 = sensor_statuses[0]
            sensor_status_2 = sensor_statuses[1]
            print(f"Sensor 1: {sensor_status_1}")
            print(f"Sensor 2: {sensor_status_2}")
            return sensor_statuses
        else:
            print(f"Failed to get data from NodeMCU. Status code: {response.status_code}")
            return ["Not Parked", "Not Parked"]
    except Exception as e:
        print(f"An error occurred: {e}")
        return ["Not Parked", "Not Parked"]

@app.route('/')
def index():
    return render_template('Park.html')

if __name__ == '__main__':
    NODEMCU_IP = "http://192.168.20.153/"
    app.run()

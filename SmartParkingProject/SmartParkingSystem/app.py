from flask import Flask, render_template_string, jsonify, request
import paho.mqtt.client as mqtt
import threading
import time

app = Flask(__name__)

data = {
    "spot1": "FREE",
    "type1": "NONE",
    "spot2": "OCCUPIED",
    "spot3": "FREE",
    "co2": 0,
    "gate": "CLOSED",
    "rfid": "NONE",
    "prediction": "UNKNOWN",
    "booking": "NONE"
}

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    if topic == "parking/spot1/status":
        data["spot1"] = payload
        update_prediction()

    if topic == "parking/spot1/type":
        data["type1"] = payload

    if topic == "parking/co2":
        data["co2"] = int(payload)

    if topic == "parking/gate/status":
        data["gate"] = payload

    if topic == "parking/gate/rfid":
        data["rfid"] = payload

def update_prediction():
    if data["spot1"] == "FREE":
        data["prediction"] = "HIGH AVAILABILITY"
    else:
        data["prediction"] = "LOW AVAILABILITY"

def mqtt_thread():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect("localhost", 1883, 60)

    client.subscribe("parking/#")
    client.loop_forever()

threading.Thread(target=mqtt_thread, daemon=True).start()

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Smart Parking</title>
<style>
body { background:#111; color:white; font-family:Arial; text-align:center; }
.container { display:flex; justify-content:center; gap:20px; margin-top:30px; }
.card { padding:20px; border-radius:15px; width:220px; }
.free { background:#2ecc71; }
.occupied { background:#e74c3c; }
.static { background:#3498db; }
.info { background:#34495e; }
button { padding:10px; font-size:16px; }
</style>
</head>
<body>

<h1>SMART PARKING SYSTEM</h1>

<div class="container">
  <div id="spot1" class="card free">Spot1</div>
  <div class="card occupied">Spot2<br>OCCUPIED</div>
  <div class="card free">Spot3<br>FREE</div>
</div>

<div class="container">
  <div id="vehicle" class="card info">Vehicle</div>
  <div id="co2" class="card info">CO2</div>
  <div id="prediction" class="card info">Prediction</div>
</div>

<div class="container">
  <div id="gate" class="card info">Gate</div>
  <div id="rfid" class="card info">RFID</div>
</div>

<div class="container">
  <button onclick="book()">Reserve Spot</button>
  <div id="booking" class="card info">Booking</div>
</div>

<script>
async function update() {
  const res = await fetch('/data');
  const d = await res.json();

  const s1 = document.getElementById("spot1");
  s1.innerHTML = "Spot1<br>" + d.spot1;
  s1.className = "card " + (d.spot1=="FREE"?"free":"occupied");

  document.getElementById("vehicle").innerHTML = "Vehicle<br>" + d.type1;
  document.getElementById("co2").innerHTML = "CO2<br>" + d.co2;
  document.getElementById("prediction").innerHTML = "Prediction<br>" + d.prediction;
  document.getElementById("gate").innerHTML = "Gate<br>" + d.gate;
  document.getElementById("rfid").innerHTML = "RFID<br>" + d.rfid;
  document.getElementById("booking").innerHTML = "Booking<br>" + d.booking;
}

async function book() {
  const res = await fetch('/book');
  update();
}

setInterval(update,1000);
</script>

</body>
</html>
""")

@app.route("/data")
def get_data():
    return jsonify(data)

@app.route("/book")
def book():
    if data["spot1"] == "FREE":
        data["booking"] = "CONFIRMED"
    else:
        data["booking"] = "FAILED - NO SPACE"
    return jsonify({"status":"ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

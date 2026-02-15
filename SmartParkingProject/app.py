from flask import Flask, render_template_string, jsonify
import paho.mqtt.client as mqtt
import threading

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

# ================= MQTT =================
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    if topic == "parking/spot1/status":
        data["spot1"] = payload
        update_prediction()

    elif topic == "parking/spot1/type":
        data["type1"] = payload

    elif topic == "parking/co2":
        try:
            data["co2"] = int(payload)
        except:
            data["co2"] = 0

    elif topic == "parking/gate/status":
        data["gate"] = payload

    elif topic == "parking/gate/rfid":
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

# ================= DASHBOARD =================
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
.card { padding:20px; border-radius:15px; width:220px; font-weight:bold; }

.free { background:#2ecc71; }
.occupied { background:#e74c3c; }
.info { background:#34495e; }

.gate-open { background:#2ecc71; }
.gate-denied { background:#e74c3c; }
.gate-default { background:#34495e; }

button { padding:10px; font-size:16px; cursor:pointer; }
</style>
</head>
<body>

<h1>SMART PARKING SYSTEM</h1>

<div class="container">
  <div id="spot1" class="card info">Spot1</div>
  <div class="card occupied">Spot2<br>OCCUPIED</div>
  <div class="card free">Spot3<br>FREE</div>
</div>

<div class="container">
  <div id="vehicle" class="card info">Vehicle</div>
  <div id="co2" class="card info">CO2</div>
  <div id="prediction" class="card info">Prediction</div>
</div>

<div class="container">
  <div id="gate" class="card gate-default">Gate</div>
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

  // Spot 1
  const s1 = document.getElementById("spot1");
  s1.innerHTML = "Spot1<br>" + d.spot1;
  s1.className = "card " + (d.spot1=="FREE"?"free":"occupied");

  // Vehicle
  document.getElementById("vehicle").innerHTML = "Vehicle<br>" + d.type1;

  // CO2
  document.getElementById("co2").innerHTML = "CO2<br>" + d.co2;

  // Prediction
  document.getElementById("prediction").innerHTML = "Prediction<br>" + d.prediction;

  // Gate
  const gate = document.getElementById("gate");
  gate.innerHTML = "Gate<br>" + d.gate;

  if (d.gate == "AUTHORIZED") {
      gate.className = "card gate-open";
  } else if (d.gate == "DENIED") {
      gate.className = "card gate-denied";
  } else {
      gate.className = "card gate-default";
  }

  // RFID
  document.getElementById("rfid").innerHTML = "RFID<br>" + d.rfid;

  // Booking
  document.getElementById("booking").innerHTML = "Booking<br>" + d.booking;
}

async function book() {
  await fetch('/book');
  update();
}

setInterval(update,1000);
update();  // Load immediately

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

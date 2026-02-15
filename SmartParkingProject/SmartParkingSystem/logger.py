import paho.mqtt.client as mqtt
import datetime

LOG_FILE = "parking_log.txt"

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker")
    client.subscribe("parking/#")

def on_message(client, userdata, msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    topic = msg.topic
    payload = msg.payload.decode()

    line = f"{timestamp} | {topic} | {payload}\n"

    with open(LOG_FILE, "a") as f:
        f.write(line)

    print(line.strip())

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_forever()

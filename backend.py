import paho.mqtt.client as mqtt
import datetime

BROKER = "localhost"
TOPIC = "parking/spot1/status"

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    status = msg.payload.decode()
    timestamp = datetime.datetime.now()

    log_entry = f"[{timestamp}] Spot Status: {status}"
    print(log_entry)

    with open("parking_log.txt", "a") as file:
        file.write(log_entry + "\n")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, 1883, 60)
client.loop_forever()


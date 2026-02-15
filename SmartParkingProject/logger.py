import paho.mqtt.client as mqtt
import datetime

def on_message(client, userdata, msg):
    with open("parking_log.txt", "a") as f:
        time = datetime.datetime.now()
        f.write(f"{time} | {msg.topic} | {msg.payload.decode()}\n")

client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.subscribe("parking/#")
client.loop_forever()

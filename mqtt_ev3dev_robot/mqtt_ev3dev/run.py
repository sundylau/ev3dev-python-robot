#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import logging
import json
import getopt
import paho.mqtt.client as mqtt

from command import CommandExecutor
from robot import Robot
from simulator import Simulator

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

###
# constants
###
TIMEOUT_SEC = 1
KEEPALIVE_SEC = 60

###
# default settings
###

# default topic
topic = "robot"

# default mqtt broker (hostname or ip) and port
server = "broker"
port = 1883

if __name__ == "__main__":

    # default robot
    robot = Simulator()

    # parse args
    optlist, args = getopt.getopt(sys.argv[1:], shortopts="", longopts=["broker=", "port=", "topic=", "mode="])

    for opt, arg in optlist:
        if opt == '--broker':
            server = arg
        elif opt == '--port':
            port = arg
        elif opt == '--topic':
            topic = arg
        elif opt == '--mode':
            if arg == 'ev3':
                robot = Robot()

    dispatcher = CommandExecutor(robot)

    logging.info("Try to connect to " + str(server) + ":" + str(port) + " and topic " + str(topic))
    logging.info("Robot: " + str(robot))

    mqtt = mqtt.Client()
    mqtt.connect(server, port, KEEPALIVE_SEC)

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
        logging.info("Connected with return code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(topic + "/process")


    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
        logging.info("Received message '" + str(msg.payload) + " on topic " + msg.topic + " with QoS " + str(msg.qos))

        try:
            obj = json.loads(msg.payload.decode('utf-8'))
            dispatcher.exec(obj)
        except Exception:
            logging.exception("Invalid message format! %s" % msg.payload)


    def on_disconnect(client, userdata, rc):
        logging.info("Disconnected with return code " + str(rc))


    mqtt.on_connect = on_connect
    mqtt.on_message = on_message
    mqtt.on_disconnect = on_disconnect

    while True:
        resp = mqtt.loop(timeout=TIMEOUT_SEC)

        # try reconnect when return code is not 0
        if resp != 0:
            try:
                mqtt.reconnect()
            except ConnectionRefusedError:
                logging.exception("connection lost rc=%s" % resp)
        else:
            mqtt.publish(topic + "/state", json.dumps(robot.state()))



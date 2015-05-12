"""
On a disconnect event, reconnects to the last connected server
"""
__author__ = "Nick Gamberini, Morgan Creekmore"
__copyright__ = "Copyright 2015, The SpockBot Project"
__license__ = "MIT"

from spock.mcp import mcpacket, mcdata
import time

INTERVAL = 2

class ReConnectPlugin:
    def __init__(self, ploader, settings):
        self.host = None
        self.port = None
        ploader.reg_event_handler('connect', self.connect)
        ploader.reg_event_handler('disconnect', self.reconnect_event)
        ploader.reg_event_handler(
            (mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x02),
            self.reconnect_success
        )
        self.net = ploader.requires('Net')
        self.client = ploader.requires('Client')
        self.reconnecting = False
        self.connected = True
        self.timeout = 0

    def connect(self, event, data):
        self.host = data[0]
        self.port = data[1]

    def reconnect_success(self, event, data):
        self.timeout = 0
        self.reconnecting = False
        self.connected = True

    def reconnect_event(self, event, data):
        self.connected = False
        if not self.reconnecting:
            while not self.connected:
                time.sleep(self.timeout)
                self.timeout = INTERVAL if self.timeout == 0 else self.timeout * INTERVAL
                self.reconnect()

    def reconnect(self):
        self.reconnecting = True
        self.net.restart()
        self.client.start(self.host, self.port)

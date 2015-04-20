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
        self.net = ploader.requires('Net')
        self.client = ploader.requires('Client')
        self.timers = ploader.requires('Timers')
        self.auth = ploader.requires('Auth')
        ploader.reg_event_handler('connect', self.connect)
        ploader.reg_event_handler('disconnect', self.reconnect_event)
        self.timeout = 0
        self.reconnecting = False

    def connect(self, event, data):
        self.timeout = 0
        self.reconnecting = False
        self.host = data[0]
        self.port = data[1]

    def reconnect_event(self, event, data):
        if not self.reconnecting:
            self.net.connected = False
            self.reconnecting = True
            while not self.net.connected:
                print("attempting reconnect...")
                self.reconnect()
                self.timeout = INTERVAL if self.timeout == 0 else self.timeout * INTERVAL
                time.sleep(self.timeout)

    def reconnect(self):
        self.net.restart()
        self.net.connect(self.host, self.port)
        self.net.push(mcpacket.Packet(
            ident = (mcdata.HANDSHAKE_STATE, mcdata.CLIENT_TO_SERVER, 0x00),
            data = {
                'protocol_version': mcdata.MC_PROTOCOL_VERSION,
                'host': self.net.host,
                'port': self.net.port,
                'next_state': mcdata.LOGIN_STATE
            }
        ))

        self.net.push(mcpacket.Packet(
            ident = (mcdata.LOGIN_STATE, mcdata.CLIENT_TO_SERVER, 0x00),
            data = {'name': self.auth.username},
        ))

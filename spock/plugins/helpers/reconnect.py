"""
On a disconnect event, reconnects to the last connected server
"""
__author__ = "Nick Gamberini, Morgan Creekmore"
__copyright__ = "Copyright 2015, The SpockBot Project"
__license__ = "MIT"

from spock.mcp import mcpacket, mcdata

class ReConnectPlugin:
    def __init__(self, ploader, settings):
        self.host = None
        self.port = None
        ploader.reg_event_handler('connect', self.connect)
        ploader.reg_event_handler('disconnect', self.reconnect)
        self.net = ploader.requires('Net')
        self.client = ploader.requires('Client')

    def connect(self, event, data):
        self.host = data[0]
        self.port = data[1]

    def reconnect(self, event, data):
        self.net.restart()
        self.client.start(self.host, self.port)

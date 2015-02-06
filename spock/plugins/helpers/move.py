"""
MovementPlugin provides a centralized plugin for controlling all outgoing
position packets so the client doesn't try to pull itself in a dozen directions.
It is planned to provide basic pathfinding and coordinate with the physics
plugin to implement SMP-compliant movement
"""

from spock.mcp import mcdata, mcpacket

class MovementPlugin:
	def __init__(self, ploader, settings):
		self.net = ploader.requires('Net')
		self.clientinfo = ploader.requires('ClientInfo')
		ploader.reg_event_handler(
			(mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x08),
			self.handle_position_look
		)
		ploader.reg_event_handler(
			(mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x07),
			self.handle_respawn
		)
		ploader.reg_event_handler('client_tick', self.client_tick)

	def handle_position_look(self, name, packet):
		self.clientinfo.position['x'] = packet.data['x']
		self.clientinfo.position['y'] = packet.data['y']
		self.clientinfo.position['z'] = packet.data['z']
		self.clientinfo.position['pitch'] = packet.data['pitch']
		self.clientinfo.position['yaw'] = packet.data['yaw']
		self.net.push(mcpacket.Packet(
			ident = (mcdata.PLAY_STATE, mcdata.CLIENT_TO_SERVER, 0x06),
			#TODO: check flags to see if Absolute vs Relative
			data = {
				'x': self.clientinfo.position['x'],
				'y': self.clientinfo.position['y'],
				'z': self.clientinfo.position['z'],
				'pitch': self.clientinfo.position['pitch'],
				'yaw': self.clientinfo.position['yaw'],
				'on_ground': True
			}
		))

	def client_tick(self, name, data):
		self.net.push(mcpacket.Packet(
			ident = (mcdata.PLAY_STATE, mcdata.CLIENT_TO_SERVER, 0x06),
			#TODO: check flags to see if Absolute vs Relative
			data = {
				'x': self.clientinfo.position['x'],
				'y': self.clientinfo.position['y'],
				'z': self.clientinfo.position['z'],
				'stance': self.clientinfo.position['stance'],
				'pitch': self.clientinfo.position['pitch'],
				'yaw': self.clientinfo.position['yaw'],
				'on_ground': True
			}
		))

	def handle_respawn(self, name, packet):
		self.net.push(mcpacket.Packet(
			ident = (mcdata.PLAY_STATE, mcdata.CLIENT_TO_SERVER, 0x06),
			#TODO: check flags to see if Absolute vs Relative
			data = {
				'x': self.clientinfo.position['x'],
				'y': self.clientinfo.position['y'],
				'z': self.clientinfo.position['z'],
				'pitch': self.clientinfo.position['pitch'],
				'yaw': self.clientinfo.position['yaw'],
				'on_ground': False
			}
		))

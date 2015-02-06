"""
Registers timers to provide the necessary tick rates expected by MC servers
"""

CLIENT_TICK_RATE = 0.5
PHYSICS_TICK_RATE = 0.2

class TickerPlugin:
	def __init__(self, ploader, settings):
		self.event = ploader.requires('Event')
		self.timers = ploader.requires('Timers')
		ploader.reg_event_handler('PLAY_STATE', self.start_tickers)

	def start_tickers(self, _, __):
		self.timers.reg_event_timer(CLIENT_TICK_RATE, self.client_tick)
		self.timers.reg_event_timer(PHYSICS_TICK_RATE, self.physics_tick)

	def client_tick(self):
		self.event.emit('client_tick')

	def physics_tick(self):
		self.event.emit('physics_tick')

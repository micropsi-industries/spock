import struct
import zlib
from spock.mcp import mcdata
from spock.mcp import datautils
from spock.mcp import nbt
from spock import utils
from spock.mcp.mcdata import (
    MC_BOOL, MC_UBYTE, MC_BYTE, MC_USHORT, MC_SHORT, MC_UINT, MC_INT,
    MC_LONG, MC_FLOAT, MC_DOUBLE, MC_STRING, MC_VARINT, MC_SLOT, MC_META
)

hashed_extensions = {}
extensions = tuple(tuple({} for i in j) for j in mcdata.packet_structs)
def extension(ident):
    def inner(cl):
        hashed_extensions[ident] = cl
        extensions[ident[0]][ident[1]][ident[2]] = cl
        return cl
    return inner

#Login SERVER_TO_CLIENT 0x01 Encryption Request
@extension((mcdata.LOGIN_STATE, mcdata.SERVER_TO_CLIENT, 0x01))
class ExtensionLSTC01:
    def decode_extra(packet, bbuff):
        length = datautils.unpack(MC_SHORT, bbuff)
        packet.data['public_key'] = bbuff.recv(length)
        length = datautils.unpack(MC_SHORT, bbuff)
        packet.data['verify_token'] = bbuff.recv(length)
        return packet

    def encode_extra(packet):
        o  = datautils.pack(MC_SHORT, len(packet.data['public_key']))
        o += packet.data['public_key']
        o += datautils.pack(MC_SHORT, len(packet.data['verify_token']))
        o += packet.data['verify_token']
        return o

#Login CLIENT_TO_SERVER 0x01 Encryption Response
@extension((mcdata.LOGIN_STATE, mcdata.CLIENT_TO_SERVER, 0x01))
class ExtensionLCTS01:
    def decode_extra(packet, bbuff):
        length = datautils.unpack(MC_SHORT, bbuff)
        packet.data['shared_secret'] = bbuff.recv(length)
        length = datautils.unpack(MC_SHORT, bbuff)
        packet.data['verify_token'] = bbuff.recv(length)
        return packet

    def encode_extra(packet):
        o  = datautils.pack(MC_SHORT, len(packet.data['shared_secret']))
        o += packet.data['shared_secret']
        o += datautils.pack(MC_SHORT, len(packet.data['verify_token']))
        o += packet.data['verify_token']
        return o

#Play  SERVER_TO_CLIENT 0x0C Spawn Player
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x0C))
class ExtensionPSTC0C:
	def decode_extra(packet, bbuff):
		packet.data['Data'] = tuple(
			tuple(
				datautils.unpack(MC_STRING, bbuff), #Name
				datautils.unpack(MC_STRING, bbuff), #Value
				datautils.unpack(MC_STRING, bbuff), #Signature
			) for i in datautils.unpack(MC_VARINT, bbuff)
		)

		packet.data['x'] = datautils.unpack(MC_INT, bbuff)
		packet.data['y'] = datautils.unpack(MC_INT, bbuff)
		packet.data['z'] = datautils.unpack(MC_INT, bbuff)
		packet.data['yaw'] = datautils.unpack(MC_BYTE, bbuff)
		packet.data['pitch'] = datautils.unpack(MC_BYTE, bbuff)
		packet.data['current_item'] = datautils.unpack(MC_SHORT, bbuff)
		packet.data['metadata'] = datautils.unpack(MC_META, bbuff)
		return packet

	def encode_extra(packet):
		o = datautils.pack(MC_VARINT, len(packet.data['Data']))
		for data in packet.data['Data']:
			for string in data:
				o += datautils.pack(MC_STRING, string)

		o += datautils.pack(MC_INT, packet.data['x'])
		o += datautils.pack(MC_INT, packet.data['y'])
		o += datautils.pack(MC_INT, packet.data['y'])
		o += datautils.pack(MC_BYTE, packet.data['yaw'])
		o += datautils.pack(MC_BYTE, packet.data['pitch'])
		o += datautils.pack(MC_SHORT, packet.data['current_item'])
		o += datautils.pack(MC_META, packet.data['metadata'])
		return o


#Play  SERVER_TO_CLIENT 0x0E Spawn Object
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x0E))
class ExtensionPSTC0E:
    def decode_extra(packet, bbuff):
        if packet.data['obj_data']:
            packet.data['speed_x'] = datautils.unpack(MC_SHORT, bbuff)
            packet.data['speed_y'] = datautils.unpack(MC_SHORT, bbuff)
            packet.data['speed_z'] = datautils.unpack(MC_SHORT, bbuff)
        return packet

    def encode_extra(packet):
        if packet.data['obj_data']:
            o  = datautils.pack(MC_SHORT, packet.data['speed_x'])
            o += datautils.pack(MC_SHORT, packet.data['speed_y'])
            o += datautils.pack(MC_SHORT, packet.data['speed_z'])
        return o

#Play  SERVER_TO_CLIENT 0x13 Destroy Entities
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x13))
class ExtensionPSTC13:
    def decode_extra(packet, bbuff):
        count = datautils.unpack(MC_BYTE, bbuff)
        packet.data['eids'] = [
            datautils.unpack(MC_INT, bbuff) for i in range(count)
        ]
        return packet

    def encode_extra(packet):
        o = datautils.pack(MC_INT, len(packet.data['eids']))
        for eid in packet.data['eids']:
            o += datautils.pack(MC_INT, eid)
        return o

#Play  SERVER_TO_CLIENT 0x20 Entity Properties
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x20))
class ExtensionPSTC20:
    def decode_extra(packet, bbuff):
        packet.data['properties'] = []
        for i in range(datautils.unpack(MC_INT, bbuff)):
            prop = {
                'key': datautils.unpack(MC_STRING, bbuff),
                'value': datautils.unpack(MC_DOUBLE, bbuff),
                'modifiers': [],
            }
            for j in range(datautils.unpack(MC_SHORT, bbuff)):
                a, b = struct.unpack('>QQ', bbuff.recv(16))
                prop['modifiers'].append({
                    'uuid': (a<<64)|b,
                    'amount': datautils.unpack(MC_DOUBLE, bbuff),
                    'operation': datautils.unpack(MC_BYTE, bbuff),
                })
            packet.data['properties'].append(prop)
        return packet

    def encode_extra(packet):
        o = datautils.pack(MC_INT, len(packet.data['properties']))
        for prop in packet.data['properties']:
            o += datautils.pack(MC_STRING, prop['key'])
            o += datautils.pack(MC_DOUBLE, prop['value'])
            o += datautils.pack(MC_SHORT, len(prop['modifiers']))
            for modifier in prop['modifiers']:
                o += struct.pack('>QQ',
                    (modifier['uuid']>>64)&((1<<64)-1),
                    modifier['uuid']&((1<<64)-1)
                )
                o += datautils.pack(MC_DOUBLE, modifier['amount'])
                o += datautils.pack(MC_BYTE, modifier['operation'])
        return o

#Play  SERVER_TO_CLIENT 0x21 Chunk Data
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x21))
class ExtensionPSTC21:
    def decode_extra(packet, bbuff):
        packet.data['data'] = zlib.decompress(
            bbuff.recv(datautils.unpack(MC_INT, bbuff))
        )
        return packet

    def encode_extra(packet):
        data = zlib.compress(packet.data['data'])
        o = datautils.pack(MC_INT, len(data))
        o += data
        return o

#Play  SERVER_TO_CLIENT 0x22 Multi Block Change
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x22))
class ExtensionPSTC22:
    def decode_extra(packet, bbuff):
        count = datautils.unpack(MC_SHORT, bbuff)
        assert(datautils.unpack(MC_INT, bbuff) == 4*count)
        packet.data['blocks'] = []
        for i in range(count):
            data = datautils.unpack(MC_UINT, bbuff)
            packet.data['blocks'].append({
                'metadata': (data     )&0xF,
                'block_id':    (data>> 4)&0xFFF,
                'y':        (data>>16)&0xFF,
                'z':        (data>>24)&0xF,
                'x':        (data>>28)&0xF,
            })
        return packet

    def encode_extra(packet):
        o  = datautils.pack(MC_SHORT, len(packet.data['blocks']))
        o += datautils.pack(MC_INT, 4*len(packet.data['blocks']))
        for block in packet.data['blocks']:
            o += datautils.pack(MC_UINT,
                block['metadata']  +
                (block['type']<<4) +
                (block['y'] << 16) +
                (block['z'] << 24) +
                (block['x'] << 28)
            )
        return o

#Play  SERVER_TO_CLIENT 0x26 Map Chunk Bulk
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x26))
class ExtensionPSTC26:
    def decode_extra(packet, bbuff):
        count = datautils.unpack(MC_SHORT, bbuff)
        size = datautils.unpack(MC_INT, bbuff)
        packet.data['sky_light'] = datautils.unpack(MC_BOOL, bbuff)
        packet.data['data'] = zlib.decompress(bbuff.recv(size))
        packet.data['metadata'] = [{
            'chunk_x': datautils.unpack(MC_INT, bbuff),
            'chunk_z': datautils.unpack(MC_INT, bbuff),
            'primary_bitmap': datautils.unpack(MC_USHORT, bbuff),
            'add_bitmap': datautils.unpack(MC_USHORT, bbuff),
        } for i in range(count)]
        return packet

    def encode_extra(packet):
        data = zlib.compress(packet.data['data'])
        o = datautils.pack(MC_SHORT, len(packet.data['metadata']))
        o += datautils.pack(MC_INT, len(data))
        o += datautils.pack(MC_BOOL, packet.data['sky_light'])
        for metadata in packet.data['metadata']:
            o += datautils.pack(MC_INT, metadata['chunk_x'])
            o += datautils.pack(MC_INT, metadata['chunk_z'])
            o += datautils.pack(MC_USHORT, metadata['primary_bitmap'])
            o += datautils.pack(MC_USHORT, metadata['add_bitmap'])
        return o

#Play  SERVER_TO_CLIENT 0x27 Explosion
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x27))
class ExtensionPSTC27:
    def decode_extra(packet, bbuff):
        packet.data['blocks'] = [
            [datautils.unpack(MC_BYTE, bbuff) for j in range(3)]
        for i in range(datautils.unpack(MC_INT, bbuff))]
        packet.data['player_x'] = datautils.unpack(MC_FLOAT, bbuff)
        packet.data['player_y'] = datautils.unpack(MC_FLOAT, bbuff)
        packet.data['player_z'] = datautils.unpack(MC_FLOAT, bbuff)
        return packet

    def encode_extra(packet):
        o = datautils.pack(MC_INT, len(packet.data['blocks']))
        for block in packet.data['blocks']:
            for coord in block:
                o += datautils.pack(MC_BYTE, coord)
        o += datautils.pack(MC_FLOAT, packet.data['player_x'])
        o += datautils.pack(MC_FLOAT, packet.data['player_y'])
        o += datautils.pack(MC_FLOAT, packet.data['player_z'])
        return o

#Play  SERVER_TO_CLIENT 0x2D Open Window
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x2D))
class ExtensionPSTC2D:
	def decode_extra(packet, bbuff):
		if packet.data['window_id'] == 11:
			packet.data['eid'] = datautils.unpack(MC_INT, bbuff)
		return packet

	def encode_extra(packet):
		if packet.data['window_id'] == 11:
			return datautils.pack(MC_SHORT, packet.data['eid'])
		

#Play  SERVER_TO_CLIENT 0x30 Window Items
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x30))
class ExtensionPSTC30:
    def decode_extra(packet, bbuff):
        packet.data['slots'] = [
            datautils.unpack(MC_SLOT, bbuff)
        for i in range(datautils.unpack(MC_SHORT, bbuff))]
        return packet

    def encode_extra(packet):
        o = datautils.pack(MC_SHORT, len(packet.data['slots']))
        for slot in packet.data['slots']:
            o += datautils.pack(MC_SLOT, slot)
        return o

#TODO: Actually decode the map data into a useful format
#Play  SERVER_TO_CLIENT 0x34 Maps
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x34))
class ExtensionPSTC34:
    def decode_extra(packet, bbuff):
        packet.data['data'] = bbuff.recv(datautils.unpack(MC_SHORT, bbuff))
        return packet

    def encode_extra(packet):
        o = datautils.pack(len(packet.data['data']))
        o += packet.data['data']
        return o

#Play  SERVER_TO_CLIENT 0x35 Update Block Entity
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x35))
class ExtensionPSTC35:
    def decode_extra(packet, bbuff):
        data = bbuff.recv(datautils.unpack(MC_SHORT, bbuff))
        data = utils.BoundBuffer(zlib.decompress(data, 16+zlib.MAX_WBITS))
        assert(datautils.unpack(MC_BYTE, data) == nbt.TAG_COMPOUND)
        name = nbt.TAG_String(buffer = data)
        nbt_data = nbt.TAG_Compound(buffer = data)
        nbt_data.name = name
        packet.data['nbt'] = nbt_data
        return packet

    def encode_extra(packet):
        bbuff = utils.BoundBuffer()
        TAG_Byte(packet.data['nbt'].id)._render_buffer(bbuff)
        TAG_String(packet.data['nbt'].name)._render_buffer(bbuff)
        packet.data['nbt']._render_buffer(bbuff)
        compress = zlib.compressobj(wbits = 16+zlib.MAX_WBITS)
        data = compress.compress(bbuff.flush())
        data += compress.flush()
        o = datautils.pack(MC_SHORT, len(data))
        o += data
        return o

#Play  SERVER_TO_CLIENT 0x37 Statistics
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x37))
class ExtensionPSTC37:
    def decode_extra(packet, bbuff):
        packet.data['entries'] = [[
            datautils.unpack(MC_STRING, bbuff),
            datautils.unpack(MC_VARINT, bbuff)
        ] for i in range(datautils.unpack(MC_VARINT, bbuff))]
        return packet

    def encode_extra(packet):
        o = datautils.pack(MC_VARINT, len(packet.data['entries']))
        for entry in packet.data['entries']:
            o += datautils.pack(MC_STRING, entry[0])
            o += datautils.pack(MC_VARINT, entry[1])
        return o

#Play  SERVER_TO_CLIENT 0x3A Tab-Complete
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x3A))
class ExtensionPSTC3A:
    def decode_extra(packet, bbuff):
        packet.data['matches'] = [
            datautils.unpack(MC_STRING, bbuff)
        for i in range(datautils.unpack(MC_VARINT, bbuff))]
        return packet

    def encode_extra(packet):
        o = datautils.pack(MC_VARINT, len(packet.data['matches']))
        for match in packet.data['matches']:
            o += datautils.pack(MC_STRING, match)
        return o

#Play  SERVER_TO_CLIENT 0x3E Teams
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x3E))
class ExtensionPSTC3E:
    def decode_extra(packet, bbuff):
        mode = packet.data['mode']
        if mode == 0 or mode == 2:
            packet.data['display_name'] = datautils.unpack(MC_STRING, bbuff)
            packet.data['team_prefix'] = datautils.unpack(MC_STRING, bbuff)
            packet.data['team_suffix'] = datautils.unpack(MC_STRING, bbuff)
            packet.data['friendly_fire'] = datautils.unpack(MC_BYTE, bbuff)
        if mode == 0 or mode == 3 or mode == 4:
            packet.data['players'] = [
                datautils.unpack(MC_STRING, bbuff)
            for i in range(datautils.unpack(MC_SHORT, bbuff))]
        return packet

    def encode_extra(packet):
        mode = packet.data['mode']
        o = b''
        if mode == 0 or mode == 2:
            o += datautils.pack(MC_STRING, packet.data['display_name'])
            o += datautils.pack(MC_STRING, packet.data['team_prefix'])
            o += datautils.pack(MC_STRING, packet.data['team_suffix'])
            o += datautils.pack(MC_BYTE, packet.data['friendly_fire'])
        if mode == 0 or mode == 3 or mode == 4:
            o += datautils.pack(MC_SHORT, len(packet.data['players']))
            for player in packet.data['players']:
                o += datautils.pack(MC_STRING, player)
        return o

#Play  SERVER_TO_CLIENT 0x3F Plugin Message
#Play  CLIENT_TO_SERVER 0x17 Plugin Message
@extension((mcdata.PLAY_STATE, mcdata.SERVER_TO_CLIENT, 0x3F))
@extension((mcdata.PLAY_STATE, mcdata.CLIENT_TO_SERVER, 0x17))
class ExtensionPluginMessage:
    def decode_extra(packet, bbuff):
        packet.data['data'] = bbuff.recv(datautils.unpack(MC_SHORT, bbuff))
        return packet

    def encode_extra(packet):
        o = datautils.pack(MC_SHORT, len(packet.data['data']))
        o += packet.data['data']
        return o

@extension(mcdata.packet_idents['PLAY<Open Window'])
class ExtensionOpenWindow:
    def decode_extra(packet, bbuff):
        if packet.data['inv_type'] == 11:
            packet.data['eid'] = datautils.unpack(MC_INT, bbuff)

    def encode_extra(packet):
        if packet.data['inv_type'] == 11:
            return datautils.pack(MC_INT, packet.data['eid'])
        else:
            return ''

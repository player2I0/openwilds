import asyncio
import websockets
import json
import msgpack
import base64
import websockets

import game_util.protocol_packets as packets

class GamePlayerConnections:
	def __init__(self, game):
		self.connections = []

	def add(self, connection):
		self.connections.append(connection)

	def remove(self, connection):
		self.connections.remove(connection)

	def add_ws(self, ws):
		connection = GamePlayerConnection(ws)
		self.add(connection)
		return connection

	def remove_ws(self, ws):
		for connection in self.connections:
			if connection.ws == ws:
				self.remove(connection)
				break

	async def broadcast_packet(self, packet):
		for connection in self.connections:
			await connection.send_packet(packet)


class GamePlayerConnection:
	def __init__(self, ws):
		self.ws = ws
		self.citizen = None

		self.pointer_x = 0
		self.pointer_y = 0

	async def send_packet(self, packet):
		try:
			await self.ws.send(msgpack.packb(packet.build()))
		except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosedError) as e:
			pass

def build_incoming_packet(connection, data):
	msg = msgpack.unpackb(data, raw=False)

	packs = {
		'hello': packets.HelloIncomingPacket,
		'ping': packets.PingIncomingPacket,
		'pointer': packets.PointerIncomingPacket,
		'direction': packets.DirectionIncomingPacket,
		'move': packets.MoveIncomingPacket,
		'growl_start': packets.GrowlStartIncomingPacket,
		'growl_stop': packets.GrowlStopIncomingPacket,
		'press': packets.PressIncomingPacket,
		'release': packets.ReleaseIncomingPacket,
		'useSkill': packets.UseSkillIncomingPacket,
		'ack': packets.AckIncomingPacket,
		'message': packets.MessageIncomingPacket,
		'chatHistory': packets.ChatHistoryIncomingPacket
	}

	if msg[0] in packs:
		return packs[msg[0]](connection, msg[1])
	else:
		return packets.UnsupportedIncomingPacket(connection, msg)
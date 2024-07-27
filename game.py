import websockets
import asyncio
import time
from aabbtree import AABB
from aabbtree import AABBTree

import game_util.protocol as protocol
import game_util.protocol_packets as packets

class Game:
	def __init__(self, master):
		self.master = master
		self.connections = protocol.GamePlayerConnections(self)
		self.world = GameWorld(self)
		self.sharer = GameSharer()
		self.last_step = time.time()
		self.chat = GameChat(self)

		self.ended = False

		self.last_clients_count = 0

	async def main(self):
		async with websockets.serve(self.handler, "localhost", self.master.config['game_port']):
			print('started game websocket!')
			await asyncio.Future()  # run forever

	async def handler(self, websocket):
		connection = self.connections.add_ws(websocket)

		async for message in websocket:
			#packet = protocol.GamePlayerConnectionPacket(message, websocket)
			packet = protocol.build_incoming_packet(connection, message)

			await packet.process(self)

		try:
			await websocket.wait_closed()
		finally:
			connection.citizen.remove = True
			connection.citizen.p_changes.add('remove')
			self.connections.remove_ws(websocket)

	async def step(self, dt):
		#t = time.time()
		changes = []
		to_delete = []

		existing_overlaps = {}

		self.world.entities.collisions.build_tree()

		for entity in self.world.entities.groups.citizens:
			existing_overlaps[entity.sid] = []

			overlaps = self.world.entities.collisions.entity_overlaps(entity)
			
			for overlap_entity in overlaps.copy():
				if overlap_entity.constructorName == 'Citizen' and overlap_entity.sid in existing_overlaps and entity.sid in existing_overlaps[overlap_entity.sid]:
					overlaps.remove(overlap_entity)
				else:
					existing_overlaps[entity.sid].append(overlap_entity.sid)
			
			entity.step(self, dt, overlaps)

			if len(entity.p_changes.properties) > 0:
				changes.append(entity.p_changes.encode(self.sharer))

			if len(entity.p_private.p_changes.properties) > 0:
				await entity.p_connection.send_packet(packets.PrivateOutcomingPacket(entity.p_private.p_changes.encode(self.sharer)))

			if entity.remove:
				to_delete.append(entity)

		for hit in self.world.entities.groups.hits:
			en = hit.p_changes.encode(self.sharer)
			await self.connections.broadcast_packet(packets.HitOutcomingPacket(en))
			to_delete.append(hit)

		for dash in self.world.entities.groups.dashes:
			await self.connections.broadcast_packet(packets.DashOutcomingPacket(entity_sid=dash.entity.sid, direction=dash.direction))
			to_delete.append(dash)

		for entity in to_delete:
			self.world.entities.remove(entity)

		#print('time to process: ' + '{0:.10f}'.format(time.time() - t) + ' dt: ' + '{0:.10f}'.format(dt))

		return changes

	async def game_loop(self, dt):
		changes = await self.step(dt)

		if len(changes) > 0:
			await self.connections.broadcast_packet(packets.UpdateOutcomingPacket(entities=changes, last_clients=self.last_clients_count, clients=len(self.connections.connections)))

		self.last_clients_count = len(self.connections.connections)

	async def launch_game_loop(self, t):
		while True:
			start = time.time()
			dt = time.time() - self.last_step
			self.last_step += dt

			await self.game_loop(dt)

			await asyncio.sleep(start + t - time.time())


class GameChat:
	def __init__(self, game):
		self.game = game

		self.messages = []

	def add_message(self, msg):
		self.messages.append(msg)

	async def say(self, conn, txt, game):
		if len(txt.strip()) > 0:
			msg = GameChatMessage(conn.citizen, txt)
			self.add_message(msg)

			await game.connections.broadcast_packet(packets.SayOutcomingPacket(entity_sid=msg.entity_sid, text=msg.text))


class GameChatMessage:
	def __init__(self, entity, text, system=False):
		self.system = system

		self.entity_sid = entity.sid
		self.text = text
		self.nickname = entity.name


class GameWorld:
	def __init__(self, game):
		self.game = game
		self.entities = GameWorldEntities(self)
		self.map = GameWorldMap(self, width=1984, height=1518)


class GameWorldMap:
	def __init__(self, game, width, height):
		self.game = game

		self.width = width
		self.height = height
		self.data = '{}'


class GameWorldEntities:
	def __init__(self, world):
		self.world = world

		self.collisions = GameWorldEntitiesCollisions(self)

		self.groups = GameWorldEntitiesGroups(self)

		self.entities = []
		self.sid_counter = 10
		self.sid_map = {}

		self.groups.create_group('citizens')
		self.groups.create_group('slashes')
		self.groups.create_group('hits')
		self.groups.create_group('dashes')

	def add(self, entity):
		self.entities.append(entity)

		if entity.p_is_entity:
			entity.sid = self.sid_counter
			self.sid_map[entity.sid] = entity
			self.sid_counter += 1

	def remove(self, entity):
		if entity.p_group != None:
			self.groups.remove(entity.p_group, entity)

		self.entities.remove(entity)

		if entity.p_is_entity:
			del self.sid_map[entity.sid]


class GameWorldEntitiesGroups:
	def __init__(self, entities):
		self.entities = entities

	def create_group(self, name):
		setattr(self, name, [])

	def add(self, group, entity):
		self.entities.add(entity)
		getattr(self, group).append(entity)
		entity.p_group = group

	def remove(self, group, entity):
		entity.p_group = None
		getattr(self, group).remove(entity)


class GameWorldEntitiesCollisions:
	def __init__(self, entities):
		self.entities = entities

		self.entities_to_aabb = {}

	def build_tree(self):
		self.tree = AABBTree()

		#self.tree.add(AABB([(-self.entities.world.map.width, 0), (0, -self.entities.world.map.height)]), None)

		for entity in self.entities.entities:
			aabb = AABB(entity.p_hitbox.get_absolute_coordinates())
			#print(entity.p_hitbox.get_absolute_coordinates())
			self.tree.add(aabb, entity)
			self.entities_to_aabb[entity.sid] = aabb

	def entity_overlaps(self, entity):
		aabbs = self.tree.overlap_values(self.entities_to_aabb[entity.sid], closed=True)

		try:
			aabbs.remove(entity)
		except:
			pass
		
		return aabbs


class GameSharer:
	def __init__(self):
		self.keys = {
			1: "snapshot",
			2: "PlayerPrivateData",
			3: "Game",
			4: "battle_royale",
			5: "fun",
			6: "arena1",
			7: "coins",
			8: "mapReplaceTile",
			9: "Rope",
			10: "DebugPoint",
			11: "Tree",
			12: "Obstacle",
			13: "Citizen",
			14: "Monster",
			15: "Animal",
			16: "Sandworm",
			17: "Pedestal",
			18: "Campfire",
			19: "FlagBase",
			20: "ClaimableFlag",
			21: "Gate",
			22: "FortFlag",
			23: "Flag",
			24: "Crate",
			25: "Guillotine",
			26: "Spikes",
			27: "Quicksand",
			28: "ThrowingKnife",
			29: "Projectile",
			30: "Wave",
			31: "Pickup",
			32: "Stone",
			33: "Mine",
			34: "Ball",
			35: "SoccerGoalLine",
			36: "Beam",
			37: "Grenade",
			38: "Container",
			39: "Door",
			40: "Stove",
			41: "Marker",
			42: "Hit",
			43: "idle",
			44: "orc_archer",
			45: "bow",
			46: "hood",
			47: "no_shield",
			48: "default_voice",
			49: "no_cape",
			50: "medical_cupboard1",
			51: "fort",
			52: "armory_wardrobe1",
			53: "randoms",
			54: "barbarian_miner",
			55: "hammer",
			56: "no_helmet",
			57: "barbarian_sentry",
			58: "club",
			59: "orc_berserker",
			60: "double_axe",
			61: "elf_ears",
			62: "mohawk_hair",
			63: "orc_tank",
			64: "shield_heavy",
			65: "orc_warrior",
			66: "axe",
			67: "viking_helmet",
			68: "shield_usa",
			69: "barbarian_saper",
			70: None,
			71: "backpack",
			72: "barbarian_giant",
			73: "house",
			74: "default",
			75: "mine",
			76: "knife",
			77: "stun",
			78: "hero",
			79: "fedora",
			80: "desert",
			81: "attack",
			82: "charge",
			83: "jump",
			84: "launchArrow",
			85: "arrow",
			86: "jumpAttack",
			87: "roll",
			88: "throw",
			89: "stone",
			90: "block",
			91: "blocked",
			92: "dying",
			93: "kick",
			94: "dead",
			95: "powerHit",
			96: "fallBack",
			97: "fallFront",
			98: "spin",
			99: "shield_wooden",
			100: "ice_staff",
			101: "noble_cape",
			102: "operate"
		}

		self.values = self.generate_values()
		self.encoded = self.encode()

		self.descriptors = {"PlayerPrivateData":[["items","object"],["stamina","sfloat"],["temperature","sfloat"],["cooldowns","object"],["gold_cap","int"],["gold_inc","int"],["interactor_sid","int"],["exp","int"]],"Game":[["weather","key"]],"battle_royale":[["eclipseRadius","int"]],"fun":[["eclipseRadius","int"]],"arena1":[["eclipseRadius","int"]],"coins":[["x","int"],["y","int"],["follow","int"],["amount","int"]],"mapReplaceTile":[["x","int"],["y","int"],["layer","key"],["key","int"]],"Rope":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["ex","int"],["ey","int"]],"DebugPoint":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["color","int"]],"Tree":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["health","int"],["pine","bool"]],"Obstacle":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["key","int"],["type","key"]],"Citizen":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["key","key"],["growling","bool"],["moving","int"],["stateQueue","queue"],["direction","sfloat"],["kills","int"],["team","int"],["name","string"],["dead","bool"],["health","sfloat"],["maxHealth","int"],["armor","int"],["score","int"],["flag","string"],["kind","string"],["frozen","float"],["gameLink","int"],["weapon","key"],["helmet","key"],["shield","key"],["voice","key"],["badges","object"],["cape","key"],["partner_sid","int"]],"Monster":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["health","int"],["type","string"],["stateKey","string"],["direction","float"],["dead","bool"]],"Animal":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["type","string"],["stateKey","string"],["direction","float"],["dead","bool"]],"Sandworm":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["stateQueue","queue"]],"Pedestal":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"]],"Campfire":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["health","int"]],"FlagBase":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["team","int"]],"ClaimableFlag":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["team","int"],["a","float"],["b","float"]],"Gate":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["team","int"],["state","int"],["health","int"]],"FortFlag":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["team","int"]],"Flag":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["team","int"],["parent_sid","int"],["status","key"]],"Crate":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["key","int"],["dead","bool"]],"Guillotine":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["key","int"],["closed","bool"],["dirty","bool"]],"Spikes":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["key","int"],["closed","bool"],["dirty","bool"]],"Quicksand":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["radius","int"]],"ThrowingKnife":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int","sharedx"],["y","int","sharedy"],["speed","int"],["team","int"],["key","key"],["direction","float"]],"Projectile":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["speed","int"],["key","key"],["direction","float"]],"Wave":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["direction","float"],["speed","int"],["duration","int"]],"Pickup":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["sx","int"],["sy","int"],["key","string"]],"Stone":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["key","string"],["dead","bool"]],"Mine":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["exploded","bool"],["x","int"],["y","int"],["timeout","float"],["range","int"]],"Ball":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["z","int"]],"SoccerGoalLine":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["width","int"],["height","int"],["team","int"],["orientation","int"]],"Beam":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["target_sid","int"],["length","int"],["direction","float"],["key","key"],["team","int"]],"Grenade":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["exploded","bool"],["targetX","int"],["targetY","int"],["parent_sid","int"],["key","key"],["delay","float"],["speed","float"],["hits","object"]],"Container":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["serialized","object"],["key","key"],["locked","boolean"]],"Door":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["locked","boolean"],["team","int"]],"Stove":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["health","int"]],"Marker":[["sid","always"],["constructorName","key"],["remove","bool","_remove"],["x","int"],["y","int"],["marker","key"],["globalMarker","bool"],["markerText","string"]],"Hit":[["armor","int"],["projectile_sid","int"],["entity_sid","int"],["attacker_sid","int"],["kick","boolean"],["missile","boolean"],["blocked","boolean"],["damage","float"],["fall","boolean"],["stun","boolean"],["crush","boolean"],["fatal","boolean"],["reverse","boolean"],["blockBroken","boolean"]]}
		self.descriptors_dict = self.generate_dict_descriptors()

	def generate_values(self):
		values = {}

		for i in self.keys:
			values[self.keys[i]] = i

		return values

	def generate_dict_descriptors(self):
		d = {}

		for entity in self.descriptors:
			d[entity] = {}

			for property in self.descriptors[entity]:
				d[entity][property[0]] = property[1]

		return d

	def encode(self):
		r = []

		for i in self.keys:
			r.append(i)
			r.append(self.keys[i])
		return r
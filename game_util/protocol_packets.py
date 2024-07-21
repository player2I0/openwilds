import msgpack
import math

import game_util.entities.citizen as citizen
import game_util.entities.citizen_states as citizen_states
import game_util.utility as utility

#INCOMING
class IncomingPacket:
	def __init__(self, connection):
		self.connection = connection

class HelloIncomingPacket(IncomingPacket):
	def __init__(self, connection, data):
		super().__init__(connection)

		self.url = data['url']
		self.seat_id = data['seat_id']
		self.mode = data['mode']
		self.gender = data['gender']

	async def process(self, game):
		#print('yes!')
		player = citizen.Citizen(game.sharer, game)
		player.key = 'hero'
		player.name = str(game.world.entities.sid_counter)
		player.weapon = 'axe'
		player.helmet = 'viking_helmet'
		player.shield = 'shield_heavy'
		player.voice = 'default_voice'
		player.cape = 'no_cape'
		player.kind = 'human'
		player.health = 8
		player.maxHealth = 8
		player.x = -1900
		player.y = -1452
		player.moving = 1
		player.team = 2
		#player.stateQueue.set('idle')

		player.p_connection = self.connection

		game.world.entities.groups.add('citizens', player)
		self.connection.citizen = player

		await self.connection.send_packet(SayOutcomingPacket(system=True, text="Welcome to EU server"))

		#await self.connection.ws.send(msgpack.packb(['snapshot', {'ended': False, 'entities': [player.encode(game.sharer)], 'innerWidth': 1984, 'innerHeight': 1518, 'lifetime': 1, 'mapData': '{}', 'mapName': '', 'mode': 'fun', 'sharedKeys': game.sharer.encoded, 'speed': 1}]))
		await self.connection.send_packet(SnapshotOutcomingPacket(game=game))

		await self.connection.send_packet(SetPlayerCitizenOutcomingPacket(citizen=player))

		await self.connection.send_packet(PrivateOutcomingPacket(data=player.p_private.p_changes.encode(game.sharer)))

		player.p_changes.add_all_properties(game.sharer)


class PingIncomingPacket(IncomingPacket):
	def __init__(self, connection, data):
		super().__init__(connection)

	async def process(self, game):
		await self.connection.send_packet(PongOutcomingPacket())


class PointerIncomingPacket(IncomingPacket):
	def __init__(self, connection, data):
		super().__init__(connection)

		self.x = data[0]
		self.y = data[1]

		self.blacklist_states = ['jumpAttack', 'dying', 'dead']

	async def process(self, game):
		if self.x != None and self.y != None:

			self.connection.pointer_x = self.x
			self.connection.pointer_y = self.y

			if self.connection.citizen != None and self.connection.citizen.stateQueue.state.alias not in self.blacklist_states:
				player = self.connection.citizen

				dir = round(utility.angle_towards_pos(player.x, player.y, self.x, self.y), 1)

				if dir != player.direction:
					player.direction = dir
					player.p_changes.add('direction', game.sharer)


class PressIncomingPacket(IncomingPacket):
	def __init__(self, connection, data):
		super().__init__(connection)

	async def process(self, game):
		self.connection.citizen.p_inputs.lmb_pressed = True


class ReleaseIncomingPacket(IncomingPacket):
	def __init__(self, connection, data):
		super().__init__(connection)

	async def process(self, game):
		#self.connection.citizen.p_inputs.lmb_pressed = False
		self.connection.citizen.p_inputs.lmb_release()


class DirectionIncomingPacket(IncomingPacket):
	def __init__(self, connection, data):
		super().__init__(connection)

		self.dir = data

	async def process(self, game):
		#print(self.dir)
		#self.connection.citizen.direction = self.dir
		pass


class MoveIncomingPacket(IncomingPacket):
	def __init__(self, connection, data):
		super().__init__(connection)

		self.key = data['key']

	async def process(self, game):
		player = self.connection.citizen

		mov = (0, 0)

		UP = (0, 1)
		DOWN = (0, -1)
		LEFT = (-1, 0)
		RIGHT = (1, 0)
		movement_vector = (0, 0)
		if self.key & 0b0010:  # UP
			movement_vector = utility.addvec(movement_vector, UP)
		if self.key & 0b1000:  # DOWN
			movement_vector = utility.addvec(movement_vector, DOWN)
		if self.key & 0b0100:  # LEFT
			movement_vector = utility.addvec(movement_vector, LEFT)
		if self.key & 0b0001:  # RIGHT
			movement_vector = utility.addvec(movement_vector, RIGHT)  # или любое другое значение
		if movement_vector == (0, 0):
			player.moving = 0
			player.p_changes.add('moving', game.sharer)
		else:
			player.moving = 1
			player.p_changes.add('moving', game.sharer)

		player.p_movement_vector = movement_vector
		#player.changes.add('movement_vector', game.sharer)
		#print(player.p_changes.encode(game.sharer))


class GrowlStartIncomingPacket(IncomingPacket):
	def __init__(self, connection, data):
		super().__init__(connection)

	async def process(self, game):
		self.connection.citizen.growling = True
		self.connection.citizen.p_changes.add('growling')


class GrowlStopIncomingPacket(IncomingPacket):
	def __init__(self, connection, data):
		super().__init__(connection)

	async def process(self, game):
		self.connection.citizen.growling = False
		self.connection.citizen.p_changes.add('growling')


class UseSkillIncomingPacket(IncomingPacket):
	def __init__(self, connection, data):
		super().__init__(connection)

		self.skill = data

	async def process(self, game):
		player = self.connection.citizen

		if self.skill == 'jump':
			player.stateQueue.state.set(citizen_states.CitizenStateJump(player.stateQueue))


class UnsupportedIncomingPacket(IncomingPacket):
	def __init__(self, connection, data):
		super().__init__(connection)
		self.data = data

	async def process(self, game):
		print('unsupported incoming packet! ', self.data)


#OUTCOMING
class OutcomingPacket:
	def __init__(self):
		self.alias = 'packet'

	def format(self, encoded, sharer):
		if encoded:
			print(sharer.values)
			return sharer.values[self.alias]
		else:
			return self.alias


class PongOutcomingPacket(OutcomingPacket):
	def __init__(self):
		super().__init__()
		self.alias = 'pong'

	def build(self, encoded=False, sharer=None):
		return [self.format(encoded, sharer), None]


class HitOutcomingPacket(OutcomingPacket):
	def __init__(self, hit):
		super().__init__()
		self.alias = 42

		self.hit = hit

	def build(self, encoded=False, sharer=None):
		self.hit[0] = -1
		return [self.format(encoded, sharer), self.hit]


class SnapshotOutcomingPacket(OutcomingPacket):
	def __init__(self, game):
		super().__init__()
		self.alias = 'snapshot'

		self.ended = game.ended
		self.innerWidth = game.world.map.width
		self.innerHeight = game.world.map.height
		#self.lifetime = 1
		self.mapData = game.world.map.data
		self.sharedKeys = game.sharer.encoded
		self.entities = self.make_entities_list(game.world.entities, game.sharer)

	def build(self, encoded=False, sharer=None):
		return [self.format(encoded, sharer), {'ended': self.ended, 'entities': self.entities, 'innerWidth': self.innerWidth, 'innerHeight': self.innerHeight, 'lifetime': 1, 'mapData': self.mapData, 'mapName': '', 'mode': 'fun', 'sharedKeys': self.sharedKeys, 'speed': 1}]

	def make_entities_list(self, entities, sharer):
		l = []

		for entity in entities.entities:
			l.append(entity.encode(sharer))

		return l


class PrivateOutcomingPacket(OutcomingPacket):
	def __init__(self, data):
		super().__init__()
		self.alias = 'private'

		self.data = data

	def build(self, encoded=False, sharer=None):
		return [self.format(encoded, sharer), self.data]


class UpdateOutcomingPacket(OutcomingPacket):
	def __init__(self, entities, last_clients, clients):
		super().__init__()
		self.alias = 'update'

		self.entities = entities
		self.clients = None

		if (clients != last_clients):
			self.clients = clients

	def build(self, encoded=False, sharer=None):
		p = [self.format(encoded, sharer), {'entities': self.entities, 'lifetime': 0, 'queue': []}]

		if self.clients != None:
			p[1]['clients'] = self.clients

		return p


class SayOutcomingPacket(OutcomingPacket):
	def __init__(self, system, text):
		super().__init__()
		self.alias = 'say'

		self.system = system
		self.text = text

	def build(self, encoded=False, sharer=None):
		return [self.format(encoded, sharer), {'system': self.system, 'text': self.text}]


class SetPlayerCitizenOutcomingPacket(OutcomingPacket):
	def __init__(self, citizen):
		super().__init__()
		self.alias = 'setPlayersCitizen'

		self.citizen = citizen

	def build(self, encoded=False, sharer=None):
		return [self.format(encoded, sharer), {'sid': self.citizen.sid}]
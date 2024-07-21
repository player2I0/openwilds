import math

import game_util.utility as utility
import game_util.entities.entity as entity

class CitizenWeaponSlash(entity.Entity):
	def __init__(self, citizen, angle, game=None):
		super().__init__()
		self.citizen = citizen

		self.angle = angle
		self.range = 0
		self.arc = math.pi
		self.timer = 0
		self.damage = 0
		self.p_hitbox = CitizenWeaponSlashHitbox(self)
		self.damaged_entities = []

		if game != None:
			game.world.entities.groups.add('slashes', self)

	def step(self, dt, game):
		self.timer -= dt

		if self.timer <= 0:
			game.world.entities.remove(self)
			self.citizen.p_weapon_slash = None

	def calc(self):
		self.start_ang = self.angle - self.arc / 2
		self.end_ang = self.angle + self.arc / 2

	def is_point_inside(self, x, y):
		ang = utility.angle_towards_pos(self.citizen.x, self.citizen.y, x, y)

		if (ang >= self.start_ang and ang <= self.end_ang) and (utility.distance_between_points(self.citizen.x, self.citizen.y, x, y) <= self.range):
			return True
		else:
			return False

	def is_entity_inside(self, entity):
		return self.is_point_inside(entity.x, entity.y)

	def damage_entity(self, entity, game):
		if entity != self.citizen and not entity.p_is_dead and entity not in self.damaged_entities and self.is_entity_inside(entity):
			entity.damage(self.damage)

			if entity.p_is_dead:
				entity.p_pulse.set(timer=1.5, direction=utility.angle_towards_pos(self.citizen.x, self.citizen.y, entity.x, entity.y), distance=350, const_distance=False)
			else:
				entity.p_pulse.set(timer=0.3, direction=utility.angle_towards_pos(self.citizen.x, self.citizen.y, entity.x, entity.y), distance=500, const_distance=False)

			self.damaged_entities.append(entity)
			game.world.entities.groups.add('hits', Hit(sharer=game.sharer, entity_sid=entity.sid, attacker_sid=self.citizen.sid, damage=self.damage, fatal=entity.p_is_dead))


class CitizenWeaponSlashHitbox:
	def __init__(self, slash):
		self.slash = slash

	def get_absolute_coordinates(self):
		return [(int(-self.slash.range + self.slash.citizen.x), int(self.slash.range + self.slash.citizen.x)), (int(-self.slash.range + self.slash.citizen.y), int(self.slash.range + self.slash.citizen.y))]


class CitizenAxeSlash(CitizenWeaponSlash):
	def __init__(self, citizen, angle, game=None):
		super().__init__(citizen, angle, game)

		self.timer = 0.5
		self.range = 60
		self.damage = 2

		self.calc()


class CitizenAxeSpinSlash(CitizenWeaponSlash):
	def __init__(self, citizen, angle, game=None):
		super().__init__(citizen, angle, game)

		self.timer = 0.6
		self.range = 60
		self.damage = 2
		#self.arc = 2 * math.pi

		self.calc()

	def is_point_inside(self, x, y):
		if utility.distance_between_points(self.citizen.x, self.citizen.y, x, y) <= self.range:
			return True
		else:
			return False


class Hit(entity.Entity):
	def __init__(self, sharer, armor=0, projectile_sid=0, entity_sid=0, attacker_sid=0, kick=False, missile=False, blocked=False, damage=0, fall=False, stun=False, crush=False, fatal=False, reverse=False, blockBroken=False):
		super().__init__()

		self.armor = armor #-1 = no armor
		self.projectile_sid = projectile_sid #0 = no projectile
		self.entity_sid = entity_sid #entity that got hit
		self.attacker_sid = attacker_sid
		self.kick = kick
		self.missile = missile
		self.blocked = blocked
		self.damage = damage
		self.fall = fall
		self.stun = stun
		self.crush = crush
		self.fatal = fatal
		self.reverse = reverse
		self.blockBroken = blockBroken

		self.p_changes.add_all_properties(sharer)
		self.p_is_entity = False
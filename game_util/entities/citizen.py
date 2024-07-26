import math

import game_util.utility as utility
import game_util.entities.entity as entity
import game_util.entities.citizen_private_data as citizen_private_data
import game_util.entities.citizen_states as citizen_states
import game_util.entities.citizen_slashes as citizen_slashes
import game_util.entities.citizen_skills as citizen_skills

class Citizen(entity.Entity): #canon entity
	def __init__(self, sharer, game):
		super().__init__()
		#constructorName will be inserted...
		self.remove = False
		self.x = 0
		self.y = 0
		self.key = ''
		self.growling = False
		self.moving = 0
		self.stateQueue = citizen_states.CitizenStateManager(self, game)
		self.direction = 0
		self.kills = 0
		self.team = 0
		self.name = ''
		self.dead = False
		self.health = 0
		self.maxHealth = 0
		self.armor = 0
		self.score = 0
		self.flag = ''
		self.kind = ''
		self.frozen = 0
		self.gameLink = 0
		self.weapon = ''
		self.helmet = ''
		self.shield = ''
		self.voice = ''
		self.badges = {}
		self.cape = ''
		self.partner_sid = 0

		self.p_connection = None #properties starting with p_ will be ignored in encoding
		self.p_movement_vector = (0, 0)
		self.p_private = citizen_private_data.CitizenPrivateData(self, sharer)
		self.p_movement_speed = 150
		#self.p_pressed = False #indicates whether player pressed left mouse button or not
		self.p_hitbox = CitizenHitBox(self)
		self.p_weapon_slash = None
		self.p_inputs = CitizenInputs(self)
		self.p_pulse = entity.EntityPulse(self)
		self.p_is_dead = False
		self.p_skills = citizen_skills.CitizenSkills(self)

	def step(self, game, dt, overlaps):
		if not self.p_is_dead and self.stateQueue.state.alias not in ['fallFront', 'fallBack']:
			self.p_inputs.step(dt)
			self.stateQueue.state.step(dt, game)
			self.p_pulse.step(dt)

			if self.p_weapon_slash != None:
				self.p_weapon_slash.step(dt, game)

			if self.stateQueue.state.alias == 'spin':
				dire = (math.cos(self.direction), math.sin(self.direction))
				self.x += dire[0]*(150*(self.stateQueue.state.timer*2)) * dt
				self.y += dire[1]*(150*(self.stateQueue.state.timer*2)) * dt
				
				self.p_changes.add('x')
				self.p_changes.add('y')

			if self.stateQueue.state.alias == 'charge':
				if self.p_private.stamina > 0:
					self.p_private.stamina -= 0.5 * dt
					self.p_private.p_changes.add('stamina')
				else:
					self.stateQueue.state.set(citizen_states.CitizenStateAttack(self.stateQueue))

			if self.stateQueue.state.alias == 'jumpAttack':
				dire = (math.cos(self.direction), math.sin(self.direction))
				self.x += dire[0]*(150*(self.stateQueue.state.timer*2)) * dt
				self.y += dire[1]*(150*(self.stateQueue.state.timer*2)) * dt

				self.p_changes.add('x')
				self.p_changes.add('y')

			if self.stateQueue.state.alias not in ['jumpAttack', 'roll', 'kick']:
				if self.stateQueue.state.alias != 'spin':
					if self.growling:
						self.p_movement_speed = 180
						if self.p_movement_vector != (0, 0):
							if self.p_private.stamina > 0:
								self.p_private.stamina -= 0.3 * dt
								self.p_private.p_changes.add('stamina')
								#await self.ws.send(msgpack.packb(['private', [2, formatValueDescriptor(self.private.p['stamina'], 'sfloat')]]))
								#await self.ws_send(['private', [2, formatValueDescriptor(self.private.p['stamina'], 'sfloat')]])
							else:
								self.growling = False
								self.p_changes.add('growling')
					else:
						if self.stateQueue.state.alias == 'idle':
							if self.p_private.stamina < 1:
								self.p_private.stamina += 0.1 * dt
								self.p_private.p_changes.add('stamina')
								#await self.ws.send(msgpack.packb(['private', [2, formatValueDescriptor(self.private.p['stamina'], 'sfloat')]]))
								#await self.ws_send(['private', [2, formatValueDescriptor(self.private.p['stamina'], 'sfloat')]])
						self.p_movement_speed = 150

				self.p_movement_vector = utility.normvec(self.p_movement_vector)
				final_movement = (self.p_movement_vector[0] * self.p_movement_speed, self.p_movement_vector[1] * self.p_movement_speed)
				#print(final_movement)
				self.x += final_movement[0] * dt
				self.y += final_movement[1] * dt

				if final_movement != (0, 0):
					self.p_changes.add('x')
					self.p_changes.add('y')

			self.process_collisions(game, dt, overlaps)
		else:
			self.stateQueue.state.step(dt, game)
			self.p_pulse.step(dt)

	def process_collisions(self, game, dt, overlaps):
		blacklisted_states = ['roll', 'jumpAttack']

		for entity in overlaps:
			if entity.constructorName == 'Citizen' and not entity.p_is_dead and entity.stateQueue.state.alias not in blacklisted_states and self.stateQueue.state.alias not in blacklisted_states:
				m = utility.angle_towards_pos(self.x, self.y, entity.x, entity.y)
				dire = (math.cos(m), math.sin(m))
				entity.x += dire[0] * self.p_movement_speed/2 * dt
				entity.y += dire[1] * self.p_movement_speed/2 * dt
				entity.p_changes.add('x')
				entity.p_changes.add('y')

				self.x -= dire[0] * self.p_movement_speed/2 * dt
				self.y -= dire[1] * self.p_movement_speed/2 * dt
				self.p_changes.add('x')
				self.p_changes.add('y')

			elif entity.constructorName == 'CitizenWeaponSlash':
				entity.damage_entity(self, game)


	def slash(self, game):
		aliases = ['attack', 'spin', 'jumpAttack']
		skills = {'kick': citizen_slashes.CitizenSkillKickSlash, 'roll': citizen_slashes.CitizenSkillRollSlash}
		classes = {'axe': [citizen_slashes.CitizenAxeSlash, citizen_slashes.CitizenAxeSpinSlash, citizen_slashes.CitizenAxeJumpAttackSlash]}
		cl = None

		if self.stateQueue.state.alias not in skills:
			cl = classes[self.weapon][aliases.index(self.stateQueue.state.alias)]
		else:
			cl = skills[self.stateQueue.state.alias]

		if cl != None:
			self.p_weapon_slash = cl(self, self.direction, game)

	def damage(self, dmg):
		if self.health > 0:
			self.health -= dmg
			self.p_changes.add('health')

		self.die()

	def die(self):
		if self.health <= 0 and not self.p_is_dead:
			self.stateQueue.set(citizen_states.CitizenStateDying(self.stateQueue))


class CitizenInputs:
	def __init__(self, citizen):
		self.citizen = citizen

		self.lmb_pressed = False
		self.lmb_timer = 0

	def step(self, dt):
		'''
		if self.lmb_pressed and (self.citizen.stateQueue.state == 'idle' or self.citizen.stateQueue.state == 'charge'):
			self.lmb_timer += dt

		if self.citizen.stateQueue.state == 'idle' or self.citizen.stateQueue.state == 'charge':
			if self.lmb_pressed:
				if self.citizen.p_private.stamina > 0:
					self.lmb_timer += dt
					self.citizen.stateQueue.soft_set('charge')
				else:
					self.citizen.stateQueue.set('attack')
					self.lmb_release()
			if not self.lmb_pressed and self.citizen.stateQueue.state == 'charge':
				self.lmb_release()
				self.citizen.stateQueue.set('attack')
		elif self.citizen.stateQueue.state == 'jump' and self.lmb_pressed:
			self.citizen.stateQueue.soft_set('attack')
			self.lmb_release()
		'''

		if self.lmb_pressed: 
			if self.citizen.stateQueue.state.alias == 'idle' or self.citizen.stateQueue.state.alias == 'charge': #only count if citizen is idle or charging
				self.lmb_timer += dt
				self.citizen.stateQueue.state.set(citizen_states.CitizenStateCharge(self.citizen.stateQueue))
			elif self.citizen.stateQueue.state.alias == 'jump':
				self.citizen.stateQueue.state.set(citizen_states.CitizenStateAttack(self.citizen.stateQueue))
		else:
			if self.citizen.stateQueue.state.alias == 'charge':
				self.citizen.stateQueue.state.set(citizen_states.CitizenStateAttack(self.citizen.stateQueue))


	def lmb_release(self):
		self.lmb_pressed = False
		self.lmb_timer = 0


class CitizenHitBox(entity.EntityHitBox):
	def __init__(self, citizen):
		super().__init__(citizen)

		self.min = (-9, 9)
		self.max = (9, -9)

	def get_absolute_coordinates(self):
		#return [(int(self.min[0] + self.entity.x), int(self.min[1] + self.entity.y)), (int(self.max[0] + self.entity.x), int(self.max[1] + self.entity.y))]
		return [(int(self.min[0] + self.entity.x), int(self.max[0] + self.entity.x)), (int(self.max[1] + self.entity.y), int(self.min[1] + self.entity.y))]
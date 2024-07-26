import time

import game_util.entities.entity as entity
import game_util.utility as utility

class PlayerPrivateData(entity.Entity): #canon entity
	def __init__(self, entity, sharer):
		super().__init__()

		self.items = [{'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}]
		self.stamina = 1
		self.temperature = 1
		self.cooldowns = PlayerPrivateDataSkills(self)
		self.gold_cap = 12000
		self.gold_inc = 0
		self.interactor_sid = 0
		self.exp = 0

		del self.sid

		for property in self.__dict__:
			if property != 'sid' and property != 'constructorName' and property.find('p_') == -1:
				self.p_changes.add(property, sharer) #because at the start we need 255 change hash

		self.p_citizen = entity
		self.p_is_entity = False

	def step(self, game, dt):
		if len(self.p_citizen.p_skills.used_skills) > 0 and time.time() - self.cooldowns.last_encode >= 0.1:
			self.p_changes.add('cooldowns', game.sharer)


class PlayerPrivateDataSkills:
	def __init__(self, private):
		self.private = private

		self.last_encode = 0

	def encode(self, sharer=None): #in this parcticular method the sharer is not needed
		en = {}

		for skill in self.private.p_citizen.p_skills.used_skills.copy():
			skill_object = self.private.p_citizen.p_skills.skills[skill]
			en[skill] = skill_object.cooldown - (time.time() - skill_object.last_time_used)

			if en[skill] <= 0:
				en[skill] = 0
				self.private.p_citizen.p_skills.used_skills.remove(skill)

		self.last_encode = time.time()

		return en
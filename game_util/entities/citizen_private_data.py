import game_util.entities.entity as entity

class CitizenPrivateData(entity.Entity): #canon entity
	def __init__(self, entity, sharer):
		super().__init__()

		self.items = [{'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}]
		self.stamina = 1
		self.temperature = 1
		self.cooldowns = {}
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
import game_util.utility as utility

class Entity: #special entity
	def __init__(self):
		self.sid = 0
		self.constructorName = self.__class__.__name__
		self.p_changes = EntityChanges(self) #those properties which start with p_ will be ignored in the encoding functions
		self.p_is_entity = True
		self.p_group = None

	def encode(self, sharer):
		en = []

		for property in sharer.descriptors[self.constructorName]:
			en.append(utility.format_descriptor_value(self.__dict__[property[0]], property[1], sharer))
		#print(en)

		return en


class EntityHitBox: #special entity
	def __init__(self, entity):
		self.entity = entity

		self.min = (0, 0) #bottom-left corner
		self.max = (0, 0) #top-right corner


class EntityChanges: #special entity
	def __init__(self, entity):
		self.entity = entity
		self.properties = []
		self.hash = 0b0

	def add(self, property_name, sharer=None):
		if property_name not in self.properties:
			self.properties.append(property_name)

	def add_all_properties(self, sharer):
		for descriptor_property in sharer.descriptors_dict[self.entity.__class__.__name__]:
			self.add(descriptor_property)

	def encode(self, sharer):
		en = []

		if self.entity.p_is_entity:
			self.add('sid', sharer)

		l = list(sharer.descriptors_dict[self.entity.__class__.__name__])

		for descriptor_property in sharer.descriptors_dict[self.entity.__class__.__name__]:
			if descriptor_property in self.properties:
				self.hash |= (1<<l.index(descriptor_property))
				en.append(utility.format_descriptor_value(getattr(self.entity, descriptor_property), sharer.descriptors_dict[self.entity.__class__.__name__][descriptor_property], sharer))

		en.insert(0, self.hash)
		#print(en)

		self.properties = []
		self.hash = 0b0
		return en

	def sort_properties(self, descriptor):
		prop = []

		for property in descriptor:
			if property in self.properties:
				prop.append(property)

		self.properties = prop


class EntityProperty: #special entity
	def __init__(self, entity, property_name):
		self.entity = entity
		self.property_name = property_name


class EntityPulse: #special utility that makes entity slide in desired direction for n seconds
	def __init__(self, entity):
		self.entity = entity

		self.timer = 0
		self.start_timer = 0
		self.direction = 0
		self.distance = 0
		self.const_distance = False

	def set(self, timer=0, direction=0, distance=0, const_distance=False):
		self.timer = timer
		self.start_timer = timer
		self.direction = direction
		self.distance = distance
		self.const_distance = const_distance

	def step(self, dt):
		self.timer -= dt

		if self.timer > 0:
			vector = utility.angle_to_vector(self.direction)

			if self.const_distance:
				self.entity.x += (vector[0] * self.distance) * dt
				self.entity.y += (vector[1] * self.distance) * dt
			else:
				self.entity.x += ((vector[0] * self.distance) * (self.timer / self.start_timer)) * dt
				self.entity.y += ((vector[1] * self.distance) * (self.timer / self.start_timer)) * dt
			
			self.entity.p_changes.add('x')
			self.entity.p_changes.add('y')
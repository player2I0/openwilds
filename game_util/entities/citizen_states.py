'''
class CitizenStateManager: #special entity
	def __init__(self, citizen):
		self.citizen = citizen

		self.state = 'idle'
		self.timer = 0

		self.durations = {"idle": 0, "jump": 1, "attack": 0.5, 'jumpAttack': 1, 'charge': 0.6, 'spin': 0.6}

	def set(self, state):
		self.state = state
		self.timer = self.durations[state]
		self.citizen.p_changes.add('stateQueue')

		if state == 'attack' or state == 'spin':
			self.citizen.p_inputs.lmb_release()

	def step(self, game, dt):
		self.timer -= dt

		if self.timer <= 0:
			if self.state == 'charge':
				self.set('spin')
			elif self.state != 'idle':
				self.set('idle')

	def soft_set(self, state):
		if self.timer <= 0:
			self.set(state)
		else:
			if self.state == 'jump' and state == 'attack':
				self.set('jumpAttack')

	def encode(self, sharer):
		return [sharer.values[self.state]]
'''


class CitizenStateManager:
	def __init__(self, citizen, game):
		self.citizen = citizen
		self.game = game

		self.state = CitizenStateIdle(self)

	def set(self, state):
		self.state = state
		self.state.after_serialization()
		self.citizen.p_changes.add('stateQueue')

	def encode(self, sharer):
		return [sharer.values[self.state.alias]]


class CitizenState:
	def __init__(self, manager):
		self.manager = manager

		self.timer = 0
		self.alias = ''

	def step(self, dt, game):
		self.timer -= dt

		if self.timer <= 0:
			self.manager.set(CitizenStateIdle(self.manager))

	def set(self, state):
		pass

	def after_serialization(self):
		pass


class CitizenStateIdle(CitizenState):
	def __init__(self, manager=None):
		super().__init__(manager)

		self.alias = 'idle'

	def step(self, dt, game):
		pass

	def set(self, state):
		if state.alias == 'attack' or state.alias == 'jump' or state.alias == 'charge':
			self.manager.set(state)


class CitizenStateAttack(CitizenState):
	def __init__(self, manager=None):
		super().__init__(manager)

		self.alias = 'attack'
		self.timer = 0.5

		self.manager.citizen.p_inputs.lmb_release()

	def after_serialization(self):
		self.manager.citizen.slash(self.manager.game)


class CitizenStateJump(CitizenState):
	def __init__(self, manager=None):
		super().__init__(manager)

		self.alias = 'jump'
		self.timer = 1

		self.manager.citizen.p_inputs.lmb_release()

	def set(self, state):
		if state.alias == 'attack':
			self.manager.set(CitizenStateJumpAttack(self.manager))


class CitizenStateJumpAttack(CitizenState):
	def __init__(self, manager=None):
		super().__init__(manager)

		self.alias = 'jumpAttack'
		self.timer = 1

	def after_serialization(self):
		self.manager.citizen.slash(self.manager.game)


class CitizenStateCharge(CitizenState):
	def __init__(self, manager=None):
		super().__init__(manager)

		self.alias = 'charge'
		self.timer = 0.6

	def step(self, dt, game):
		self.timer -= dt

		if self.timer <= 0:
			self.manager.set(CitizenStateSpin(self.manager))

	def set(self, state):
		if state.alias == 'attack':
			self.manager.set(CitizenStateAttack(self.manager))


class CitizenStateSpin(CitizenState):
	def __init__(self, manager=None):
		super().__init__(manager)

		self.alias = 'spin'
		self.timer = 0.6

		self.manager.citizen.p_inputs.lmb_release()

	def after_serialization(self):
		self.manager.citizen.slash(self.manager.game)


class CitizenStateDying(CitizenState):
	def __init__(self, manager=None):
		super().__init__(manager)

		self.alias = 'dying'
		self.timer = 1.5

		#print(self.manager.citizen.p_pulse.timer)
		self.manager.citizen.p_is_dead = True
		#self.manager.citizen.p_pulse.set(timer=1.5, direction=self.manager.citizen.direction, distance=500, const_distance=False)

	def step(self, dt, game):
		self.timer -= dt

		if self.timer <= 0:
			self.manager.set(CitizenStateDead(self.manager))


class CitizenStateDead(CitizenState):
	def __init__(self, manager=None):
		super().__init__(manager)

		self.alias = 'dying'
		self.timer = 0

		self.manager.citizen.dead = True
		self.manager.citizen.p_changes.add('dead')

	def step(self, dt, game):
		pass


class CitizenStateBlock(CitizenState):
	def __init__(self, manager=None):
		super().__init__(manager)

		self.alias = 'block'
		self.timer = 1


class CitizenStateRoll(CitizenState):
	def __init__(self, manager=None):
		super().__init__(manager)

		self.alias = 'roll'
		self.timer = 0.8

	def after_serialization(self):
		self.manager.citizen.p_pulse.set(timer=0.8, direction=self.manager.citizen.direction, distance=200, const_distance=True)
		self.manager.citizen.slash(self.manager.game)


class CitizenStateKick(CitizenState):
	def __init__(self, manager=None):
		super().__init__(manager)

		self.alias = 'kick'
		self.timer = 0.8

	def after_serialization(self):
		self.manager.citizen.p_pulse.set(timer=0.8, direction=self.manager.citizen.direction, distance=200, const_distance=False)
		self.manager.citizen.slash(self.manager.game)


class CitizenFallBack(CitizenState):
	def __init__(self, manager=None):
		super().__init__(manager)

		self.alias = 'fallBack'
		self.timer = 1.4
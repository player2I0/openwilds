import time
import game_util.entities.citizen_states as citizen_states

class CitizenSkills:
	def __init__(self, entity):
		self.citizen = entity

		self.skills = {}

		self.add(CitizenSkillBlock(self))
		self.add(CitizenSkillRoll(self))
		self.add(CitizenSkillJump(self))
		self.add(CitizenSkillKick(self))

	def add(self, skill):
		self.skills[skill.alias] = skill
		setattr(self, skill.alias, skill)


class CitizenSkill:
	def __init__(self, skills=None):
		self.alias = 'skill'
		self.cooldown = 0
		self.last_time_used = 0
		self.skills = skills
		self.state = citizen_states.CitizenStateIdle

	def use(self):
		if (time.time() - self.last_time_used >= self.cooldown) and self.skills.citizen.stateQueue.state.alias == 'idle':
			self.last_time_used = time.time()

			self.skills.citizen.stateQueue.set(self.state(self.skills.citizen.stateQueue))


class CitizenSkillBlock(CitizenSkill):
	def __init__(self, skills=None):
		super().__init__(skills)

		self.alias = 'block'
		self.cooldown = 1.8
		self.state = citizen_states.CitizenStateBlock


class CitizenSkillRoll(CitizenSkill):
	def __init__(self, skills=None):
		super().__init__(skills)

		self.alias = 'roll'
		self.cooldown = 1
		self.state = citizen_states.CitizenStateRoll


class CitizenSkillJump(CitizenSkill):
	def __init__(self, skills=None):
		super().__init__(skills)

		self.alias = 'jump'
		self.cooldown = 1
		self.state = citizen_states.CitizenStateJump


class CitizenSkillKick(CitizenSkill):
	def __init__(self, skills=None):
		super().__init__(skills)

		self.alias = 'kick'
		self.cooldown = 1.8
		self.state = citizen_states.CitizenStateKick
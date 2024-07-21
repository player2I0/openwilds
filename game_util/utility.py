import inspect
import math

import game_util.entities.citizen as citizen
import game_util.entities.citizen_states as citizen_states
import game_util.entities.entity as entity
import game_util.entities.player_private_data as player_private_data

def format_descriptor_value(val, type, sharer):
	if type == 'sfloat':
		return int(round(val, 1)*10)
	elif type == 'float':
		return int(round(val, 2)*100)
	elif type == 'int':
		return int(val)
	elif type == 'key':
		return sharer.values[val]
	elif val.__class__.__name__ in vars(citizen) or val.__class__.__name__ in vars(entity) or val.__class__.__name__ in vars(player_private_data) or val.__class__.__name__ in vars(citizen_states): # check if val is a class in citizen.py. for example, it is statequeue of citizen
		return val.encode(sharer)
	else:
		return val

def addvec(a, b):
	return (a[0] + b[0], a[1] + b[1])

def normvec(vec):
	length = (vec[0]**2 + vec[1]**2)**0.5
	if length == 0:
		return (0, 0)
	return (vec[0] / length, vec[1] / length)

def positive_radians(rad):
	if rad < 0:
		return math.pi * 2 + rad
	elif rad > math.pi * 2:
		return rad - math.pi * 2
	else:
		return rad

def angle_towards_pos(x1, y1, x2, y2):
	return positive_radians(math.atan2((y2)-y1, (x2)-x1))

def distance_between_points(x1, y1, x2, y2):
	return math.sqrt((x2 - x1)**2 + (y2 - y1) ** 2)

def angle_to_vector(ang):
	return (math.cos(ang), math.sin(ang))
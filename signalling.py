import asyncio
import websockets
import json

class SignallingServer:
	def __init__(self, master):
		self.master = master

		self.CONNECTIONS = {}
		self.idnums = {'peer': 0}
		self.pl = {}

	async def main(self):
		async with websockets.serve(self.handler, "localhost", self.master.config['main_port']):
			print('started signalling websocket!')
			await asyncio.Future()  # run forever

	async def handler(self, websocket):
		id = str(self.idnums['peer'])
		self.idnums['peer'] += 1
		#pl[id] = {}
		self.CONNECTIONS[id] = websocket
		self.pl[id] = {"locale": 'NA', "date": 0, "flag": "xx"}
		await websocket.send('''[ "status", { "counts": { "fun": 6 }, "maxMMR": { "graveyard_score": 1565, "flags": 2475, "goals": 2151, "bones": 25000, "arena_mmr": 1267 }, "mmcounts": { "soccer": 0 } } ]''')
		#["ask",{"token":"03AFcWeA4zt-drtbTCLgc5BDHLBOAq5lFeRVYouvM3Epq6RZ1PAIce5p-Nn_JIWYfCe9mmECnqIeardeMAcLyRjB5TwnmwoqgrcekxzDP5UptCa-AvEePtd4uomOJzJlWCEOXE_vlmuaS5dUbyWSpra5EGPTQtkZzmKUHIO6Xo5RsHcTpc0UmtDzz9S_eZ4Cp2JAfRyLSOwYBIbfeiaYTUTPNgRePh6rYASXAWa6u27b5lek18mIaeHiLXD6K6A7qdRWZPKbjMZ2P-0y_gSgm9TKqY6zKfReF6mzyevdz0SrLQMmYSpZcAt0GOOAjBpbpJUa3fJwFE9pKYLOW7_joI67UDnoKUY219yccTBiSJ8pxqn_0ssoYnKM4wth4JhxaovJRx7jHzDwvjUde5mgpTtszwGDnIdOxe17IzBB54I5GV4DQWoA_mvXUMbXalbWbs4IMkal1QLIg5zOG2JYb5RHre63uYHOcfMKBq-GLvX52zVkBoz0WTqRwUYdSfS9zORjULW3Bkzw-v55X3aCz47u_juSmmw95thA","question":"captcha","request_id":1}]
		async for message in websocket:
			msg = json.loads(message)
			if msg[0] == "set_location":
				self.pl[id]['locale'] = msg[1]
			if msg[0] == "date":
				self.pl[id]['date'] = msg[1]
			if msg[0] == "set_flag":
				self.pl[id]['flag'] = msg[1]
			if msg[0] == 'ask':
				if msg[1]['question'] == "captcha":
					await websocket.send('["response", {"request_id":'+str(msg[1]['request_id']) + '}]')
			if msg[0] == 'play':
				await websocket.send('["game_ready",{"url":"localhost","seat_id":"0","mode":"fun"}]')
			#print(message)
			
			#greeting = f"Hello {name}!"
			#await websocket.send(greeting)
			#print(f">>> {greeting}")
		try:
			await websocket.wait_closed()
		finally:
			del self.CONNECTIONS[id]
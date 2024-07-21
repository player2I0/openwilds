import asyncio
import websockets
import json

import signalling
import game

class Master:
	def __init__(self):
		self.config = ''

		with open('config.json', 'r') as f:
			self.config = json.loads(f.read())

		self.game = game.Game(self)
		self.signalling_server = signalling.SignallingServer(self)

async def main(master):
	await asyncio.gather(master.signalling_server.main(), master.game.main(), master.game.launch_game_loop(1/20))

if __name__ == "__main__":
	#p = Process(target=main_loop, args=())
	#p.start()
	#p.join()

	master = Master()
	
	asyncio.run(main(master))
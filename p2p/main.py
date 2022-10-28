import os
from asyncio import Task, as_completed, ensure_future, get_event_loop, new_event_loop, set_event_loop
from dataclasses import dataclass

from pyipv8.ipv8.community import Community
from pyipv8.ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from pyipv8.ipv8.lazy_community import lazy_wrapper
from pyipv8.ipv8.messaging.payload_dataclass import overwrite_dataclass
from pyipv8.ipv8_service import IPv8

import string
import random
from threading import Thread
from threading import Event

def id_generator(size):
	return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(size))

dataclass = overwrite_dataclass(dataclass)  # Enhance normal dataclasses for IPv8 (see the serialization documentation)

@dataclass(msg_id=1)  # The (byte) value 1 identifies this message and must be unique per community
class MyMessage:
	text: str

class MyCommunity(Community):
	community_id = bytes([254,10,128,88,75,5,188,130,10,151,179,240,26,88,125,221,44,223,239,217])

	def __init__(self, my_peer, endpoint, network):
		super().__init__(my_peer, endpoint, network)
		self.add_message_handler(MyMessage, self.on_message)

	def started(self):
		pass

	def send(self, item):
		for p in self.get_peers():
			self.ez_send(p, MyMessage(item))

	@lazy_wrapper(MyMessage)
	def on_message(self, peer, payload):
		print(peer, ':', payload.text)


def open_peer():
	class ipv8_holder:
		ipv8: IPv8 = None
	holder = ipv8_holder()
	event = Event()

	async def start_peer():
		builder = ConfigBuilder().clear_keys().clear_overlays()
		builder.add_key("my peer", "medium", "key.pem")
		builder.add_overlay("MyCommunity", "my peer", [WalkerDefinition(Strategy.RandomWalk, 10, {'timeout': 3.0})],
							default_bootstrap_defs, {}, [('started',)])
		ipv8 = IPv8(builder.finalize(), extra_communities={'MyCommunity': MyCommunity})
		await ipv8.start()
		return ipv8

	def work():
		set_event_loop(new_event_loop())
		future = ensure_future(start_peer())
		get_event_loop().run_until_complete(future)
		holder.ipv8 = future.result()
		event.set()
		get_event_loop().run_forever()
	
	Thread(target = work).start()
	event.wait()
	return holder.ipv8
		

ipv8 = open_peer()
while True:
	ipv8.get_overlay(MyCommunity).send(input())

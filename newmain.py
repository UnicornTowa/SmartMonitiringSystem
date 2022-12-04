import os
from asyncio import Task, as_completed, ensure_future, get_event_loop, new_event_loop, set_event_loop
from dataclasses import dataclass

from pyipv8.ipv8.community import Community
from pyipv8.ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition
from pyipv8.ipv8.configuration import Bootstrapper, BootstrapperDefinition, default_bootstrap_defs
from pyipv8.ipv8.lazy_community import lazy_wrapper
from pyipv8.ipv8.messaging.payload_dataclass import overwrite_dataclass
from pyipv8.ipv8_service import IPv8
from pyipv8.ipv8.peer import Peer

import string
import random
from threading import Thread
from threading import Event
import _thread

from time import sleep
from math import sqrt
from base64 import b64encode
from time import time

import glob
from imageai.Detection import VideoObjectDetection
import cv2
from PIL import Image
import imagehash as ih
from math import sqrt

current_hashes = []
upcoming_hashes = []

stop = 1

def write_to_upcoming(imagehash_str):
    imagehash_str = ih.hex_to_flathash(imagehash_str, 3)
    for obj in upcoming_hashes:
        if imagehash_str - obj <= 3:
            return
    upcoming_hashes.append(imagehash_str)


def write_to_current(imagehash):
    for obj in upcoming_hashes:
        if imagehash - obj <= 3:
            return
    current_hashes.append(imagehash)


dataclass = overwrite_dataclass(dataclass)  # Enhance normal dataclasses for IPv8 (see the serialization documentation)


@dataclass(msg_id=1)  # The (byte) value 1 identifies this message and must be unique per community
class MyMessage:
    text: str


class MyPeer:
    def __init__(self, peer: Peer, online: bool):
        self.peer = peer
        self.online = online

    def __eq__(self, other):
        self.peer.address
        return self.peer.mid == other.peer.mid


all_peers = {}
ids = []

class Person:
    hashim = 0
    line = []
    def __init__(self, hashim,coord):
        self.hashim = hashim
        self.line.append(coord)
    def new_coord(self,stack):
        self.line.append(stack)
class MyCommunity(Community):
    community_id = bytes([254, 10, 128, 88, 75, 5, 188, 130, 10, 151, 179, 240, 26, 88, 125, 221, 44, 223, 239, 217])

    def __init__(self, my_peer, endpoint, network):
        super().__init__(my_peer, endpoint, network)
        self.add_message_handler(MyMessage, self.on_message)

    def started(self):
        async def print_ip():
            ip = self.my_peer.address
            if ip[0] != "0.0.0.0":
                print("my ip: ", ip[0], ':', ip[1], sep="")
                self.cancel_pending_task("print_ip")

        async def save_peers():
            for p in all_peers.values():
                p.online = False
            for p in self.get_peers():
                all_peers[p.mid] = MyPeer(p, time() - p.last_response < 3)
            ids.clear()
            for p in list(all_peers.values()):
                ids.append(p.peer)

        # for p in all_peers.values():
        #	print(b64encode(p.peer.mid).decode('utf-8'), "\t: ", p.online)

        self.register_task("print_ip", print_ip, interval=0.5, delay=1)
        self.register_task("save_peers", save_peers, interval=5, delay=5)

    def send(self, item):
        for p in self.get_peers():
            self.ez_send(p, MyMessage(item))

    @lazy_wrapper(MyMessage)
    def on_message(self, peer, payload):
        message = str(payload.text)
        if message == 'startall':
            stop = 0
        if message[0] == '%':
            write_to_upcoming(message.split('%')[1])
        print(peer, ':', payload.text)


def open_peer():
    class ipv8_holder:
        ipv8: IPv8 = None

    holder = ipv8_holder()
    event = Event()

    async def start_peer():
        builder = ConfigBuilder().clear_keys().clear_overlays()
        builder.add_key("my peer", "medium", "key.pem")
        builder.add_overlay(
            "MyCommunity",
            "my peer",
            [WalkerDefinition(Strategy.RandomWalk, 10, {'timeout': 3.0})],
            [BootstrapperDefinition(Bootstrapper.UDPBroadcastBootstrapper, {})],
            {}, [('started',)])
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

    Thread(target=work).start()
    event.wait()
    return holder.ipv8


ipv8 = open_peer()

execution_path = os.getcwd()


def get_path(n):
    return os.path.join(execution_path, "output", "second" + str(n) + ".txt")


def get_distance(a, b):
    #  print("distance = " + str(int(sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))))
    return int(sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))


num_of_seconds = 1


def send_to_peer(num, message):
    if num == -1:
        return
    ipv8.get_overlay(MyCommunity).ez_send(ids[int(num)], MyMessage(message))


print('You should setup nodes to send messages correctly')
print('Enter "peers" to get list of peers')
print('Enter "test" to send test message')
print('Enter "setup" to make final preparations')
r = 0
l = 0
rs = 'left'
ls = 'right'

while stop:
    s = input()
    ipv8.get_overlay(MyCommunity).send(s)
    if s == "start" or s == 'startall':
        break
    if s == 'peers':
        print('List of your peers:')
        c = 0
        for p in all_peers.values():
            print('Peer', c, ':')
            c += 1
            print(b64encode(p.peer.mid).decode('utf-8'), "\t: ", p.online)
    if s == 'send':
        print('Enter number of peer to send test message, or Q to quit: ')
        n = input()
        if str(n) != 'Q':
            send_to_peer(int(n), 'Test message')
    if s == 'setup':
        r = int(input('Enter number of node which is on right or "-1" if there is no such node: '))
        if r != -1:
            rs = str(input('"right" if person will came from right side to that cam, "left" if not: '))
        l = int(input('Enter number of node which is on left or "-1" if there is no such node: '))
        if l != -1:
            ls = str(input('"right" if person will came from right side to that cam, "left" if not: '))
        print('Setup completed')
    sleep(0.05)

print("\nDetection started\n")

execution_path = os.getcwd()

cam = cv2.VideoCapture(0)

detector = VideoObjectDetection()
detector.setModelTypeAsYOLOv3()
detector.setModelPath(os.path.join(execution_path, "yolo.h5"))
detector.loadModel(detection_speed="flash")
custom = detector.CustomObjects(person=True)


def per_second(second_number, output_arrays, count_arrays, average_output_count, returned_frame):
    people = []
    for person in output_arrays[0]:
        people.append(Person(ih.colorhash(person["box_points"]), person["box_points"]))
    for i in range(1, 5):
        for person in output_arrays[i]:
            hashdif = []
            for sample in people:
                hashdif.append(ih.colorhash(person["box_points"])-sample.hashim)

            if min(hashdif) > 6:
                people.append(Person(ih.colorhash(person["box_points"]), person["box_points"]))
            else:
                ind = hashdif.index(min(hashdif))
                people[ind].new_coord(person["box_points"])
    for i in range(len(people)):
        line = people[i].line
        current_mid = []
        first_mid_x = 0
        first = True
        noreturn = False
        for j in range(5):
            center = [round((line[j][0] + line[j][2]) / 2), round((line[j][1] + line[j][3]) / 2)]
            if first:
                first_mid_x = center[0]
                current_mid = center
                first = False

            elif current_mid and get_distance(current_mid, center) < 100:
                current_mid = center
            else:
                noreturn = True
        if current_mid and first_mid_x and not noreturn:
            im = Image.fromarray(returned_frame).crop(line[0])
            hashim = ih.colorhash(im)
            for imhash in upcoming_hashes:
                if hashim - imhash <= 3:
                    write_to_current(hashim)
                    upcoming_hashes.pop(imhash)
                    print('Detected upcoming')
            diff = current_mid[0] - first_mid_x
            if abs(diff) < 50:
                print("STANDING")
            elif diff > 0:
                print("MOVING LEFT, sending")
                send_to_peer(l, 'Person is coming from ' + ls + ' side')
                send_to_peer(l, '%' + str(hashim))
                for imhash in current_hashes:
                    if imhash - hashim <= 3:
                        current_hashes.pop(imhash)
            else:
                print("MOVING RIGHT, sending")
                send_to_peer(r, 'Person is coming from ' + rs + ' side')
                send_to_peer(r, '%' + str(hashim))
                for imhash in current_hashes:
                    if imhash - hashim <= 3:
                        current_hashes.pop(imhash)


detector.detectObjectsFromVideo(camera_input=cam, custom_objects=custom,
                                save_detected_video=False,
                                frames_per_second=5,
                                per_second_function=per_second,
                                minimum_percentage_probability=70,
                                return_detected_frame=True
                                # , detection_timeout=10
                                )

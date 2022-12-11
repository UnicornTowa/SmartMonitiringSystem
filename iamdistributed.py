import os
from asyncio import ensure_future, get_event_loop, new_event_loop, set_event_loop
from base64 import b64encode
from dataclasses import dataclass
from math import sqrt
from threading import Event
from threading import Thread
from time import sleep
from time import time

import cv2
import imagehash as ih
from PIL import Image
from imageai.Detection import VideoObjectDetection

from pyipv8.ipv8.community import Community
from pyipv8.ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition
from pyipv8.ipv8.configuration import default_bootstrap_defs
from pyipv8.ipv8.lazy_community import lazy_wrapper
from pyipv8.ipv8.messaging.payload_dataclass import overwrite_dataclass
from pyipv8.ipv8.peer import Peer
from pyipv8.ipv8_service import IPv8

current_hashes = []
upcoming_hashes = []

stop = 1
r = -1
l = -1
rr = -1
ll = -1



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
    current_node = -1
    last_frame = -1

    def __init__(self, hashim, coord, frame):
        self.hashim = hashim
        self.line.append(coord)
        self.last_frame = frame

    def new_coord(self, stack):
        self.line.append(stack)

    def change_node(self, node):
        self.current_node = node

    def del_coord(self):
        self.line = []


def change_node(peer, hash):
    global people
    people_hash = [i.hashim for i in people]
    if hash in people_hash:
        ind = people_hash.index(hash)
        people[ind].del_coord()
        # people[ind].change_node(TODO поменять ноду)


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

        self.register_task("print_ip", print_ip, interval=0.5, delay=1)
        self.register_task("save_peers", save_peers, interval=5, delay=5)

    def send(self, item):
        for p in self.get_peers():
            self.ez_send(p, MyMessage(item))

    @lazy_wrapper(MyMessage)
    def on_message(self, peer, payload):
        global stop, r, l, rr, ll
        message = str(payload.text)
        if message != '':
            if "detect" in message:
                change_node(peer, message[message.index("%") + 1:])
            elif message == 'startall':
                stop = 0
            elif message[0] == '%':
                write_to_upcoming(message.split('%')[1])
            elif 'set!' in message:
                message = message.split(' ')
                if message[1] == 'r':
                    r = ids.index(peer)
                    print('Forced to new r')
                    send_to_peer(r, 'request! r')
                    send_to_peer(l, 'request! me')
                elif message[1] == 'l':
                    l = ids.index(peer)
                    print('Forced to new l')
                    send_to_peer(l, 'request! l')
                    send_to_peer(r, 'request! me')
            elif 'request!' in message:
                message = message.split(' ')
                if message[1] == 'me':
                    try:
                        ind = ids.index(peer)
                    except:
                        ind = -1
                    if r == ind and ind != -1:
                        send_to_peer(r, 'request! r')
                    elif l == ind and l != -1:
                        send_to_peer(l, 'request! l')
                elif message[1] == 'r':
                    if r == -1:
                        ipv8.get_overlay(MyCommunity).ez_send(peer, MyMessage('rr=' + '-1'))
                    else:
                        ipv8.get_overlay(MyCommunity).ez_send(peer, MyMessage('rr=' + b64encode(ids[int(r)].mid).decode('utf-8')))
                elif message[1] == 'l':
                    if l == -1:
                        ipv8.get_overlay(MyCommunity).ez_send(peer, MyMessage('ll=' + '-1'))
                    else:
                        ipv8.get_overlay(MyCommunity).ez_send(peer, MyMessage('ll=' + b64encode(ids[int(l)].mid).decode('utf-8')))
            elif 'rr=' in message:
                ident = message.split('rr=')[1]
                if ident == '-1':
                    rr = -1
                else:
                    for p in all_peers.values():
                        if b64encode(p.peer.mid).decode('utf-8') == ident:
                            rr = ids.index(p.peer)
                            print('new rr = ' + b64encode(ids[rr].mid).decode('utf-8'))
            elif 'll=' in message:
                ident = message.split('ll=')[1]
                if ident == '-1':
                    ll = -1
                else:
                    for p in all_peers.values():
                        if b64encode(p.peer.mid).decode('utf-8') == ident:
                            ll = ids.index(p.peer)
                            print('new ll = ' + b64encode(ids[ll].mid).decode('utf-8'))
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
            # [BootstrapperDefinition(Bootstrapper.UDPBroadcastBootstrapper, {})],
            default_bootstrap_defs,
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


def get_distance(a, b):
    return int(sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))


num_of_seconds = 1


def send_to_peer(num, message):
    if num == -1:
        return
    ipv8.get_overlay(MyCommunity).ez_send(ids[int(num)], MyMessage(message))


def get_status(num):
    if num == -1:
        return None
    return all_peers[ids[int(num)].mid].online


def check_rl():
    global r, rr, l, ll
    if r != -1 and not get_status(r):
        r = rr
        rr = -1
        print('moved to rr')
        print(ids[rr])
        send_to_peer(r, 'request! r')
        if r == -1:
            print('System broke into 2 sections')
    elif l != -1 and not get_status(l):
        l = ll
        ll = -1
        print('moved to ll')
        send_to_peer(l, 'request! l')
        if l == -1:
            print('System broke into 2 sections')
    if rr != -1 and not get_status(rr):
        send_to_peer(r, 'request! r')
    elif ll != -1 and not get_status(ll):
        send_to_peer(l, 'request! l')




print('You should setup nodes to send messages correctly')
print('Enter "peers" to get list of peers')
print('Enter "test" to send test message')
print('Enter "setup" to make final preparations')


if os.path.exists('config.txt'):
    s = input("Found old config, use it? Y/N: ")
    if s == 'Y' or s == 'y':
        with open('config.txt') as f:
            right = f.readline().split(' ')[0].split('r=')[1].rstrip()
            if right == '-1':
                r = -1
            else:
                for p in all_peers.values():
                    if b64encode(p.peer.mid).decode('utf-8') == right:
                        r = int(ids.index(p.peer))
                        print('found r')
                        send_to_peer(r, 'set! l')
                        send_to_peer(r, 'request! r')
            left = f.readline().split(' ')[0].split('l=')[1].rstrip()
            if left == '-1':
                l = -1
            else:
                for p in all_peers.values():
                    if b64encode(p.peer.mid).decode('utf-8') == left:
                        l = int(ids.index(p.peer))
                        print('found l')
                        send_to_peer(l, 'set! r')
                        send_to_peer(l, 'request! l')
            print('Use config: r = ' + str(r) + '\n' + 'l = ' + str(l))

ready = 0
peercount = len(ids)

while stop:
    if len(ids) > peercount:
        print("NEW PEER")
        peercount = len(ids)
    if not ready:
        s = input()
        ipv8.get_overlay(MyCommunity).send(s)
        if s == 'status':
            n = int(input())
            print(get_status(n))
        if s == 'ready':
            ready = 1
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
            if os.path.exists('config.txt'):
                os.remove('config.txt')
            with open('config.txt', 'w') as f:
                r = int(input('Enter number of node which is on right or "-1" if there is no such node: '))
                l = int(input('Enter number of node which is on left or "-1" if there is no such node: '))
                print('Setup completed')
                if r == -1:
                    f.write('r=-1\n')
                else:
                    f.write('r=' + b64encode(ids[r].mid).decode('utf-8') + '\n')
                if l == -1:
                    f.write('l=-1\n')
                else:
                    f.write('l=' + b64encode(ids[l].mid).decode('utf-8') + '\n')
                print('Config written')
        if s == 'rrll':
            if r != -1:
                send_to_peer(r, 'request! r')
            if l != -1:
                send_to_peer(l, 'request! l')
    sleep(0.05)


print("\nDetection started\n")

execution_path = os.getcwd()

cam = cv2.VideoCapture(0)

detector = VideoObjectDetection()
detector.setModelTypeAsYOLOv3()
detector.setModelPath(os.path.join(execution_path, "yolo.h5"))
detector.loadModel(detection_speed="flash")
custom = detector.CustomObjects(person=True)

people = []
old_people = []


def per_frame(frame_number, output_array, output_count, returned_frame):
    global people
    if (frame_number - 1) % 5 == 0:
        for person in people:
            # TODO костыль, по-другому не придумал
            person.del_coord()
    for person in output_array:
        if len(people) == 0:
            people.append(
                Person(ih.colorhash(Image.fromarray(returned_frame).crop(person["box_points"])), person["box_points"],
                       frame_number))
        else:
            hashdif = []
            for sample in people:
                hashdif.append(ih.colorhash(Image.fromarray(returned_frame).crop(person["box_points"])) - sample.hashim)

            if min(hashdif) > 6:
                people.append(Person(ih.colorhash(Image.fromarray(returned_frame).crop(person["box_points"])),
                                     person["box_points"], frame_number))
            else:
                ind = hashdif.index(min(hashdif))
                k = 1
                s_hashdif = sorted(hashdif)
                while people[ind].current_node not in [l, r, -1] and k != len(hashdif):
                    new_min = s_hashdif[k]
                    k += 1
                    ind = hashdif.index(new_min)
                if people[ind].current_node in [l, r, -1]:
                    people[ind].new_coord(person["box_points"])
                    people[ind].current_node = -1
                else:
                    people.append(Person(ih.colorhash(Image.fromarray(returned_frame).crop(person["box_points"])),
                                         person["box_points"], frame_number))


def per_second(second_number, output_arrays, count_arrays, average_output_count, returned_frame):
    check_rl()
    global people, r, l
    # print(ids)
    for i in range(len(people)):
        line = people[i].line
        current_mid = []
        first_mid_x = 0
        first = True
        noreturn = False
        for j in range(len(line)):
            center = [round((line[j][0] + line[j][2]) / 2), round((line[j][1] + line[j][3]) / 2)]
            if first:
                first_mid_x = center[0]
                current_mid = center
                first = False

            elif get_distance(current_mid, center) < 100:
                current_mid = center
            else:
                noreturn = True
        if not noreturn and current_mid:
            hashim = people[i].hashim
            for imhash in upcoming_hashes:
                if hashim - imhash <= 3:
                    write_to_current(hashim)
                    upcoming_hashes.remove(imhash)
                    send_to_peer(l, "detect %" + hashim)
                    send_to_peer(r, "detect %" + hashim)

                    print('Detected upcoming')
            diff = current_mid[0] - first_mid_x
            if abs(diff) < 50:
                print("STANDING")
            elif diff > 0:
                if int(l) == -1:
                    print('Person leaving left')
                else:
                    print("MOVING LEFT, sending to " + b64encode(ids[l].mid).decode('utf-8'))
                    send_to_peer(l, 'Person is coming')
                    send_to_peer(l, '%' + str(hashim))
                for imhash in current_hashes:
                    if imhash - hashim <= 3:
                        current_hashes.remove(imhash)
                        # TODO обновлять текующую ноду
            else:
                if int(r) == -1:
                    print('Person leaving right')
                else:
                    print("MOVING RIGHT, sending to " + b64encode(ids[r].mid).decode('utf-8'))
                    send_to_peer(r, 'Person is coming')
                    send_to_peer(r, '%' + str(hashim))
                for imhash in current_hashes:
                    if imhash - hashim <= 3:
                        current_hashes.remove(imhash)
                        # TODO обновлять текующую ноду


detector.detectObjectsFromVideo(camera_input=cam, custom_objects=custom,
                                save_detected_video=False,
                                frames_per_second=5,
                                per_frame_function=per_frame,
                                per_second_function=per_second,
                                minimum_percentage_probability=70,
                                return_detected_frame=True
                                # , detection_timeout=10
                                )

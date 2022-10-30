import os
from time import sleep
from math import sqrt

execution_path = os.getcwd()


def get_path(n):
    return os.path.join(os.getcwd(), "output", "second" + str(n) + ".txt")


def get_distance(a, b):
    #  print("distance = " + str(int(sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))))
    return int(sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))


num_of_seconds = 1

while True:
    path = get_path(num_of_seconds)
    if os.path.isfile(path):
        #  print("File number" + str(num_of_seconds))
        #  mid = []
        current_mid = []
        first_mid_x = 0
        first = True
        current_second = open(path, "r")
        noreturn = False
        for i in range(5):
            #  print("Frame number " + str(i + 1))
            line = current_second.readline()
            line = line.split("%")
            for person in line:
                if person and person != "\n":
                    person = person.split(" ")
                    center = [round((int(person[0]) + int(person[2])) / 2),
                              round((int(person[1]) + int(person[3])) / 2)]
                    if first:
                        first_mid_x = center[0]
                        current_mid = center
                        first = False
                        #  mid.append(center)

                    elif current_mid and get_distance(current_mid, center) < 100:
                        current_mid = center
                    else:
                        noreturn = True

                break
        # print(first_mid_x)
        # print(current_mid[0])
        if current_mid and first_mid_x and not noreturn:
            if current_mid[0] > first_mid_x:
                print("MOVING RIGHT")
            else:
                print("MOVING LEFT")
        num_of_seconds += 1
    else:
        sleep(0.05)

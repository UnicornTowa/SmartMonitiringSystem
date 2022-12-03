import os
from imageai.Detection import VideoObjectDetection
import cv2
from PIL import Image
import imagehash as ih
from math import sqrt

def get_distance(a, b):
    #  print("distance = " + str(int(sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))))
    return int(sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))

execution_path = os.getcwd()

cam = cv2.VideoCapture(0)

detector = VideoObjectDetection()
detector.setModelTypeAsYOLOv3()
detector.setModelPath(os.path.join(execution_path, "yolo.h5"))
detector.loadModel(detection_speed="flash")
lasthash = ih.colorhash(Image.open(execution_path+'/image2.jpg'))
custom = detector.CustomObjects(person=True)


def per_second(second_number, output_arrays, count_arrays, average_output_count, returned_frame):
    global lasthash
    f = open(os.path.join(os.getcwd(), "output", "second" + str(second_number) + ".txt"), 'w')
    #personcoord=[]
    num_of_people = len(output_arrays[0])
    for i in range(1, 5):
        num_of_people = min(num_of_people, len(output_arrays[i]))
    for i in range(num_of_people):
        line = []
        for frame in output_arrays:
            line.append(frame[i]["box_points"])
        #personcoord.append(line)
        current_mid = []
        first_mid_x = 0
        first = True
        noreturn = False
        good_line_count = 0
        for j in range(5):
            center = [round((line[j][0] + line[j][2]) / 2), round((line[j][1] + line[j][3]) / 2)]
            good_line_count += 1
            if first:
                first_mid_x = center[0]
                current_mid = center
                first = False
                #  mid.append(center)

            elif current_mid and get_distance(current_mid, center) < 100:
                current_mid = center
            else:
                noreturn = True
        # print(first_mid_x)
        # print(current_mid[0])
        if current_mid and first_mid_x and not noreturn and good_line_count >= 3:
            im = Image.fromarray(returned_frame).crop(line[0])
            hashim = ih.colorhash(im)
            diff = current_mid[0] - first_mid_x
            if abs(diff) < 50:
                print("STANDING")
            elif diff > 0:
                print("MOVING LEFT, sending")
                print(hashim)
                print(hashim - lasthash)
                lasthash = hashim
                #TODO send hashim to left camera
                #send_to_peer(l, 'Person is coming from ' + ls + ' side')
            else:
                print("MOVING RIGHT, sending")
                print(hashim)
                print(hashim - lasthash)
                lasthash = hashim
                # TODO send hashim to right camera
                #send_to_peer(r, 'Person is coming from ' + rs + ' side')

    # print("SECOND : ", second_number)
    # print("Array for the outputs of each frame ", output_arrays)
    # print("Array for output count for unique objects in each frame : ", count_arrays)
    # print("Output average count for unique objects in the last second: ", average_output_count)
    # print("------------END OF A SECOND --------------")


detector.detectObjectsFromVideo(camera_input=cam, custom_objects=custom,
                                save_detected_video=False,
                                frames_per_second=5,
                                per_second_function=per_second,
                                minimum_percentage_probability=70,
                                return_detected_frame=True
                                # , detection_timeout=10
                                )

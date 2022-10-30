import os
from imageai.Detection import VideoObjectDetection
import cv2

execution_path = os.getcwd()

cam = cv2.VideoCapture(0)

detector = VideoObjectDetection()
detector.setModelTypeAsYOLOv3()
detector.setModelPath(os.path.join(execution_path, "yolo.h5"))
detector.loadModel(detection_speed="flash")

custom = detector.CustomObjects(person=True)


def per_second(second_number, output_arrays, count_arrays, average_output_count):
    f = open(os.path.join(os.getcwd(), "output", "second" + str(second_number) + ".txt"), 'w')
    for frame in output_arrays:
        for person in frame:
            for coord in person["box_points"]:
                f.write(str(coord) + ' ')
            # f.write('%')
            break
        f.write('\n')
    f.close()

    # print("SECOND : ", second_number)
    # print("Array for the outputs of each frame ", output_arrays)
    # print("Array for output count for unique objects in each frame : ", count_arrays)
    # print("Output average count for unique objects in the last second: ", average_output_count)
    # print("------------END OF A SECOND --------------")


detector.detectObjectsFromVideo(camera_input=cam, custom_objects=custom,
                                save_detected_video=False,
                                frames_per_second=5,
                                per_second_function=per_second,
                                minimum_percentage_probability=70
                                # , detection_timeout=10
                                )

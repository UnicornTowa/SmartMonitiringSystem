import os
import numpy as np
from imageai.Detection import ObjectDetection

execution_path = os.getcwd()
detector = ObjectDetection()
detector.setModelTypeAsYOLOv3()
detector.setModelPath(os.path.join(execution_path, "yolo.h5"))
detector.loadModel()
custom_objects = detector.CustomObjects(person=True)


def person_detect(np_array):
    detections = detector.detectCustomObjectsFromImage(input_type="array", custom_objects=custom_objects,
                                                       input_image=np_array,
                                                       minimum_percentage_probability=50)
    persons = []
    for eachObject in detections:
        persons.append(eachObject["box_points"])
    return np.array(persons)

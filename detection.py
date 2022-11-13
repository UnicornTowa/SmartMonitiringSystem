import os
from imageai.Detection import VideoObjectDetection
import cv2
import PIL as pl


def CalcImageHash(FileName):
    image = cv2.imread(FileName)  # Прочитаем картинку
    resized = cv2.resize(image, (8, 8), interpolation=cv2.INTER_AREA)  # Уменьшим картинку
    gray_image = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)  # Переведем в черно-белый формат
    avg = gray_image.mean()  # Среднее значение пикселя
    ret, threshold_image = cv2.threshold(gray_image, avg, 255, 0)  # Бинаризация по порогу

    # Рассчитаем хэш
    _hash = ""
    for x in range(8):
        for y in range(8):
            val = threshold_image[x, y]
            if val == 255:
                _hash = _hash + "1"
            else:
                _hash = _hash + "0"

    return _hash


def CompareHash(hash1, hash2):
    l = len(hash1)
    i = 0
    count = 0
    while i < l:
        if hash1[i] != hash2[i]:
            count = count + 1
        i = i + 1
    return count

execution_path = os.getcwd()

cam = cv2.VideoCapture(0)

detector = VideoObjectDetection()
detector.setModelTypeAsYOLOv3()
detector.setModelPath(os.path.join(execution_path, "yolo.h5"))
detector.loadModel(detection_speed="flash")

custom = detector.CustomObjects(person=True)


def per_second(second_number, output_arrays, count_arrays, average_output_count, returned_frame):
    f = open(os.path.join(os.getcwd(), "output", "second" + str(second_number) + ".txt"), 'w')
    im = pl.Image.fromarray(returned_frame)
    print(output_arrays[0][0]["box_points"])
    im.save('img/kek'+str(second_number)+'.jpg')
    im = im.crop(output_arrays[0][0]["box_points"])
    im.save('img/lol'+str(second_number)+'.jpg')
    try:
        print(CompareHash(CalcImageHash('img/lol'+str(second_number)+'.jpg'), CalcImageHash('img/lol'+str(second_number-1)+'.jpg')))
    except:
        print("nichego")
    #print(len(returned_frame))
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


video_path = detector.detectObjectsFromVideo(camera_input=cam, custom_objects=custom,
                                save_detected_video=False,
                                frames_per_second=5,
                                per_second_function=per_second,
                                minimum_percentage_probability=70,
                                return_detected_frame=True
                                # , detection_timeout=10
                                )

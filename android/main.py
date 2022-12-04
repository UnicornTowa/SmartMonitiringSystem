import cv2
import numpy as np
import sys

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtGui import QImage

import os
from PIL import Image
import imagehash as ih
from math import sqrt

FPS = 5
out = None

if not os.path.exists('output'):
    os.mkdir('output')

def get_distance(a, b):
    #  print("distance = " + str(int(sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))))
    return int(sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))

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
                out.print("STANDING")
            elif diff > 0:
                out.print("MOVING LEFT, sending")
                out.print(hashim)
                out.print(hashim - lasthash)
                lasthash = hashim
                #TODO send hashim to left camera
                #send_to_peer(l, 'Person is coming from ' + ls + ' side')
            else:
                out.print("MOVING RIGHT, sending")
                out.print(hashim)
                out.print(hashim - lasthash)
                lasthash = hashim
                # TODO send hashim to right camera
                #send_to_peer(r, 'Person is coming from ' + rs + ' side')


class RecordVideo(QtCore.QObject):
    image_data = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, camera_port, parent=None):
        super().__init__(parent)
        self.camera = cv2.VideoCapture(camera_port)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timerEvent)
        self.timer.start(int(1000 / FPS))

    def timerEvent(self):
        read, data = self.camera.read()
        if read:
            self.image_data.emit(data)


class FaceDetectionWidget(QtWidgets.QWidget):
    def __init__(self, cascade_filepath, parent=None):
        super().__init__(parent)
        self.classifier = cv2.CascadeClassifier(cascade_filepath)
        self.image = QImage()
        self._border = (0, 255, 0)
        self._width = 2
        
        self.frame_num = 0
        self.bounds = [[]]

    def detect_faces(self, image):
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_image = cv2.equalizeHist(gray_image)
        faces = self.classifier.detectMultiScale(gray_image, 1.3, 5)
        return faces

    def image_data_slot(self, image_data):
        if (self.width() > self.height()) != (image_data.shape[1] > image_data.shape[0]):
            # Need to rotate image data, the screen / camera is rotated
            image_data = cv2.rotate(image_data, cv2.ROTATE_90_COUNTERCLOCKWISE)
        faces = self.detect_faces(image_data)
        for (x, y, w, h) in faces:
            cv2.rectangle(image_data, (x, y), (x + w, y + h), self._border, self._width)
        self.image = self.get_qimage(image_data)
        self.update()
        
        self.frame_num += 1
        #out.print(str(self.frame_num))
        frame = []
        for (x, y, w, h) in faces:
            frame.append({"box_points":[x, y, x+w, y+h]})
        self.bounds.append(frame)
        if self.frame_num % FPS == 0:
            per_second(int(self.frame_num / FPS), self.bounds, 0, 0, image_data)
            self.bounds = [self.bounds[FPS]]
        
    def get_qimage(self, image):
        height, width, colors = image.shape
        image = QImage(image.data, width, height, 3 * width, QImage.Format_RGB888).rgbSwapped()
        return image

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        w = self.width()
        h = self.height()
        cw = self.image.width()
        ch = self.image.height()

        # Keep aspect ratio
        if ch != 0 and cw != 0:
            w = min(cw * h / ch, w)
            h = min(ch * w / cw, h)
            w, h = int(w), int(h)

        painter.drawImage(QtCore.QRect(0, 0, w, h), self.image)
        self.image = QImage()


class OutputWidget(QtWidgets.QLabel):
    def init(self,parent=None):
        super().init(parent)
  
    def print(self, text):
        self.setText(self.text() + str(text) + '\n')


class MainWidget(QtWidgets.QWidget):
    def __init__(self, haarcascade_filepath, parent=None):
        super().__init__(parent)
        fp = haarcascade_filepath
        self.face_detection_widget = FaceDetectionWidget(fp,self)
        # 1 is used for frontal camera
        self.record_video = RecordVideo(1)
        self.record_video.image_data.connect(self.face_detection_widget.image_data_slot)
        
        self.output_widget = OutputWidget(self)
        global out
        out = self.output_widget
        
        #layout = QtWidgets.QVBoxLayout()
        #layout.addWidget(self.face_detection_widget)
        #layout.addWidget(self.output_widget)
        #self.setLayout(layout)
        
    def resizeEvent(self, event):
    	sz = event.size()
    	hh = int(sz.height() / 2)
    	
    	self.face_detection_widget.move(0,0)
    	self.face_detection_widget.resize(sz.width(), hh)
    	
    	self.output_widget.move(0, hh)
    	self.output_widget.resize(sz.width(), hh)
    	


app = QtWidgets.QApplication(sys.argv)
haar_cascade_filepath = cv2.data.haarcascades + '/haarcascade_frontalface_default.xml'
main_window = QtWidgets.QMainWindow()
main_widget = MainWidget(haar_cascade_filepath)
main_window.setCentralWidget(main_widget)
main_window.show()
sys.exit(app.exec_())

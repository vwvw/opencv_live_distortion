#!/usr/bin/env python3

import cv2
import sys
import numpy as np

from PyQt5.QtCore import QDateTime, Qt, QTimer, QSize
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QDialog,
    QLabel,
    QSlider,
    QVBoxLayout,
    QPushButton,
    QWidget,
)
from PyQt5.QtGui import QIcon, QPixmap, QImage


class MySlider:
    def __init__(self, parent_widget, name, initial_value, decimal_point):
        """
        Create a Slider in PyQT and provide access to its values and the surrounding UI
        :param parent_widget: the widget containing the callback function that will be
                              called when the value is updated
        :param name: the label that will be placed next to the slider
        :param initial_value: the default value of the slider
        :param decimal_point: the number of decimal point that the slider should be able
                              to handle
        """
        self.name = name
        self.initial_value = initial_value
        self.decimal_point = decimal_point
        self.parent_widget = parent_widget
        slider_initial_value = self.compute_slider_value(self.initial_value)

        self.slider = QSlider(Qt.Horizontal)
        span = max(0.5 * slider_initial_value, pow(10, decimal_point - 1))
        self.slider.setMinimum(slider_initial_value - span)
        self.slider.setMaximum(slider_initial_value + span)
        self.slider.setValue(slider_initial_value)
        self.slider.setSingleStep(0.0001)
        self.slider.valueChanged.connect(self.slider_changed)

        box = QGroupBox()
        vbox = QVBoxLayout()
        box.setLayout(vbox)
        gbox = QGroupBox()
        hbox = QHBoxLayout()
        gbox.setLayout(hbox)

        self.label = QLabel(self.get_label())
        button = QPushButton("Reset")
        button.clicked.connect(self.button_reset_pressed)

        hbox.addWidget(self.label, 0)
        hbox.addWidget(button, 1)

        vbox.addWidget(gbox, 0)
        vbox.addWidget(self.slider, 1)

        self.widget = box

    def compute_slider_value(self, value):
        """
        As the slider do not support float, we multiply the number to get an equivalent
        precision to the number of decimal point needed.
        This function transform a real-world value to the magnitude used in the slider
        reference.
        :param value: the value to transform in the scale of the slider
        :return: the value in the scale used by the slider
        """
        return value * pow(10, self.decimal_point)

    def get_value(self):
        """
        Get the real world value not in the scale of the slider.
        :return: the real world value
        """
        return self.slider.value() / pow(10, self.decimal_point)

    def get_label(self):
        """
        Getter for the text representation of the slider.
        :return: the name and the slider value as a string
        """
        return self.name + ": " + str(self.get_value())

    def button_reset_pressed(self):
        """
        Callback function to reset the value of the slider to it's initial value.
        """
        self.slider.setValue(self.compute_slider_value(self.initial_value))
        self.parent_widget.undistort()

    def slider_changed(self):
        """
        Callback function used when the slider value changes. It will first updated the
        text of the UI label and then call the undistortion function of the image as the
        parameters were modified.
        """
        self.label.setText(self.get_label())
        self.parent_widget.undistort()


class WidgetGallery(QDialog):
    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)

        self.sliders = []
        self.pic = None
        self.res_img_shape = QSize(1690, 670)

        self.mainLayout = QGridLayout()
        self.setLayout(self.mainLayout)

        self.sliders.append(MySlider(self, "fx", 598.6028602, 2))
        self.sliders.append(MySlider(self, "fy", 597.89808123, 2))
        self.sliders.append(MySlider(self, "cx", 648.84050704, 2))
        self.sliders.append(MySlider(self, "cy", 342.10643555, 2))
        self.sliders.append(MySlider(self, "k1", 0.62685222, 6))
        self.sliders.append(MySlider(self, "k2", 0.07302406, 6))
        self.sliders.append(MySlider(self, "p1", 0.0, 6))
        self.sliders.append(MySlider(self, "p2", 0.0, 6))
        self.sliders.append(MySlider(self, "k3", 0.00275536, 6))
        self.sliders.append(MySlider(self, "k4", 0.98399674, 6))
        self.sliders.append(MySlider(self, "k5", 0.20003344, 6))
        self.sliders.append(MySlider(self, "k6", 0.01347275, 6))
        self.sliders.append(MySlider(self, "s1", 0.0, 6))
        self.sliders.append(MySlider(self, "s2", 0.0, 6))
        self.sliders.append(MySlider(self, "s3", 0.0, 6))
        self.sliders.append(MySlider(self, "s4", 0.0, 6))
        self.sliders.append(MySlider(self, "tx", 0.0, 6))
        self.sliders.append(MySlider(self, "ty", 0.0, 6))

        self.pic = QLabel(self)
        pixmap = QPixmap("image.jpeg")
        self.pic.setPixmap(pixmap)
        self.resize(self.res_img_shape)

        for i, sl in enumerate(self.sliders):
            self.mainLayout.addWidget(sl.widget, i // 6, i % 6)
        self.mainLayout.addWidget(self.pic, 3, 0, 1, len(self.sliders))

        self.img_shape = (1280, 720)
        self.img = cv2.imread("image.png")

        self.undistort()

    def create_camera_matrix(self):
        """
        Retrieve the data from the sliders and put them in the correct matrix format for
        the distortion correction to take place.
        :return: a tuple of matrices. First the 3x3 camera matrix and the 14x1
                 distortion coefficient matrix. Both matrices are in the same order as
                 expected by OpenCV
        """
        mat_intrinsic = np.eye(3)
        mat_intrinsic[0][0] = self.sliders[0].get_value()
        mat_intrinsic[1][1] = self.sliders[1].get_value()
        mat_intrinsic[0][2] = self.sliders[2].get_value()
        mat_intrinsic[1][2] = self.sliders[3].get_value()

        mat_dist = np.zeros((14, 1), np.float32)
        for i in range(len(mat_dist)):
            mat_dist[i][0] = self.sliders[i + 4].get_value()
        return mat_intrinsic, mat_dist

    def undistort(self):
        """
        Retrieve the chosen camera and distortion settings and then undistort the image
        before displaying in the main UI.
        """
        camera_mat, dist_mat = self.create_camera_matrix()
        new_m, roi = cv2.getOptimalNewCameraMatrix(
            camera_mat, dist_mat, self.img_shape, 1, (1690, 670)
        )
        r_mat = np.eye(3)
        map1, map2 = cv2.initUndistortRectifyMap(
            camera_mat,
            dist_mat,
            r_mat,
            new_m,
            (1690, 670),
            cv2.CV_16SC2,
        )
        dst = cv2.remap(self.img, map1, map2, cv2.INTER_LINEAR, cv2.BORDER_CONSTANT)
        cv2.rectangle(
            dst, (roi[0], roi[1]), (roi[0] + roi[2], roi[1] + roi[3]), 255, 1, 8, 0
        )
        bytes_per_line = 3 * self.res_img_shape.width()
        q_img = QImage(
            dst.data,
            self.res_img_shape.width(),
            self.res_img_shape.height(),
            bytes_per_line,
            QImage.Format_RGB888,
        ).rgbSwapped()
        self.pic.setPixmap(QPixmap(q_img))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gallery = WidgetGallery()
    gallery.show()
    sys.exit(app.exec_())

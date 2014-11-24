# fisheye_view.py
# Viewer for fisheye imagery and visualizing sample angles.
#
#  Copyright 2014-2015 Program of Computer Graphics, Cornell University
#     580 Rhodes Hall
#     Cornell University
#     Ithaca NY 14853
#  Web: http://www.graphics.cornell.edu/
#
#  Not for commercial use. Do not redistribute without permission.
#

import sys, os
import PySide
from PySide import QtCore, QtGui
sys.modules['PyQt4'] = PySide
from datetime import time, timedelta, datetime

import angle_utilities

class FisheyeViewer(QtGui.QLabel):
    def __init__(self, fisheyeFile=None, parent=None):
        super(FisheyeViewer, self).__init__(parent)
        self.fisheyeFile = fisheyeFile
        self.setAlignment(QtCore.Qt.AlignCenter)

        # Set up the label container for the fisheye image
        if self.fisheyeFile:
            self.loadFisheyeFile(self.fisheyeFile)

    def drawAnglePosition(self, theta, phi, inRadians=True):
        """ Draw a marker on the fisheye image at the current sample. """
        if not self.fisheyeFile:
            return

        pixmap = self.pixmap()

        # Determine the pixel location of the angles. 
        theta, phi = angle_utilities.FisheyeAngleWarp(theta, phi, inRadians=inRadians)
        angleU, angleV = angle_utilities.GetUVFromAngle(theta, phi, inRadians=inRadians)
        angleU = angleU * pixmap.width()
        angleV = angleV * pixmap.height()

        # Paint at the angle position on the fisheye pixmap.
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QColor(255, 0, 0, 255))
        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0, 255))
        painter.setBrush(brush)
        painter.drawEllipse(angleU, angleV, 5, 5)

        # Update the fisheyeContainer with the new pixmap
        self.setPixmap(pixmap)

    def loadFisheyeFile(self, fisheyeFile):
        """ Load the specified fisheye file into widget. """
        self.fisheyeFile = fisheyeFile
        pixmap = QtGui.QPixmap(fisheyeFile)
        pixmap = pixmap.scaled(300, 300, QtCore.Qt.KeepAspectRatio)
        self.setPixmap(pixmap)
        #self.setFixedSize(pixmap.size())

    def reset(self):
        """ Resets the view to be the clean fisheye image without any angles
              drawn on the image.
        """
        self.loadFisheyeFile(self.fisheyeFile)

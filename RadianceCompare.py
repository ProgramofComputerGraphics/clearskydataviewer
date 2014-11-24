# RadianceCompare.py
# Provides functionality for comparing radiance spectra samples. See Usage.txt
#   for information on using the tool.
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

import re
import numpy
import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4']='PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
rcParams.update({'text.usetex': True})
rcParams.update({'font.size': 12})

import fisheye_view

class RadianceSampleItem(QtGui.QTreeWidgetItem):
    def __init__(self, radianceData, parent=None):
        super(RadianceSampleItem, self).__init__(parent)
        self.radianceData = radianceData

    def __lt__(self, otherItem):
        """ Define a custom comparison to order float text. """
        column = self.treeWidget().sortColumn()
        try:
            return float(self.text(column)) > float(otherItem.text(column))
        except ValueError:
            return self.text(column) > otherItem.text(column)

class RadianceSampleViewer(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(RadianceSampleViewer, self).__init__(parent)
        self.setWindowTitle("Radiance Sample Viewer")
        self.setAcceptDrops(True)

        # Build the main plot canvas
        self.plot = Figure(facecolor=(0.933, 0.933, 0.933), edgecolor=(0, 0, 0))
        self.plotCanvas = FigureCanvas(self.plot)
        self.setCentralWidget(self.plotCanvas)

        # Build the sample tree view
        self.sampleTreeDock = QtGui.QDockWidget("Open Samples", self)
        self.sampleTreeDock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.sampleTree = QtGui.QTreeWidget()
        self.sampleTree.setSortingEnabled(True)
        self.sampleTree.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.sampleTree.itemSelectionChanged.connect(self.SOCKET_handleSampleSelection)
        self.sampleTree.itemChanged.connect(self.SOCKET_handleSampleCheck)
        self.sampleTree.setHeaderLabels(["Date", "Time", "Azimuth", "Elevation"])

        self.sampleTreeDock.setWidget(self.sampleTree)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.sampleTreeDock)

        # Build the fisheye view dock
        self.fisheyeDock = QtGui.QDockWidget("Fisheye Viewer", self)
        self.fisheyeDock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.fisheyeView = fisheye_view.FisheyeViewer()
        self.fisheyeDock.setWidget(self.fisheyeView)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.fisheyeDock)

        # Setup the file menu bar
        self.menubar = self.menuBar()
        fileMenu = self.menubar.addMenu("&File")
        loadRadianceAction = QtGui.QAction("&Load Radiance File", self)
        loadRadianceAction.triggered.connect(self.SOCKET_loadRadianceData)
        fileMenu.addAction(loadRadianceAction)
        loadFisheyeAction = QtGui.QAction("Load Fisheye Image", self)
        loadFisheyeAction.triggered.connect(self.SOCKET_loadFisheyeImage)
        fileMenu.addAction(loadFisheyeAction)
        clearDataAction = QtGui.QAction("&Clear Radiance Data", self)
        clearDataAction.triggered.connect(self.sampleTree.clear)
        fileMenu.addAction(clearDataAction)

    def SOCKET_handleSampleSelection(self):
        """ Redraw the graph when the user selection changes. """
        self.plotRadianceData()

    def SOCKET_handleSampleCheck(self, item, column):
        """ Add or remove a sample plot from the radiance plotter bsed on if it 
              is checked or not. 
        """
        self.plotRadianceData()

    def dragEnterEvent(self, event):
        """ Accept drag events concerning files. """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def addSampleItem(self, sampleData, sampleFile):
        """ Add a radiance sample to the tree widget and the radiance plot. """
        # Add the file to the tree list
        treeWidgetItem = RadianceSampleItem(sampleData, self.sampleTree)
        treeWidgetItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
        treeWidgetItem.setCheckState(0, QtCore.Qt.Unchecked)

        fileInfo = self.parseRadianceFileName(sampleFile)

        # Add columns for each of the data fields
        treeWidgetItem.setText(0, fileInfo[0])  # Date
        treeWidgetItem.setText(1, fileInfo[1])  # Time
        treeWidgetItem.setText(2, fileInfo[4])  # Azimuth
        treeWidgetItem.setText(3, fileInfo[5])  # Elevation
            
        self.sampleTree.addTopLevelItem(treeWidgetItem)

    def dropEvent(self, event):
        """ Handle the file drop event and load the radiance file dropped on the
              window.
        """
        files = event.mimeData().urls()
        self.sampleTree.blockSignals(True)
        for radianceFile in files:
            # Add the sample data to the file list
            radianceSample = self.loadRadianceDataFile(radianceFile.toLocalFile())
            self.addSampleItem(radianceSample, radianceFile.toLocalFile())
        
        self.sampleTree.blockSignals(False)
        self.plotRadianceData()

    def parseRadianceFileName(self, filename):
        """ Parses out the date, time, and angle information from a radiance
              file.
        """
        fileComponents = os.path.split(filename)
        fullFile = fileComponents[1]
        if fullFile and fullFile.endswith(".asd.rad.txt"):
            noExt = fullFile[:-12]
            noExt = re.sub("_+", "_", noExt)
            fileInfo = noExt.split('_')
            return fileInfo

    def plotRadianceData(self):
        """ Plot the current radiance data loaded into memory. """
        self.plot.clear()
        ax = self.plot.add_subplot(111)
        ax.axis([350, 800, 0.0, 0.3])
        ax.set_ylabel("Radiance ($W/m^2$)")
        ax.set_xlabel("Wavelength ($nm$)")

        selectedSample = None
        selectedIndex = None
        for i in range(self.sampleTree.topLevelItemCount()):
            sampleItem = self.sampleTree.topLevelItem(i)
            sample = sampleItem.radianceData
            if sampleItem.isSelected():
                selectedSample = [sample.keys(), sample.values()]
                selectedIndex = i

                # Update the fisheye view with the correct angle pair
                azimuth = float(sampleItem.text(2))
                elevation = float(sampleItem.text(3))
                self.fisheyeView.reset()
                self.fisheyeView.drawAnglePosition(azimuth, elevation, inRadians=False)

            if sampleItem.checkState(0) == QtCore.Qt.Checked:
                ax.plot(sample.keys(), sample.values(), color="#000000")

        # Redraw the selected sample in a thicker line
        if selectedSample:
            ax.plot(selectedSample[0], selectedSample[1], color="#4499FF", linewidth=3)
            self.plot.text(0.05, 0.95, "%d" % selectedIndex)

        self.plotCanvas.draw()

        if selectedSample:
            saveFilename = "C:/Users/dtk47/Desktop/THESIS/plot%05d.png" % selectedIndex
            self.plot.savefig(saveFilename)

    def SOCKET_loadRadianceData(self):
        """ Allow the user to open a new radiance file and display the file in 
              the radiance plot.
        """
        radianceFiles = QtGui.QFileDialog.getOpenFileNames(self, "Radiance File")[0]
        self.sampleTree.blockSignals(True)
        for radianceFile in radianceFiles:
            radianceSample = self.loadRadianceDataFile(radianceFile)
            self.addSampleItem(radianceSample, radianceFile)
        self.sampleTree.blockSignals(False)
        self.plotRadianceData()

    def SOCKET_loadFisheyeImage(self):
        """ Allow the user to load a fisheye image to display in conjunction 
              with the radiance samples to display the angle associated with
              the selected sample. 
        """
        fisheyeFile = QtGui.QFileDialog.getOpenFileName(self, "Fisheye File")
        fisheyeFilename = fisheyeFile[0]
        self.fisheyeView.loadFisheyeFile(fisheyeFilename)

    def loadRadianceDataFile(self, filename):
        """ Read in a radiance file in txt format, and return a dictionary of
              wavelength to radiance. 
        """
        radianceFile = open(filename, 'r')
        radianceDict = {}

        for line in radianceFile:
            fileCols = line.split('\t')
            try:
               # Try to parse the first piece as in int wavelength
               wavelength = int(fileCols[0])
               radiance = float(fileCols[1])
               radianceDict[wavelength] = radiance
            except ValueError:
                # Catch the error on the first line, and continue
                print line
                continue  

        radianceFile.close()
        return radianceDict

    def quit(self):
        self.close()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    viewer = RadianceSampleViewer()
    viewer.resize(1280, 920)
    viewer.show()

    sys.exit(app.exec_())

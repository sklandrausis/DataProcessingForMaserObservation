#! /usr/bin/python3
import sys
import os
import argparse
import configparser
import numpy as np
from astropy.convolution import Gaussian1DKernel, convolve
from astropy.modeling import fitting
from astropy.modeling.polynomial import Chebyshev1D
from scipy.interpolate import UnivariateSpline
import peakutils
import json
from PyQt5.QtWidgets import (QWidget, QGridLayout, QApplication, QDesktopWidget, QPushButton, QMessageBox, QLabel, QLineEdit, QSlider)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QFont
import re

from ploting_qt5 import  Plot

def parseArguments():
    # Create argument parser
    parser = argparse.ArgumentParser(description='''plotting tool. ''', epilog="""PRE PLOTTER.""")
    
    # Positional mandatory arguments
    parser.add_argument("datafile", help="Experiment correlation file name", type=str)

    # Optional arguments
    parser.add_argument("-c", "--config", help="Configuration Yaml file", type=str, default="config/config.cfg")

    # Print version
    parser.add_argument("-v","--version", action="version", version='%(prog)s - Version 1.0')

    # Parse arguments
    args = parser.parse_args()
    return args

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def indexies(array, value):
    indexs = list()
    for i in range(0, len(array)-1):
        if array[i] == value:
            indexs.append(i)
    return indexs

def FWHM(x, y, constant):
    spline = UnivariateSpline(x, y-np.max(y)/2, k=3, s=20)
    spline.set_smoothing_factor(0.5)
    root1 = spline.roots()[0] - constant
    root2 = spline.roots()[-1] + constant
    index_1 =  (np.abs(x-root1)).argmin()
    index_2 =  (np.abs(x-root2)).argmin()
    return (index_1, index_2)

class Analyzer(QWidget):
    def __init__(self, datafile, resultFilePath):
        super().__init__()
       
        self.setWindowIcon(QIcon('viraclogo.png'))
        #self.center()
        
        self.FWHMconstant = 1
        self.polynomialOrder = 3
        self.source = re.split("([A-Z, a-z]+)", datafile.split("/")[-1].split(".")[0])[1]
        self.expername = datafile.split("/")[-1].split(".")[0]
        self.date = re.split("([A-Z, a-z]+)", datafile.split("/")[-1].split(".")[0])[2][0:-1]
        self.location = datafile.split("/")[-1].split(".")[0].split("_")[-1]
        self.resultFilePath = resultFilePath
        
        self.infoSet = set()
        self.infoSet_2 = list()
        
        try:
            data = np.fromfile(datafile, dtype="float64", count=-1, sep=" ") .reshape((file_len(datafile),3))
        
        except IOError as e:
            print ("IO Error",  e)
            sys.exit(1)
                
        except:
            print("Unexpected error:", sys.exc_info()[0])
            sys.exit(1)
                 
        else:
            self.dataPoints = data.shape[0]
            self.m = 0
            self.n = self.dataPoints
            
            self.xdata = data[:, [0]]
            self.y_u1 = data[:, [1]] 
            self.y_u9 = data[:, [2]]
            
            #Making sure that data is numpy array
            self.xarray = np.zeros(self.dataPoints)
            self.y1array = np.zeros(self.dataPoints)
            self.y2array = np.zeros(self.dataPoints)
            
            for i in range (0, self.dataPoints):
                self.xarray[i] = self.xdata[i]
                self.y1array[i] = self.y_u1[i]
                self.y2array[i] = self.y_u9[i]
                
            self.xarray =  np.flip(self.xarray,0)
            self.y1array =  np.flip(self.y1array,0)
            self.y2array =  np.flip(self.y2array,0)
            
            self.grid = QGridLayout()
            self.setLayout(self.grid)
            self.grid.setSpacing(10)
            
            self.plotInitData()
    
    def onpickU1(self, event):
        thisline = event.artist
        xdata = thisline.get_xdata()
        ydata = thisline.get_ydata()
        ind = event.ind
        p = tuple(zip(xdata[ind], ydata[ind]))
        self.plot_3.plot(p[0][0], p[0][1], 'ro',  markersize=1,  picker=5)
        self.points_1u.append(p[0])
        #self.points_9u.append(p[0])
        self.plot_3.canvasShow()
        
    def onpickU9(self, event):
        thisline = event.artist
        xdata = thisline.get_xdata()
        ydata = thisline.get_ydata()
        ind = event.ind
        p = tuple(zip(xdata[ind], ydata[ind]))
        self.plot_4.plot(p[0][0], p[0][1], 'ro', markersize=1, picker=5)
        self.points_9u.append(p[0])
        #self.points_1u.append(p[0])
        self.plot_4.canvasShow()
        
    def onpick_maxU1(self, event):
        thisline = event.artist
        xdata = thisline.get_xdata()
        ydata = thisline.get_ydata()
        ind = event.ind
        self.maxu1_index.append(ind[0])
        p = tuple(zip(xdata[ind], ydata[ind]))
        self.plot_7.plot(p[0][0], p[0][1], 'gd', markersize=2, picker=5)
        if  self.maxU1.count(p[0]) == 0:
            self.maxU1.append(p[0])
        self.plot_7.canvasShow()
        
    def onpick_maxU9(self, event):
        thisline = event.artist
        xdata = thisline.get_xdata()
        ydata = thisline.get_ydata()
        ind = event.ind
        self.maxu9_index.append(ind[0])
        p = tuple(zip(xdata[ind], ydata[ind]))
        self.plot_8.plot(p[0][0], p[0][1], 'gd', markersize=2, picker=5)
        if  self.maxU9.count(p[0]) == 0:
            self.maxU9.append(p[0])
        self.plot_8.canvasShow()
        
    def onpick_maxAVG(self, event):
        thisline = event.artist
        xdata = thisline.get_xdata()
        ydata = thisline.get_ydata()
        ind = event.ind
        self.maxavg_index.append(ind[0])
        p = tuple(zip(xdata[ind], ydata[ind]))
        self.plot_9.plot(p[0][0], p[0][1], 'gd', markersize=2, picker=5)
        if  self.avgMax.count(p[0]) == 0:
            self.avgMax.append(p[0])
        self.plot_9.canvasShow()
            
    def plotInitData(self):
        self.setWindowTitle("Info")
        
        self.changeDataButton = QPushButton("Change Data", self)
        self.changeDataButton.clicked.connect(self.changeData)
        self.changeDataButton.setStyleSheet("background-color: blue")
        self.grid.addWidget(self.changeDataButton, 4, 3)
        
        self.plotSmoothDataButton = QPushButton("Smooth Data", self)
        self.plotSmoothDataButton.clicked.connect(self.plotSmoothData)
        self.plotSmoothDataButton.setStyleSheet("background-color: green")
        self.grid.addWidget(self.plotSmoothDataButton, 4, 4)
         
        self.plot_1 = Plot()
        self.plot_1.creatPlot(self.grid, 'Frequency Mhz', 'Flux density (Jy)', "u1 Polarization", (1, 0))
        self.plot_1.plot(self.xarray, self.y1array, 'ko', label='Data Points', markersize=1)
            
        self.plot_2 = Plot()
        self.plot_2.creatPlot(self.grid, 'Frequency Mhz', 'Flux density (Jy)', "u9 Polarization", (1, 1))
        self.plot_2.plot(self.xarray, self.y2array, 'ko', label='Data Points', markersize=1)
            
        self.grid.addWidget(self.plot_1, 0, 0)
        self.grid.addWidget(self.plot_2, 0, 1)
        
        infoPanelLabelsText = ["FWHM constant", "Polynomial order"]
        infoPanelEntryText = [ {"defaultValue":str(self.FWHMconstant), "addEntry":True}, {"defaultValue":str(self.polynomialOrder), "addEntry":True}]
        
        for i in range(0, len(infoPanelLabelsText)):
            
            self.infoLabel = QLabel(infoPanelLabelsText[i])
            self.grid.addWidget(self.infoLabel, i +  1, 3)
            self.infoSet.add(self.infoLabel)
            
            if  infoPanelEntryText[i]["addEntry"]:
                self.infoInputField = QLineEdit()
                self.infoInputField.setText(str(infoPanelEntryText[i]["defaultValue"]))
                self.grid.addWidget(self.infoInputField, i + 1, 4)
                self.infoSet_2.append(self.infoInputField)
            
    def changeData (self):
        newValues = list()
        
        for value in self.infoSet_2:
            newValues.append(value.text())
            
        self.FWHMconstant = int(newValues[0])
        self.polynomialOrder = int(newValues[1])
        
        QMessageBox.information(self, "Info", "Data was changed")
            
    def plotSmoothData(self):
        self.setWindowTitle("Smooth Data")
        
        while len(self.infoSet) != 0:
            info_item = self.infoSet.pop()
            info_item.hide()
            info_item.close()
            self.grid.removeWidget(info_item)
            del info_item 
            
        while len(self.infoSet_2) != 0:   
            info_item = self.infoSet_2.pop()
            info_item.hide()
            info_item.close()
            self.grid.removeWidget(info_item)
            del info_item 
            
        del self.infoSet
        del self.infoSet_2
        
        self.changeDataButton.hide()
        self.plotSmoothDataButton.hide()
        self.changeDataButton.close()
        self.plotSmoothDataButton.close()
        self.grid.removeWidget(self.plotSmoothDataButton)
        self.grid.removeWidget(self.changeDataButton)
        del self.plotSmoothDataButton
        del self.changeDataButton
        
        self.plot_1.hide()
        self.plot_2.hide()
        self.plot_1.close()
        self.plot_2.close()
        self.grid.removeWidget(self.plot_1)
        self.grid.removeWidget(self.plot_2)
        self.plot_1.removePolt()
        self.plot_2.removePolt()
        del self.plot_1
        del self.plot_2
        
        g1 = Gaussian1DKernel(stddev=3, x_size=19, mode='center', factor=100)
        g2 = Gaussian1DKernel(stddev=3, x_size=19, mode='center', factor=100)
    
        self.z1 = convolve(self.y1array, g1, boundary='extend')
        self.z2 = convolve(self.y2array, g2, boundary='extend')
        
        self.points_1u = list()
        self.points_9u = list()
        
        self.plot_3 = Plot()
        self.plot_3.creatPlot(self.grid, 'Frequency Mhz', 'Flux density (Jy)', "1u Polarization", (1, 0))
        self.plot_3.plot(self.xarray, self.z1, 'ko', label='Data Points', markersize=1, picker=5)
        self.plot_3.addPickEvent(self.onpickU1)
        self.plot_3.addSecondAxis("x", "Data points", 0, self.dataPoints + 512, 1024)
        
        self.plot_4 = Plot()
        self.plot_4.creatPlot(self.grid, 'Frequency Mhz', 'Flux density (Jy)', "9u Polarization", (1, 1))
        self.plot_4.plot(self.xarray, self.z2, 'ko', label='Data Points', markersize=1, picker=5)
        self.plot_4.addPickEvent(self.onpickU9)
        self.plot_4.addSecondAxis("x", "Data points", 0, self.dataPoints + 512, 1024)
        
        self.grid.addWidget(self.plot_3, 0, 0)
        self.grid.addWidget(self.plot_4, 0, 1)
        
        self.a, self.b = FWHM(self.xarray, (self.z1 + self.z2)/2, self.FWHMconstant)
        
        #sliders
        self.previousM = self.m
        self.previousN = self.n -1
        
        self.m_slider = QSlider(Qt.Horizontal, self)
        self.n_slider = QSlider(Qt.Horizontal, self)
        self.m_slider.setFocusPolicy(Qt.NoFocus)
        self.n_slider.setFocusPolicy(Qt.NoFocus)
        self.m_slider.setMinimum(10)
        self.m_slider.setMaximum(20)
        self.n_slider.setMinimum(20)
        self.n_slider.setMaximum(10)
        self.n_slider.setValue(19)
        self.m_slider.setMinimumSize(200, 0)
        self.m_slider.setMinimumSize(200, 0)
        self.m_slider.valueChanged[int].connect(self.changeValue)
        self.n_slider.valueChanged[int].connect(self.changeValue_2)
        
        self.grid.addWidget(self.m_slider, 3,3)
        self.grid.addWidget(self.n_slider, 4,3)
        
    def changeValue(self, value):
        print (value)
        pass 
    
    def changeValue_2(self, value):
        print (value)
        pass
              
def main():
    args = parseArguments()
   
    datafile = str(args.__dict__["datafile"])
    configFilePath = str(args.__dict__["config"])
    
    config = configparser.RawConfigParser()
    config.read(configFilePath)
    dataFilesPath =  config.get('paths', "dataFilePath")
    resultFilePath =  config.get('paths', "resultFilePath")
    
    #Create App
    qApp = QApplication(sys.argv)

    aw = Analyzer(dataFilesPath + datafile, resultFilePath)
    aw.show()
    sys.exit(qApp.exec_())
    
    sys.exit(0)
                
if __name__=="__main__":
    main()

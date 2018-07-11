#! /usr/bin/python3

import sys
import os
import argparse
import configparser
import numpy as np
from astropy.convolution import Gaussian1DKernel, convolve
from scipy.interpolate import UnivariateSpline
import peakutils
import json
from PyQt5.QtWidgets import (QWidget, QGridLayout, QApplication, QPushButton, QMessageBox, QLabel, QLineEdit, QSlider, QDesktopWidget, QLCDNumber)
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from PyQt5.QtGui import QColor
import re

from ploting_qt5 import  Plot

def parseArguments():
    # Create argument parser
    parser = argparse.ArgumentParser(description='''plotting tool. ''', epilog="""PRE PLOTTER.""")
    
    # Positional mandatory arguments
    parser.add_argument("datafile", help="Experiment correlation file name", type=str)

    # Optional arguments
    parser.add_argument("-c", "--config", help="Configuration cfg file", type=str, default="config/config.cfg")

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
    def __init__(self, datafile, resultFilePath, source_velocities, cuts):
        super().__init__()
       
        self.setWindowIcon(QIcon('viraclogo.png'))
        self.center()
        
        self.FWHMconstant = 1
        self.polynomialOrder = 3
        self.source = re.split("([A-Z, a-z]+)", datafile.split("/")[-1].split(".")[0])[1]
        self.expername = datafile.split("/")[-1].split(".")[0]
        self.location = datafile.split("/")[-1].split(".")[0].split("_")[-2]
        self.date = "_".join([datafile.split("/")[-1].split(".")[0].split("_")[1], datafile.split("/")[-1].split(".")[0].split("_")[2], datafile.split("/")[-1].split(".")[0].split("_")[3]])
        self.iteration_number = datafile.split("/")[-1].split(".")[0].split("_")[-1]
        self.resultFilePath = resultFilePath
        self.source_velocities = source_velocities
        self.cuts = cuts
        
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
            
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
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
        self.grid.addWidget(self.changeDataButton, 5, 3)
        
        self.plotSmoothDataButton = QPushButton("Create Shorter specter", self)
        self.plotSmoothDataButton.clicked.connect(self.plotShortSpectr)
        self.plotSmoothDataButton.setStyleSheet("background-color: green")
        self.grid.addWidget(self.plotSmoothDataButton, 5, 4)
         
        self.plot_1 = Plot()
        self.plot_1.creatPlot(self.grid, 'Velocity (km sec$^{-1}$)', 'Flux density (Jy)', "u1 Polarization", (1, 0))
        self.plot_1.plot(self.xarray, self.y1array, 'ko', label='Data Points', markersize=1)
            
        self.plot_2 = Plot()
        self.plot_2.creatPlot(self.grid, 'Velocity (km sec$^{-1}$)', 'Flux density (Jy)', "u9 Polarization", (1, 1))
        self.plot_2.plot(self.xarray, self.y2array, 'ko', label='Data Points', markersize=1)
            
        self.grid.addWidget(self.plot_1, 0, 0)
        self.grid.addWidget(self.plot_2, 0, 1)
        
        infoPanelLabelsText = ["FWHM constant", "Polynomial order"]
        infoPanelEntryText = [ {"defaultValue":str(self.FWHMconstant), "addEntry":True}, {"defaultValue":str(self.polynomialOrder), "addEntry":True}]
        
        for i in range(0, len(infoPanelLabelsText)):
            
            self.infoLabel = QLabel(infoPanelLabelsText[i])
            self.grid.addWidget(self.infoLabel, i +  3, 3)
            self.infoSet.add(self.infoLabel)
            
            if  infoPanelEntryText[i]["addEntry"]:
                self.infoInputField = QLineEdit()
                self.infoInputField.setText(str(infoPanelEntryText[i]["defaultValue"]))
                self.grid.addWidget(self.infoInputField, i + 3, 4)
                self.infoSet_2.append(self.infoInputField)
        
        self.a, self.b = FWHM(self.xarray, (self.y2array + self.y1array)/2, self.FWHMconstant)
               
        #sliders
        self.previousM = self.m
        self.previousN = self.n -1
        
        self.m_slider = QSlider(Qt.Horizontal, self)
        self.n_slider = QSlider(Qt.Horizontal, self)
        self.m_slider.setFocusPolicy(Qt.NoFocus)
        self.n_slider.setFocusPolicy(Qt.NoFocus)
        self.m_slider.setTickInterval(20)
        self.m_slider.setSingleStep(20)
        self.m_slider.setMinimum(0) 
        self.m_slider.setMaximum(self.a-1)
        self.n_slider.setMinimum(self.b-1)
        self.n_slider.setMaximum(self.n)
        self.n_slider.setValue(self.n)
        self.m_slider.setMinimumSize(500, 0)
        self.m_slider.setMinimumSize(500, 0)
        self.m_slider.valueChanged[int].connect(self.change_M)
        self.n_slider.valueChanged[int].connect(self.change_N)
        
        self.m_lcd = QLCDNumber(self)
        self.n_lcd = QLCDNumber(self)
        
        self.m_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.n_lcd.setSegmentStyle(QLCDNumber.Flat)
        mpalette = self.m_lcd.palette()
        npalette = self.n_lcd.palette()
        mpalette.setColor(mpalette.Dark, QColor(0, 255, 0))
        npalette.setColor(npalette.Dark, QColor(0, 255, 0))
        self.m_lcd.setPalette(mpalette)
        self.n_lcd.setPalette(npalette)
        
        self.mLabel = QLabel('M', self)
        self.nLabel = QLabel('N', self)
        
        self.grid.addWidget(self.mLabel, 1,3)
        self.grid.addWidget(self.nLabel, 2,3)
        
        self.grid.addWidget(self.m_slider, 1,4)
        self.grid.addWidget(self.n_slider, 2,4)
        
        self.grid.addWidget(self.m_lcd, 1,5)
        self.grid.addWidget(self.n_lcd, 2,5)
        
        self.m_slider.valueChanged.connect(self.m_lcd.display)
        self.n_slider.valueChanged.connect(self.n_lcd.display)
        
        self.m = self.m_slider.value()
        self.n = self.n_slider.value()
            
    def changeData (self):
        newValues = list()
        
        for value in self.infoSet_2:
            newValues.append(value.text())
            
        self.FWHMconstant = float(newValues[0])
        self.polynomialOrder = float(newValues[1])
        
        QMessageBox.information(self, "Info", "Data was changed")
        
    def change_M(self, value):
        self.plot_1.plot(self.xarray[int(self.previousM)], self.y1array[int(self.previousM)], 'ko', markersize=1)
        self.plot_2.plot(self.xarray[int(self.previousM)], self.y2array[int(self.previousM)], 'ko', markersize=1)
        
        self.plot_1.annotation(self.xarray[int(self.previousM)], self.y1array[int(self.previousM)], " ")
        self.plot_2.annotation(self.xarray[int(self.previousM)], self.y2array[int(self.previousM)], " ")
        
        self.plot_1.remannotation()
        self.plot_2.remannotation()

        self.plot_1.annotation(self.xarray[int(value)], self.y1array[int(value)], "M")
        self.plot_2.annotation(self.xarray[int(value)], self.y2array[int(value)], "M")
        
        self.plot_1.plot(self.xarray[int(value)], self.y1array[int(value)], 'ro', markersize=1)
        self.plot_2.plot(self.xarray[int(value)], self.y2array[int(value)], 'ro', markersize=1)
         
        self.plot_1.canvasShow()
        self.plot_2.canvasShow()
 
        self.previousM = value
    
    def change_N(self, value):
        self.plot_1.plot(self.xarray[int(self.previousN-1)], self.y1array[int(self.previousN-1)], 'ko', markersize=1)
        self.plot_2.plot(self.xarray[int(self.previousN-1)], self.y2array[int(self.previousN-1)], 'ko', markersize=1)
        
        self.plot_1.annotation(self.xarray[int(self.previousN-1)], self.y1array[int(self.previousN-1)], " ")
        self.plot_2.annotation(self.xarray[int(self.previousN-1)], self.y2array[int(self.previousN-1)], " ")

        self.plot_1.remannotation()
        self.plot_2.remannotation()
        
        self.plot_1.annotation(self.xarray[int(value-1)], self.y1array[int(value-1)], "N")
        self.plot_2.annotation(self.xarray[int(value-1)], self.y2array[int(value-1)], "N")
        
        self.plot_1.plot(self.xarray[int(value-1)], self.y1array[int(value-1)], 'ro', markersize=1)
        self.plot_2.plot(self.xarray[int(value-1)], self.y2array[int(value-1)], 'ro', markersize=1)
        
        self.plot_1.canvasShow()
        self.plot_2.canvasShow()
        
        self.previousN = value
    
    def plotShortSpectr(self):
        self.setWindowTitle("Short Specter")
        self.m = self.m_slider.value()
        self.n = self.n_slider.value()
        
        if self.m < 0:
            self.m = 0
        
        self.plot_1.hide()
        self.plot_2.close()
        self.plot_1.hide()
        self.plot_2.close()
        self.grid.removeWidget(self.plot_1)
        self.grid.removeWidget(self.plot_2)
        self.plot_1.removePolt()
        self.plot_2.removePolt()
        del self.plot_1
        del self.plot_2
        
        self.m_slider.hide()
        self.m_slider.close()
        self.n_slider.hide()
        self.n_slider.close()
        self.grid.removeWidget(self.m_slider)
        self.grid.removeWidget(self.n_slider)
        del self.m_slider
        del self.n_slider
        
        self.plotSmoothDataButton.hide()
        self.plotSmoothDataButton.close()
        self.grid.removeWidget(self.plotSmoothDataButton)
        del self.plotSmoothDataButton
        
        self.m_lcd.hide()
        self.n_lcd.hide()
        self.m_lcd.close()
        self.n_lcd.close()
        self.grid.removeWidget(self.m_lcd)
        self.grid.removeWidget(self.n_lcd)
        del self.m_lcd
        del self.n_lcd
        
        self.mLabel.hide()
        self.mLabel.close()
        self.grid.removeWidget(self.mLabel)
        del self.mLabel
        
        self.nLabel.hide()
        self.nLabel.close()
        self.grid.removeWidget(self.nLabel)
        del self.nLabel
        
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
        self.changeDataButton.close()
        self.grid.removeWidget(self.changeDataButton)
        del self.changeDataButton
        
        self.xarray = self.xarray[self.m:self.n]
        self.y1array = self.y1array[self.m:self.n]
        self.y2array = self.y2array[self.m:self.n]
        
        #u1 plot
        self.plot_10 = Plot()
        self.plot_10.creatPlot(self.grid, 'Velocity (km sec$^{-1}$)', 'Flux density (Jy)', "1u Polarization", (1, 0))
        self.plot_10.plot(self.xarray, self.y1array, 'ko', label='Data Points',  markersize=1)
        
        #u9 plot
        self.plot_11 = Plot()
        self.plot_11.creatPlot(self.grid, 'Velocity (km sec$^{-1}$)', 'Flux density (Jy)', "9u Polarization", (1, 1))
        self.plot_11.plot(self.xarray, self.y2array, 'ko', label='Data Points',  markersize=1)
        
        self.grid.addWidget(self.plot_10, 0, 0)
        self.grid.addWidget(self.plot_11, 0, 1)
        
        self.plotPoly = QPushButton("Create Polynomial", self)
        self.grid.addWidget(self.plotPoly, 3, 3)
        self.plotPoly.clicked.connect(self.removeCuts)
        self.plotPoly.setStyleSheet("background-color: green")
        
    def removeCuts(self):
        cutsIndex = list()
        cutsIndex.append(0)

        for cut in self.cuts:
            cutsIndex.append((np.abs(self.xarray-float(cut[0]))).argmin()) 
            cutsIndex.append((np.abs(self.xarray-float(cut[1]))).argmin())
            
        cutsIndex.append(self.n)
        
        polyArray_x = list()
        polyArray_u1 = list()
        polyArray_u9 = list()
        
        i = 0
        j = 1
        
        while i != len(cutsIndex):
            polyArray_x.append(self.xarray[cutsIndex[i] : cutsIndex[j]])
            polyArray_u1.append(self.y1array[cutsIndex[i] : cutsIndex[j]])
            polyArray_u9.append(self.y2array[cutsIndex[i] : cutsIndex[j]])
            i = i + 2 
            j = j + 2
            
        poly_x = list()
        poly_u1 = list()
        poly_u9 = list()
        
        for p in polyArray_x:
            for p1 in p:
                poly_x.append(p1)
                
        for p in polyArray_u1:
            for p1 in p:
                poly_u1.append(p1)
        
        for p in polyArray_u9:
            for p1 in p:
                poly_u9.append(p1)
            
        self.polyx = np.array(poly_x)
        self.polyu1 = np.array(poly_u1)
        self.polyu9 = np.array(poly_u9)
        
        z_u1 = np.polyfit(self.polyx, self.polyu1, self.polynomialOrder)
        self.p_u1 = np.poly1d(z_u1)
        
        z_u9 = np.polyfit(self.polyx, self.polyu9, self.polynomialOrder)
        self.p_u9 = np.poly1d(z_u9)
        
        self.plot_10.hide()
        self.plot_11.close()
        self.plot_10.hide()
        self.plot_11.close()
        self.grid.removeWidget(self.plot_10)
        self.grid.removeWidget(self.plot_11)
        self.plot_10.removePolt()
        self.plot_11.removePolt()
        del self.plot_10
        del self.plot_11
        
        self.plotPoly.hide()
        self.plotPoly.close()
        self.grid.removeWidget(self.plotPoly)
        del self.plotPoly
        
        #u1 plot
        self.plot_5 = Plot()
        self.plot_5.creatPlot(self.grid, 'Velocity (km sec$^{-1}$)', 'Flux density (Jy)', "1u Polarization", (1, 0))
        self.plot_5.plot(self.polyx, self.polyu1, 'ko', label='Data Points',  markersize=1)
        #self.plot_5.plot(self.xarray[self.m:self.n], self.ceb_1(self.xarray[self.m:self.n]), 'r', label='Chebyshev polynomial', markersize=1)
        self.plot_5.plot(self.xarray, self.p_u1(self.xarray), 'b', label='Numpy polyfit', markersize=1)
        
        #u9 plot
        self.plot_6 = Plot()
        self.plot_6.creatPlot(self.grid, 'Velocity (km sec$^{-1}$)', 'Flux density (Jy)', "9u Polarization", (1, 1))
        self.plot_6.plot(self.polyx, self.polyu9, 'ko', label='Data Points',  markersize=1)
        #self.plot_6.plot(self.xarray[self.m:self.n], self.ceb_2(self.xarray[self.m:self.n]), 'r', label='Chebyshev polynomial', markersize=1)
        self.plot_6.plot(self.xarray, self.p_u9(self.xarray), 'b', label='Numpy polyfit', markersize=1)
        
        self.grid.addWidget(self.plot_5, 0, 0)
        self.grid.addWidget(self.plot_6, 0, 1)
        
        self.plotPoly = QPushButton("Create local maximums", self)
        self.grid.addWidget(self.plotPoly, 3, 3)
        self.plotPoly.clicked.connect(self.plotLocalMaximum)
        self.plotPoly.setStyleSheet("background-color: green")
    
        
    def plotLocalMaximum(self):
        self.setWindowTitle("Local maximums")
        
        self.plot_5.hide()
        self.plot_5.close()
        self.plot_6.hide()
        self.plot_6.close()
        self.grid.removeWidget(self.plot_5)
        self.grid.removeWidget(self.plot_6)
        self.plot_5.removePolt()
        self.plot_6.removePolt()
        del self.plot_5
        del self.plot_6
        
        self.plotPoly.hide()
        self.plotPoly.close()
        self.grid.removeWidget(self.plotPoly)
        del self.plotPoly
        
        self.monitoringButton = QPushButton("Add points to monitoring", self)
        self.grid.addWidget(self.monitoringButton, 3, 3)
        self.monitoringButton.clicked.connect(self.createResult)
        self.monitoringButton.setStyleSheet("background-color: green")
        
        self.localMax_Array_u1 = self.y1array - self.p_u1(self.xarray)
        self.localMax_Array_u9 = self.y2array - self.p_u9(self.xarray)
        
        # Smoohting
        g1 = Gaussian1DKernel(stddev=3, x_size=19, mode='center', factor=100)
        g2 = Gaussian1DKernel(stddev=3, x_size=19, mode='center', factor=100)
    
        self.z1 = convolve(self.localMax_Array_u1, g1, boundary='extend')
        self.z2 = convolve(self.localMax_Array_u9, g2, boundary='extend')
         
        thres=0.1
           
        #indexsu apreikinasana
        indexes_for_ceb = peakutils.indexes(self.z1, thres=thres, min_dist=10)
        indexes_for_ceb2 = peakutils.indexes(self.z2, thres=thres, min_dist=10)
        
        self.plot_7 = Plot()
        self.plot_7.creatPlot(self.grid, 'Velocity (km sec$^{-1}$)', 'Flux density (Jy)', "1u Polarization", (1, 0))
        self.plot_7.plot(self.xarray, self.z1, 'b', label='Signal - polynomial', markersize=1)
        self.plot_7.plot(self.xarray[indexes_for_ceb], self.z1[indexes_for_ceb], 'dr', label="Local Maximums for signal", markersize=2, picker=5)
        self.plot_7.addPickEvent(self.onpick_maxU1)
        self.plot_7.annotations(self.xarray[indexes_for_ceb], self.z1[indexes_for_ceb])
        
        #u9
        self.plot_8 = Plot()
        self.plot_8.creatPlot(self.grid, 'Velocity (km sec$^{-1}$)', 'Flux density (Jy)', "9u Polarization", (1, 1))
        self.plot_8.plot(self.xarray, self.z2, 'b', label='Signal - polynomial', markersize=1)
        self.plot_8.plot(self.xarray[indexes_for_ceb2], self.z2[indexes_for_ceb2], 'dr', label="Local Maximums for signal", markersize=2, picker=5)
        self.plot_8.addPickEvent(self.onpick_maxU9)
        self.plot_8.annotations(self.xarray[indexes_for_ceb2], self.z2[indexes_for_ceb2])
        
        #mid plot
        avg_y = (self.z1 + self.z2) / 2
        
        indexes_for_avg = peakutils.indexes(avg_y, thres=thres, min_dist=10)
        
        self.plot_9 = Plot()
        self.plot_9.creatPlot(self.grid, 'Velocity (km sec$^{-1}$)', 'Flux density (Jy)', "Average Polarization", (1, 2))
        self.plot_9.plot(self.xarray, avg_y, 'b', label='Signal - polynomial', markersize=1)
        self.plot_9.plot(self.xarray[indexes_for_avg], avg_y[indexes_for_avg], 'dr', label="Local Maximums for signal", markersize=2, picker=5)
        self.plot_9.addPickEvent(self.onpick_maxAVG)
        self.plot_9.annotations(self.xarray[indexes_for_avg], avg_y[indexes_for_avg])
        
        self.grid.addWidget(self.plot_7, 0, 0)
        self.grid.addWidget(self.plot_8, 0, 1)
        self.grid.addWidget(self.plot_9, 0, 2)
        
        self.maxU1 = list()
        self.maxU9 = list()
        self.avgMax = list()
        self.maxu1_index = list()
        self.maxu9_index = list()
        self.maxavg_index = list()
        
    def createResult(self):
        resultFileName = self.source + ".json"
        
        if os.path.isfile(self.resultFilePath + resultFileName):
            pass
        else:
            os.system("touch " + self.resultFilePath +  resultFileName)
            
            resultFile = open (self.resultFilePath +  resultFileName, "w")
            resultFile.write("{ \n" + "\n}")
            resultFile.close()
        
        with open(self.resultFilePath + resultFileName) as result_data:    
            result = json.load(result_data)
        
        if self.expername not in result:
            result[self.expername] = dict()
            
        for source_vel in self.source_velocities:
            if all (np.abs(item[0] - float(source_vel)) >= 0.09 for item in self.maxU1):
                
                self.maxU1.append([float(source_vel), 0])
                
            if all (np.abs(item[0] - float(source_vel)) >= 0.09 for item in self.maxU9):
                self.maxU9.append([float(source_vel), 0])
            
            if all (np.abs(item[0] - float(source_vel)) >= 0.09 for item in self.avgMax):
                self.avgMax.append([float(source_vel), 0]) 
                
        self.maxU1.sort(key=lambda tup: tup[0], reverse=True)
        self.maxU9.sort(key=lambda tup: tup[0], reverse=True)
        self.avgMax.sort(key=lambda tup: tup[0], reverse=True)
              
        result[self.expername]["location"] = self.location
        result[self.expername]["Date"] = self.date
        result[self.expername]["Iteration_number"] = int(self.iteration_number)
                
        result[self.expername]["polarizationU1"] = self.maxU1
        result[self.expername]["polarizationU9"] = self.maxU9
        result[self.expername]["polarizationAVG"] = self.avgMax
                
        #result[self.expername][self.scanNumber]["index_for_polarizationU1"] =  self.maxu1_index
        #result[self.expername][self.scanNumber]["index_for_polarizationU9"] =  self.maxu9_index
        #result[self.expername][self.scanNumber]["index_for_polarizationAVG"] =  self.maxavg_index
        
        #result =  sorted(result, key = lambda i: result[i]['Iteration_number'])
        resultFile = open (self.resultFilePath +  resultFileName, "w")
        resultFile.write(json.dumps(result, indent=2))
        resultFile.close()
        
        self._quit()
    
    @QtCore.pyqtSlot()   
    def _quit(self):
        for i in reversed(range(self.grid.count())): 
            self.grid.itemAt(i).widget().deleteLater()
        
        self.hide()
        self.close()
        del self
              
def main():
    args = parseArguments()
   
    datafile = str(args.__dict__["datafile"])
    configFilePath = str(args.__dict__["config"])
    
    config = configparser.RawConfigParser()
    config.read(configFilePath)
    dataFilesPath =  config.get('paths', "dataFilePath")
    resultFilePath =  config.get('paths', "resultFilePath")
    source = datafile.split("/")[-1].split(".")[0].split("_")[0]
    cuts = config.get('cuts', source).split(";")
    cuts = [c.split(",") for c in  cuts]
    print ("source", source)
    source_velocities = config.get('velocities', source).replace(" ", "").split(",")
    
    #Create App
    qApp = QApplication(sys.argv)

    aw = Analyzer(dataFilesPath + datafile, resultFilePath, source_velocities, cuts)
    aw.show()
    aw.showMaximized() 
    sys.exit(qApp.exec_())
    
    sys.exit(0)
                
if __name__=="__main__":
    main()
#! /usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import (QWidget, QGridLayout, QApplication, QDesktopWidget, QPushButton, QInputDialog)
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore
import argparse
import configparser
import json
import matplotlib
import pickle
import numpy as np
import scipy.constants
import pandas as pd
from pandas import Series
#from pandas.stats.moments import rolling_mean

from experimentsLogReader import ExperimentLogReader
from ploting_qt5 import  Plot

def parseArguments():
    # Create argument parser
    parser = argparse.ArgumentParser(description='''Creates input file for plotting tool. ''', epilog="""PRE PLOTTER.""")
    
    # Positional mandatory arguments
    parser.add_argument("source", help="Experiment source", type=str, default="")
    parser.add_argument("iteration_number", help="iteration number ", type=int)
    parser.add_argument("logFile", help="Experiment log file name", type=str)

    # Optional arguments
    parser.add_argument("-c", "--config", help="Configuration cfg file", type=str, default="config/config.cfg")
    parser.add_argument("-t", "--threshold", help="Set threshold for outlier filter", type=float, default=1.0)
    parser.add_argument("-f", "--filter", help="Set the amount of times to filter data to remove noise spikes, higher than 5 makes little difference", type=int, default=0,
                        choices=range(0,11),metavar="[0-10]")
    parser.add_argument("-m", "--manual", help="Set manual log data", action='store_true')

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

def is_outlier(points, threshold):
    if len(points.shape) == 1:
        points = points[:,None]
    median = np.median(points, axis=0)
    diff = np.sum((points - median)**2, axis=-1)
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)

    modified_z_score =  0.6745 * diff / med_abs_deviation
    #print(modified_z_score)
    return modified_z_score < threshold

def dopler(ObservedFrequency, velocityReceiver, f0):
    c = scipy.constants.speed_of_light
    #f0 = 6668519200 # Hz 
    velocitySoure = (-((ObservedFrequency/f0)-1)*c + (velocityReceiver * 1000))/1000
    return velocitySoure

def indexies(array, value):
    indexs = list()
    for i in range(0, len(array)-1):
        if array[i] == value:
            indexs.append(i)
    return indexs

def STON(xarray, yarray, cuts):
    cutsIndex = list()
    cutsIndex.append(0)

    for cut in cuts:
        cutsIndex.append((np.abs(xarray-float(cut[0]))).argmin()) 
        cutsIndex.append((np.abs(xarray-float(cut[1]))).argmin())
            
    cutsIndex.append(-1)
        
    y_array = list()
     
    i = 0
    j = 1
        
    while i != len(cutsIndex):
        y_array.append(yarray[cutsIndex[i] : cutsIndex[j]])
        i = i + 2 
        j = j + 2
    
    y = list()
             
    for p in y_array:
        for p1 in p:
            y.append(p1)
        
    y = np.array(y)
    
    std = np.std(y) 
    max = np.max(yarray)
    
    ston = max/(std*3)
    return ston

def func():
    pass

class Result():
    def __init__(self, matrix, specie):
        self.matrix = matrix
        self.specie = specie
        
    def getMatrix(self):
        return self.matrix
    
    def getSpecie(self):
        return self.specie

class Analyzer(QWidget):
    def __init__(self, source, iteration_number, filter, threshold, badPointRange, dataPath, resultPath, logs, DPFU_max, G_El, Tcal, k, fstart, cuts, firstScanStartTime, base_frequencies):
        super().__init__()
       
        self.setWindowIcon(QIcon('viraclogo.png'))
        self.center()
        
        self.source = source
        self.threshold = threshold
        self.filter = filter
        self.badPointRange = badPointRange
        self.dataFilesPath = dataPath
        self.resultPath = resultPath
        self.index = 0
        self.totalResults_u1 = list()
        self.totalResults_u9 = list()
        self.STON_list_u1 = list()
        self.STON_list_u9 = list()
        self.STON_list_AVG = list()
        self.iteration_number = iteration_number
        self.logs = logs 
        self.date = self.logs["header"]["dates"]
        self.dataFileDir = dataPath + self.source + "/" + str(self.iteration_number) + "/"
        self.scanPairs = self.createScanPairs()
        self.datPairsCount = len(self.scanPairs)
        self.f0 = 6668519200
        self.location = self.logs["header"]["location"]
        self.expername = self.source + self.date + "_" + self.location
        self.DPFU_max = DPFU_max
        self.G_El = G_El
        self.Tcal = Tcal
        self.k = k
        self.fstart = fstart
        self.cuts = cuts
        self.firstScanStartTime = firstScanStartTime
        self.base_frequencies = base_frequencies
        self.base_frequencies_list = list()
        
        for value in self.base_frequencies:
            self.base_frequencies_list.append(float(self.base_frequencies[value]))
        
        self.setWindowTitle("Analyze for " + self.source + " " + self.date)
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.setSpacing(10)
        
        self.__UI__()
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def createScanPairs(self):
        dataFiles = list()
        for dataFile in os.listdir(self.dataFileDir):
            dataFiles.append(dataFile)
            
        dataFiles.sort()
        
        scanPairs = list()
        i = 0
        j = 1
            
        for k in range(0, int(len(dataFiles) - len(dataFiles) /2)):
            scanPairs.append((dataFiles[i], dataFiles[j])) 
            i = i + 2
            j = j + 2
            
        return scanPairs
        
    def __getDataForPolarization__(self, data1, data2, filter):

        if filter > 0:
            ndata1 = np.array(data1)
            ndata2 = np.array(data2)
            for x in range(filter+1):
                outliersMask_1 = is_outlier(ndata1, self.threshold)
                outliersMask_2 = is_outlier(ndata2, self.threshold)

                bad_point_index_1 = indexies(outliersMask_1, False)
                bad_point_index_2 = indexies(outliersMask_2, False)

                xdata = ndata1[:, [0]].tolist()
                ydata_1_u1 = ndata1[:, [1]].tolist()
                ydata_2_u1 = ndata2[:, [1]].tolist()
                ydata_1_u9 = ndata1[:, [2]].tolist()
                ydata_2_u9 = ndata2[:, [2]].tolist()

                if x==0:
                    self.y_bad_point_1_u1 = []
                    self.x_bad_point_1_u1 = []

                    for idx, point in enumerate(outliersMask_1):
                        if point == False:
                            self.x_bad_point_1_u1.append(data1[idx, [0]][0])
                            self.y_bad_point_1_u1.append(data1[idx, [1]][0])

                    self.y_bad_point_2_u1 = []
                    self.x_bad_point_2_u1 = []

                    for idx, point in enumerate(outliersMask_2):
                        if point == False:
                            self.x_bad_point_2_u1.append(data2[idx, [0]][0])
                            self.y_bad_point_2_u1.append(data2[idx, [1]][0])

                    self.y_bad_point_1_u9 = []
                    self.x_bad_point_1_u9 = []

                    for idx, point in enumerate(outliersMask_1):
                        if point == False:
                            self.x_bad_point_1_u9.append(data1[idx, [0]][0])
                            self.y_bad_point_1_u9.append(data1[idx, [2]][0])

                    self.y_bad_point_2_u9 = []
                    self.x_bad_point_2_u9 = []

                    for idx, point in enumerate(outliersMask_2):
                        if point == False:
                            self.x_bad_point_2_u9.append(data2[idx, [0]][0])
                            self.y_bad_point_2_u9.append(data2[idx, [2]][0])



                df_y1_u1 = pd.DataFrame(data=ydata_1_u1)
                df_y1_u9 = pd.DataFrame(data=ydata_1_u9)
                df_y2_u1 = pd.DataFrame(data=ydata_2_u1)
                df_y2_u9 = pd.DataFrame(data=ydata_2_u9)

                mean_y1_u1 = np.nan_to_num(df_y1_u1.rolling(window=self.badPointRange, center=True).mean())
                mean_y1_u9 = np.nan_to_num(df_y1_u9.rolling(window=self.badPointRange, center=True).mean())
                mean_y2_u1 = np.nan_to_num(df_y2_u1.rolling(window=self.badPointRange, center=True).mean())
                mean_y2_u9 = np.nan_to_num(df_y2_u9.rolling(window=self.badPointRange, center=True).mean())

                """
                TODO
                
                Plotot nevis jaunos grafikus, bet gan originalo data,
                n-tās pakāpes polinomu aizvieto nevis ar mediānu,
                ar roku izdzēst punktus.
                
                """

                for badPoint in bad_point_index_1:
                    if mean_y1_u1[badPoint]!=0: #badpoint==0 galos
                        ydata_1_u1[badPoint][0] = mean_y1_u1[badPoint]

                for badPoint in bad_point_index_1:
                    if mean_y1_u9[badPoint]!=0:
                        ydata_1_u9[badPoint][0] = mean_y1_u9[badPoint]

                for badPoint in bad_point_index_2:
                    if mean_y2_u1[badPoint]!=0:
                        ydata_2_u1[badPoint][0] = mean_y2_u1[badPoint]

                for badPoint in bad_point_index_2:
                    if mean_y2_u9[badPoint]!=0:
                        ydata_2_u9[badPoint][0] = mean_y2_u9[badPoint]
                xdata = np.array(xdata)
                ydata_1_u1 = np.array(ydata_1_u1)
                ydata_2_u1 = np.array(ydata_2_u1)
                ydata_1_u9 = np.array(ydata_1_u9)
                ydata_2_u9 = np.array(ydata_2_u9)

                ndata1[:,[1]] = ydata_1_u1
                ndata2[:,[1]] = ydata_2_u1
                ndata1[:,[2]] = ydata_1_u9
                ndata2[:,[2]] = ydata_2_u9

                if x==filter:
                    xlist = xdata.tolist()  #need list because np array has no .index() function

                    tempx = []
                    tempy = []

                    for idx, point in enumerate(self.x_bad_point_1_u1):
                        index = xlist.index(point)
                        if (self.y_bad_point_1_u1[idx] / ydata_1_u1[index][0] > 1.10 or
                                self.y_bad_point_1_u1[idx] / ydata_1_u1[index][0] < 0.90):
                            tempx.append(self.x_bad_point_1_u1[idx])
                            tempy.append(self.y_bad_point_1_u1[idx])
                        else:
                            ydata_1_u1[index][0] = data1[index, [1]][0]

                    self.x_bad_point_1_u1 = tempx
                    self.y_bad_point_1_u1 = tempy

                    tempx = []
                    tempy = []

                    for idx, point in enumerate(self.x_bad_point_2_u1):
                        index = xlist.index(point)
                        if (self.y_bad_point_2_u1[idx] / ydata_2_u1[index][0] > 1.10 or
                                self.y_bad_point_2_u1[idx] / ydata_2_u1[index][0] < 0.90):
                            tempx.append(self.x_bad_point_2_u1[idx])
                            tempy.append(self.y_bad_point_2_u1[idx])
                        else:
                            ydata_2_u1[index][0] = data2[index, [1]][0]


                    self.x_bad_point_2_u1 = tempx
                    self.y_bad_point_2_u1 = tempy

                    tempx = []
                    tempy = []

                    for idx, point in enumerate(self.x_bad_point_1_u9):
                        index = xlist.index(point)
                        if (self.y_bad_point_1_u9[idx] / ydata_1_u9[index][0] > 1.10 or
                                self.y_bad_point_1_u9[idx] / ydata_1_u9[index][0] < 0.90):
                            tempx.append(self.x_bad_point_1_u9[idx])
                            tempy.append(self.y_bad_point_1_u9[idx])
                        else:
                            ydata_1_u9[index][0] = data1[index, [2]][0]

                    self.x_bad_point_1_u9 = tempx
                    self.y_bad_point_1_u9 = tempy

                    tempx = []
                    tempy = []

                    for idx, point in enumerate(self.x_bad_point_2_u9):
                        index = xlist.index(point)
                        if (self.y_bad_point_2_u9[idx] / ydata_2_u9[index][0]  > 1.10 or
                                self.y_bad_point_2_u9[idx] / ydata_2_u9[index][0]  < 0.90):
                            tempx.append(self.x_bad_point_2_u9[idx])
                            tempy.append(self.y_bad_point_2_u9[idx])
                        else:
                            ydata_2_u9[index][0] = data2[index, [2]][0]

                    self.x_bad_point_2_u9 = tempx
                    self.y_bad_point_2_u9 = tempy



                self.dataPoints = len(xdata)

            return (xdata, ydata_1_u1, ydata_2_u1, ydata_1_u9, ydata_2_u9)

            sys.exit(3)
            pass

        else:
            xdata = data1[:, [0]]
            ydata_1_u1 = data1[:, [1]]
            ydata_2_u1 = data2[:, [1]]
            ydata_1_u9 = data1[:, [2]]
            ydata_2_u9 = data2[:, [2]]

            self.dataPoints = len(xdata)

            return (xdata, ydata_1_u1, ydata_2_u1, ydata_1_u9, ydata_2_u9)

    def calibration(self, array_x, data_1, data_2, tsys_1, tsys_2, elevation):
        #from AGN cal sessions (FS /usr2/control/rxg_files/c3.rxg):

        DPFU = np.mean(self.DPFU_max)*np.polyval(self.G_El, elevation)

        P_sig = data_1 # Get Amplitudes
        P_ref = data_2 # Get Amplitudes

        Ta_sig = float(tsys_1)*(P_sig - P_ref)/P_ref #only non-cal phase for dbbc possible...
        Ta_ref = float(tsys_2)*(P_ref - P_sig)/P_sig

        f_shift = np.max(array_x) /4.0
        f_step = (array_x[self.dataPoints-1]-array_x[0])/(self.dataPoints-1);
        n_shift = int(f_shift/f_step);

        Ta_sig = np.roll(Ta_sig, n_shift); # pos
        Ta_ref = np.roll(Ta_ref, -n_shift); # neg
            
        #avg shifted spectrums
        Ta = (Ta_sig + Ta_ref)/2 # Creting total spectr
            
        #K->Jy
        Ta = Ta/DPFU/self.k
  
        return Ta
    
    def nextPair(self):
        if self.index == self.datPairsCount -1:
            pass
        
        else:
            self.plot_start_u1.removePolt()
            self.plot_start_u9.removePolt()
            self.plot_total_u1.removePolt()
            self.plot_total_u9.removePolt()
            self.index = self.index + 1
            self.plotingPairs(self.index)
        
    def plotingPairs(self, index):
        pair = self.scanPairs[index]
            
        scanNUmber1 = self.dataFileDir + "/" + pair[0]
        scanNUmber2 = self.dataFileDir + "/" + pair[1]
        
        print ("data files ", scanNUmber1, scanNUmber2)
            
        scan_number_1 = pair[0].split(".")[0].split("_")[-1][2:].lstrip("0")
        scan_number_2 = pair[1].split(".")[0].split("_")[-1][2:].lstrip("0")
            
        print ("scan number", scan_number_1, scan_number_2)
            
        scan_1 = self.logs[str(scan_number_2)]
        scan_2 = self.logs[str(scan_number_1)]
            
        # get system temperature
        tsys_u1_1 = scan_1['Systemtemperature'][0]
        tsys_u1_2 = tsys_u1_1
        tsys_u9_1 = scan_1['Systemtemperature'][1]
        tsys_u9_2 = tsys_u9_1
            
        elevation = (float(scan_1["elevation"]) + float(scan_2["elevation"])) /2
        
        print ("elevation", elevation)
            
        print ("tsys", tsys_u1_1, tsys_u9_1)
        
        if float(tsys_u1_1) == 0:
            newT, ok = QInputDialog.getDouble(self, 'tsys error', 'Enter valid tsys:', 0, 1, 300)
            tsys_u1_1 = newT
            
        if float(tsys_u9_1) == 0:
            newT, ok = QInputDialog.getDouble(self, 'tsys error', 'Enter valid tsys:', 0, 1, 300)
            tsys_u9_1 = newT
            
        try:    
            data_1 = np.fromfile(scanNUmber1, dtype="float64", count=-1, sep=" ") .reshape((file_len(scanNUmber1),9))
            data_2 = np.fromfile(scanNUmber2, dtype="float64", count=-1, sep=" ") .reshape((file_len(scanNUmber2),9))
            
        except IOError as e:
            print ("IO Error",  e)
            sys.exit(1)
            
        else:
            
            #Delete first row
            data_1 = np.delete(data_1, (0), axis=0) #izdzes masiva primo elementu
            data_2 = np.delete(data_2, (0), axis=0) #izdzes masiva primo elementu
                  
            xdata, ydata_1_u1, ydata_2_u1, ydata_1_u9, ydata_2_u9 = self.__getDataForPolarization__(data_1, data_2, self.filter)



            self.plot_start_u1 = Plot()

            #self.plot_start_u1.fig.canvas.mpl_connect('button_press_event', lambda event: self._on_press_u1(event, xdata, ydata_1_u1, ydata_2_u1))

            self.plot_start_u1.setFocusPolicy(QtCore.Qt.ClickFocus)
            self.plot_start_u1.setFocus()
            self.plot_start_u1.creatPlot(self.grid, 'Frequency Mhz', 'Amplitude', "u1 Polarization", (1, 0))
            self.plot_start_u1.plot(xdata, ydata_1_u1, 'b', label=pair[0])
            self.plot_start_u1.plot(xdata, ydata_2_u1, 'r', label=pair[1])

            if (self.filter > 0):
                self.plot_start_u1.plot(self.x_bad_point_1_u1, self.y_bad_point_1_u1, 'x')
                self.plot_start_u1.plot(self.x_bad_point_2_u1, self.y_bad_point_2_u1, 'x')

            self.plot_start_u9 = Plot()


            self.plot_start_u9.setFocusPolicy(QtCore.Qt.ClickFocus)
            self.plot_start_u9.setFocus()
            self.plot_start_u9.creatPlot(self.grid, 'Frequency Mhz', 'Amplitude', "u9 Polarization", (1, 1))
            self.plot_start_u9.plot(xdata, ydata_1_u9, 'b', label=pair[0], picker=5)
            self.plot_start_u9.plot(xdata, ydata_2_u9, 'r', label=pair[1], picker=5)

            if (self.filter > 0):
                self.plot_start_u9.plot(self.x_bad_point_1_u9, self.y_bad_point_1_u9, 'x')
                self.plot_start_u9.plot(self.x_bad_point_2_u9, self.y_bad_point_2_u9, 'x')

            self.plot_start_u9.fig.canvas.mpl_connect('pick_event', lambda event: self._on_left_click(event, xdata, ydata_2_u9))
            self.plot_start_u9.fig.canvas.mpl_connect('pick_event', lambda event: self._on_right_click(event, xdata, ydata_1_u9))


            self.grid.addWidget(self.plot_start_u1, 0, 0)
            self.grid.addWidget(self.plot_start_u9, 0, 1)
            
            #Calibration  
            data_u1 = self.calibration(xdata, ydata_1_u1, ydata_2_u1, float(tsys_u1_1), float(tsys_u1_2), elevation) 
            data_u9 = self.calibration(xdata, ydata_1_u9, ydata_2_u9, float(tsys_u9_1), float(tsys_u9_2), elevation)
           
            xdata = np.array(xdata)
                
            self.x = xdata
            f_step = (self.x[self.dataPoints-1]-self.x[0])/(self.dataPoints-1)
            f_shift = np.max(self.x) / 4.0
            n_shift = int(f_shift/f_step)
            total_u1 = data_u1[(n_shift+1):(self.dataPoints - n_shift - 1)]
            total_u9 = data_u9[(n_shift+1):(self.dataPoints - n_shift - 1)]
            
            self.x = self.x[(n_shift+1):(self.dataPoints - n_shift - 1)] 
            
            self.totalResults_u1.append(total_u1)
            self.totalResults_u9.append(total_u9)
            
            self.plot_total_u1 = Plot()
            self.plot_total_u1.creatPlot(self.grid, 'Frequency Mhz', 'Flux density (Jy)', None, (5, 0))
            self.plot_total_u1.plot(self.x, total_u1, 'b')
            
            self.plot_total_u9 = Plot()
            self.plot_total_u9.creatPlot(self.grid, 'Frequency Mhz', 'Flux density (Jy)', None, (5, 1))
            self.plot_total_u9.plot(self.x, total_u9, 'b')
            
            self.grid.addWidget(self.plot_total_u1, 4, 0)
            self.grid.addWidget(self.plot_total_u9, 4, 1)
                
            ston_u1 = STON(self.x, total_u1, self.cuts)
            ston_u9 = STON(self.x, total_u9, self.cuts)
            stone_AVG = STON(self.x, ((total_u1 + total_u9)/2), self.cuts)
            
            self.STON_list_u1.append(ston_u1)
            self.STON_list_u9.append(ston_u9)
            self.STON_list_AVG.append(stone_AVG)
            
            if index == self.datPairsCount -1:
                self.nextPairButton.setText('Move to total results')
                self.nextPairButton.clicked.connect(self.plotTotalResults)
                self.grid.removeWidget(self.skipAllButton)
                self.skipAllButton.hide()
                self.skipAllButton.close()
                del self.skipAllButton
    
    def __PAIR(self, index, totalResults_u1, totalResults_u9, STON_list_u1, STON_list_u9, STON_list_AVG):
        pair = self.scanPairs[index]
            
        scanNUmber1 = self.dataFileDir + "/" + pair[0]
        scanNUmber2 = self.dataFileDir + "/" + pair[1]
            
        scan_number_1 = pair[0].split(".")[0].split("_")[-1][2:].lstrip("0")
        scan_number_2 = pair[1].split(".")[0].split("_")[-1][2:].lstrip("0")
            
        scan_1 = self.logs[str(scan_number_2)]
        scan_2 = self.logs[str(scan_number_1)]
            
        # get system temperature
        tsys_u1_1 = scan_1['Systemtemperature'][0]
        tsys_u1_2 = tsys_u1_1
        tsys_u9_1 = scan_1['Systemtemperature'][1]
        tsys_u9_2 = tsys_u9_1
            
        elevation = (float(scan_1["elevation"]) + float(scan_2["elevation"])) /2
            
        if float(tsys_u1_1) == 0:
            newT, ok = QInputDialog.getDouble(self, 'tsys error', 'Enter valid tsys:', 0, 1, 300)
            tsys_u1_1 = newT
            
        if float(tsys_u9_1) == 0:
            newT, ok = QInputDialog.getDouble(self, 'tsys error', 'Enter valid tsys:', 0, 1, 300)
            tsys_u9_1 = newT
        
        try:  
            data_1 = np.fromfile(scanNUmber1, dtype="float64", count=-1, sep=" ") .reshape((file_len(scanNUmber1),9))
            data_2 = np.fromfile(scanNUmber2, dtype="float64", count=-1, sep=" ") .reshape((file_len(scanNUmber2),9))
        except IOError as e:
            print ("IO Error",  e)
            sys.exit(1)
        
        except IndexError as e:
            print ("Index Error",  e)
            sys.exit(1)
            
        except:
            print("Unexpected error:", sys.exc_info()[0])
            sys.exit(1)
            
        else:
                
            #Delete first row
            data_1 = np.delete(data_1, (0), axis=0) #izdzes masiva primo elementu
            data_2 = np.delete(data_2, (0), axis=0) #izdzes masiva primo elementu
                      
            xdata, ydata_1_u1, ydata_2_u1, ydata_1_u9, ydata_2_u9 = self.__getDataForPolarization__(data_1, data_2, self.filter)
                
            #Calibration  
            data_u1 = self.calibration(xdata, ydata_1_u1, ydata_2_u1, float(tsys_u1_1), float(tsys_u1_2), elevation) 
            data_u9 = self.calibration(xdata, ydata_1_u9, ydata_2_u9, float(tsys_u9_1), float(tsys_u9_2), elevation)
               
            xdata = np.array(xdata)
                    
            self.x = xdata
            f_step = (self.x[self.dataPoints-1]-self.x[0])/(self.dataPoints-1)
            f_shift = np.max(self.x) / 4.0
            n_shift = int(f_shift/f_step)
            total_u1 = data_u1[(n_shift+1):(self.dataPoints - n_shift - 1)]
            total_u9 = data_u9[(n_shift+1):(self.dataPoints - n_shift - 1)]
                
            self.x = self.x[(n_shift+1):(self.dataPoints - n_shift - 1)] 
                
            totalResults_u1.append(total_u1)
            totalResults_u9.append(total_u9)
                
            ston_u1 = STON(self.x, total_u1, self.cuts)
            ston_u9 = STON(self.x, total_u9, self.cuts)
            stone_AVG = STON(self.x, ((total_u1 + total_u9)/2), self.cuts)
                
            STON_list_u1.append(ston_u1)
            STON_list_u9.append(ston_u9)
            STON_list_AVG.append(stone_AVG)
            
    def skipAll(self):
        totalResults_u1= list()
        totalResults_u9= list()
        
        STON_list_u1= list()
        STON_list_u9= list()
        STON_list_AVG= list()
        
        for index in range(0, len(self.scanPairs)):
            self.__PAIR(index, totalResults_u1, totalResults_u9, STON_list_u1, STON_list_u9, STON_list_AVG)
        
        self.totalResults_u1 = totalResults_u1
        self.totalResults_u9 = totalResults_u9
        self.STON_list_u1 = STON_list_u1
        self.STON_list_u9 = STON_list_u9
        self.STON_list_AVG = STON_list_AVG
        
        self.plotTotalResults()
            
    def plotTotalResults(self):
       
        self.grid.removeWidget(self.plot_start_u1)
        self.grid.removeWidget(self.plot_start_u9)
        self.grid.removeWidget(self.plot_total_u1)
        self.grid.removeWidget(self.plot_total_u9)
        
        self.plot_start_u1.hide()
        self.plot_start_u9.hide()
        self.plot_total_u1.hide()
        self.plot_total_u9.hide()
        
        self.plot_start_u1.close()
        self.plot_start_u9.close()
        self.plot_total_u1.close()
        self.plot_total_u9.close()
        
        self.plot_start_u1.removePolt()
        self.plot_start_u9.removePolt()
        self.plot_total_u1.removePolt()
        self.plot_total_u9.removePolt()
        
        del self.plot_start_u1
        del self.plot_start_u9
        del self.plot_total_u1
        del self.plot_total_u9
        
        self.grid.removeWidget(self.nextPairButton)
        self.nextPairButton.hide()
        self.nextPairButton.close()
        del self.nextPairButton 
        
        for i in reversed(range(self.grid.count())): 
            self.grid.itemAt(i).widget().deleteLater()
        
        velocitys_avg = np.zeros(self.totalResults_u1[0].shape)
        y_u1_avg = np.zeros(self.totalResults_u1[0].shape)
        y_u9_avg = np.zeros(self.totalResults_u9[0].shape)
        
        FreqStart = self.fstart +  float(self.logs["header"]["BBC"])
        print ("FreqStart", FreqStart, "BBC", float(self.logs["header"]["BBC"]))                                
        for p in range(0,  self.datPairsCount):
            scan_number_1 = self.scanPairs[p][0].split("_")[-1][2:].lstrip("0").split(".")[0]
            scan_number_2 = self.scanPairs[p][1].split("_")[-1][2:].lstrip("0").split(".")[0]
            print ("\npairs ", self.scanPairs[p])
            scan_1 = self.logs[str(scan_number_1)]
            scan_2 = self.logs[str(scan_number_2)]
            
            timeStr = scan_1['startTime'].replace(":", " ")
            dateStrList = scan_1['dates'].split()
            months = {"Jan":"1", "Feb":"2", "Mar":"3", "Apr":"4", "May":"5", "Jun":"6", "Jul":"7", "Aug":"8", "Sep":"9", "Oct":"10", "Nov":"11", "Dec":"12"}
            dateStrList[1] = int(months[dateStrList[1]])
            dateStr = str(dateStrList[2]) + " " + str(dateStrList[1]) + " " + str(dateStrList[0])
            RaStr = " ".join(scan_1["Ra"])
            DecStr = " ".join(scan_1["Dec"])
            dopsetPar = dateStr + " " + timeStr + " " + RaStr + " " + DecStr
            print ("dopsetPar", dopsetPar,  " dateStr ", dateStr + " timeStr " + timeStr + " RaStr " + RaStr + " DecStr" + DecStr)
            os.system("code/dopsetpy_v1.5 " + dopsetPar)
            
            # dopsetpy parametru nolasisana
            with open('lsrShift.dat') as openfileobject:
                for line in openfileobject:
                    Header = line.split(';')
                    vards = Header[0]
                    if vards == "Date":
                        dateStr = Header[1]
                    elif vards == "Time":
                        laiks = Header[1]
                    elif vards == "RA":
                        RaStr = Header[1]
                    elif vards == "DEC":
                        DecStr = Header[1]
                    elif vards == "Source":
                        Source = Header[1]
                    elif vards == "LSRshift":
                        lsrShift = Header[1]
                    elif vards == "MJD":
                        mjd = Header[1]
                        print ("MJD: \t", mjd)
                    elif vards == "Vobs":
                        Vobs = Header[1]
                        print ("Vobs: \t", Vobs)
                    elif vards == "AtFreq":
                        AtFreq = Header[1]
                        print ("At Freq: \t", AtFreq)
                    elif vards == "FreqShift":
                        FreqShift = Header[1]
                        print ("FreqShift: \t", FreqShift)
                    elif vards == "VelTotal":
                        VelTotal = float(Header[1])
                        print ("VelTotal: \t", VelTotal)
                    #Header +=1
                    
            Vobs = float(Vobs)
            lsrCorr = float(lsrShift)*1.e6 # for MHz 
            
            self.max_yu1_index =  self.totalResults_u1[p].argmax(axis=0)
            self.max_yu9_index =  self.totalResults_u9[p].argmax(axis=0)
            
            self.freq_0_u1_index = ((np.abs(self.base_frequencies_list - (self.x[self.max_yu1_index] + FreqStart) * (10 ** 6) ).argmin()))
            self.freq_0_u9_index = ((np.abs(self.base_frequencies_list - (self.x[self.max_yu9_index] + FreqStart) * (10 ** 6) ).argmin()))
            
            self.freq_0_u1 = self.base_frequencies_list[self.freq_0_u1_index]
            self.freq_0_u9 = self.base_frequencies_list[self.freq_0_u9_index]
            
            print ("base freqcvencie", self.freq_0_u1, self.freq_0_u9)
            
            for key, value in self.base_frequencies.items():
                if float(value) == self.freq_0_u1:
                    specie = key
                    
            print ("specie", specie)
                    
            velocitys = dopler((self.x + FreqStart) * (10 ** 6), VelTotal, self.freq_0_u1)
            y_u1_avg =  y_u1_avg + self.totalResults_u1[p]
            y_u9_avg =  y_u9_avg + self.totalResults_u9[p]
            velocitys_avg = velocitys_avg + velocitys
        
        velocitys_avg =  velocitys_avg/len(self.totalResults_u1)
        y_u1_avg = y_u1_avg/len(self.totalResults_u1)
        y_u9_avg = y_u9_avg/len(self.totalResults_u9)
             
        self.plot_velocity_u1 = Plot()
        self.plot_velocity_u1.creatPlot(self.grid, 'Velocity (km sec$^{-1}$)', 'Flux density (Jy)', "u1 Polarization", (1,0))
        self.plot_velocity_u1.plot(velocitys_avg, y_u1_avg, 'b')
        #self.plot_velocity_u1.plot(x, y, 'r')
        
        self.plot_velocity_u9 = Plot()
        self.plot_velocity_u9.creatPlot(self.grid, 'Velocity (km sec$^{-1}$)', 'Flux density (Jy)', "u9 Polarization", (1,1))
        self.plot_velocity_u9.plot(velocitys_avg, y_u9_avg, 'b')
        
        #self.plot_velocity_uAVG = Plot()
        #self.plot_velocity_uAVG.creatPlot(None, 'Velocity (km sec$^{-1}$)', 'Flux density (Jy)', "u9 Polarization")
        #self.plot_velocity_uAVG.plot(velocitys_avg, (y_u9_avg +  y_u1_avg )/2 , 'b')
        
        ston_x = np.arange(0, len(self.STON_list_u1))
        self.plot_STON = Plot()
        self.plot_STON.creatPlot(self.grid, 'Pair', 'Ratio', "Signal to Noise", (3,0))
        self.plot_STON.plot(ston_x, self.STON_list_u1, '*r', label="u1 Polarization")
        self.plot_STON.plot(ston_x, self.STON_list_u9, 'og', label="u9 Polarization")
        self.plot_STON.plot(ston_x, self.STON_list_AVG, 'vb', label="AVG Polarization")
        
        self.grid.addWidget(self.plot_velocity_u1, 0, 0)
        self.grid.addWidget(self.plot_velocity_u9, 0, 1)
        
        self.grid.addWidget(self.plot_STON, 2, 0)
        
        totalResults = np.concatenate((velocitys_avg, y_u1_avg, y_u9_avg), axis=1)
        output_file_name = self.dataFilesPath + self.source + "_" +self.date.replace(" ", "_") + "_" + self.firstScanStartTime + "_" + self.logs["header"]["location"] + "_" + str(self.iteration_number) + ".dat"
        output_file_name = output_file_name.replace(" ", "")
        #np.savetxt(output_file_name, totalResults)
        
        result = Result(totalResults, specie)
        pickle.dump(result, open(output_file_name, 'wb'))
                
    def __UI__(self):
        
        if self.index != self.datPairsCount -1: # cheking if there is not one pair
            self.nextPairButton = QPushButton("Next pair", self)
            self.nextPairButton.clicked.connect(self.nextPair)
            self.grid.addWidget(self.nextPairButton, 5, 3)
        
        self.skipAllButton = QPushButton("Skip all", self)
        self.skipAllButton.clicked.connect(self.skipAll)
        self.grid.addWidget(self.skipAllButton, 6, 3)   
        self.plotingPairs(self.index)

    def _on_press_u1(self, event, xdata, ydata_1_u1, ydata_2_u1):
        if event.button == 3:
            # click x-value
            xdata_click = event.xdata
            # index of nearest x-value in a
            xdata_nearest_index_a = (np.abs(xdata - xdata_click)).argmin()
            # new scatter point x-value
            new_xdata_point_b = xdata[xdata_nearest_index_a]
            # new scatter point [x-value, y-value]
            #new_xydata_point_b = xydata_a[new_xdata_point_b, :]
            if new_xdata_point_b in xdata:
                print(new_xdata_point_b)
                print(xdata.tolist().index(new_xdata_point_b))
                index = xdata.tolist().index(new_xdata_point_b)
                np.delete()
                event.canvas.draw()

    def _on_left_click(self, event, xdata, ydata):
        line = event.artist                            #Replace not remove points with polynom np.polyfit()
        pointx, pointy = line.get_data()                 #Save old points in array
        ind = event.ind
        if (xdata[ind].size > 1):
            print("Too many points selected")
        else:
            print("Selected point x -",pointx[ind][0]," y -",pointy[ind][0])
            y1_list = ydata.tolist()
            index = y1_list.index(pointy[ind].tolist())
            print("Index ",index)
            pf = np.polyfit(xdata[:,0], ydata[:,0], 20)
            p = np.poly1d(pf)
            print("Poly value ", p(xdata[index]))
            ydata[index][0]=p(xdata[index])
            event.artist.set_ydata(ydata[:,0])
            event.canvas.draw()
            event.canvas.flush_events()

    def _on_right_click(self, event, xdata, ydata):
        if event.mouseevent.button == 3:
            line = event.artist  # Replace not remove points with polynom np.polyfit()
            pointx, pointy = line.get_data()  # Save old points in array
            ind = event.ind
            if (xdata[ind].size > 1):
                print("Too many points selected")
            else:
                print("Selected point x -", pointx[ind][0], " y -", pointy[ind][0])
                y1_list = ydata.tolist()
                index = y1_list.index(pointy[ind].tolist())
                print("Index ", index)
                pf = np.polyfit(xdata[:, 0], ydata[:, 0], 20)
                p = np.poly1d(pf)
                print("Poly value ", p(xdata[index]))
                ydata[index][0] = p(xdata[index])
                event.artist.set_ydata(ydata[:, 0])
                event.canvas.draw()
                event.canvas.flush_events()

def main():
    args = parseArguments()
    source = str(args.__dict__["source"])
    iteration_number = int(args.__dict__["iteration_number"])
    logFile = str(args.__dict__["logFile"])
    threshold = float(args.__dict__["threshold"])
    filter = int(args.__dict__["filter"])
    configFilePath = str(args.__dict__["config"])
                
    config = configparser.RawConfigParser()
    config.read(configFilePath)
    dataFilesPath =  config.get('paths', "dataFilePath")
    prettyLogsPath =  config.get('paths', "prettyLogsPath")
    logPath = config.get('paths', "logPath")
    resultPath = config.get('paths', "resultFilePath")
    badPointRange =  config.getint('parameters', "badPointRange")
    coordinates = config.get('sources', source).replace(" ", "").split(",")
    cuts = config.get('cuts', source).split(";")
    cuts = [c.split(",") for c in  cuts]
    base_frequencies = dict(config.items('base_frequencies'))
    
    if args.manual:
        with open(prettyLogsPath + source + "_" + str(iteration_number) + "log.dat") as data_file:    
                logs  = json.load(data_file)
        f = list()
        
        for scan in logs:
            f.append(logs[scan]["fs_frequencyfs"])
        
    else:
        logs  = ExperimentLogReader(logPath + logFile, prettyLogsPath, coordinates, source).getLogs()
        f = ExperimentLogReader(logPath + logFile, prettyLogsPath, coordinates, source).getAllfs_frequencys()
        firstScanStartTime = ExperimentLogReader(logPath + logFile, prettyLogsPath, coordinates, source).getFirstScanStartTime()
        
    f = [float(fi) for fi in f]
    f = list(set(f))
    f.sort()
    f1 =  f[-1]
    f2 = f[-2]
    fstart = (f1 + f2)/ 2.0
    
    location = logs["header"]["location"]
    
    if location == "IRBENE":
        DPFU_max =  config.get('parameters', "DPFU_max").split(",")
        G_El =  config.get('parameters', "G_El").split(",")
        Tcal =  config.getfloat('parameters', "Tcal")
        k =  config.getfloat('parameters', "k")
    
    elif location == "IRBENE16":
        DPFU_max =  config.get('parameters', "DPFU_max_16").split(",")
        G_El =  config.get('parameters', "G_El_16").split(",")
        Tcal =  config.getfloat('parameters', "Tcal_16")
        k =  config.getfloat('parameters', "k_16")
    
    DPFU_max = [float(i) for i in DPFU_max]
    G_El = [float(i) for i in G_El]

    
    if threshold <= 0.0:
        raise Exception("Threshold cannot be negative or zero")   
    
    #Create App
    qApp = QApplication(sys.argv)

    aw = Analyzer(source, iteration_number, filter, threshold, badPointRange, dataFilesPath, resultPath, logs, DPFU_max, G_El, Tcal, k, fstart, cuts, firstScanStartTime, base_frequencies)
    aw.show()
    sys.exit(qApp.exec_())
    
    sys.exit(0)

if __name__=="__main__":
    main()
    
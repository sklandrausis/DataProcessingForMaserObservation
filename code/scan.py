import Tkinter
import tkSimpleDialog
from decimal import Decimal

class Scan():
    def __init__(self, logLines):
        self.logLine = logLines
        
        #Parametrs
        self.source = "None"
        self.sourceName = "None"
        self.Epochs = 0
        self.timeStart = "None"
        self.timeStop = "None"
        self.freqBBC1 = 0
        self.freqBBC2 = 0
        self.loa = 0
        self.loc = 0
        self.clock = 0
        
        self.ra = list()
        self.dec = list()
        self.SystemtemperaturesForScan = [0]*2
            
    def getParametrs(self):
        for line in self.logLine:
            if "source="  in line:
                  
                if line.endswith(",\n"):
                    logLineSplit = line[:-2].split(",")
                else:
                    logLineSplit = line[:-1].split(",")
                    
                self.source = logLineSplit[0].split("=")[1]+","+logLineSplit[-3]+","+logLineSplit[-2]
                self.sourceName = logLineSplit[0].split("=")[1]
                self.Epoch = logLineSplit[-1]
                    
                self.RA = self.source.split(",")[1]
                self.DEC = self.source.split(",")[2]
                 
                self.ra.append(self.RA[0:2])
                self.ra.append(self.RA[2:4])
                self.ra.append(self.RA[4:len(self.RA)])
                    
                if self.DEC[0] == "-":
                    self.dec.append(self.DEC[0:3])
                    self.dec.append(self.DEC[3:5])
                    self.dec.append(self.DEC[5:len(self.DEC)])
                else:    
                    self.dec.append(self.DEC[0:2])
                    self.dec.append(self.DEC[2:4])
                    self.dec.append(self.DEC[4:len(self.DEC)])
            
            elif "disk_record=on" in line:
                self.timeStart =  line.split(".")[2]
                 
            elif "disk_record=of" in line:
                self.timeStop =  line.split(".")[2]
                
            elif "/tsys/1u" in line:
                    t  = line.split("/")[2].split(",")[1]
                    try:
                        float(t)
                    except:
                        root = Tkinter.Tk()
                        root.withdraw()
                        newT = tkSimpleDialog.askfloat("System temperature error", "Got " + t + " Expected number between 0 and 300", minvalue = 0, maxvalue = 300)
                        t = newT
                        root.destroy()
                        if t == "" or t == None:
                            t = 0
                        
                    if float(t) < 0 or float(t) > 300:
                        root = Tkinter.Tk()
                        root.withdraw()
                        newT = tkSimpleDialog.askfloat("System temperature error", "Got " + t + " Expected number between 0 and 300", minvalue = 0, maxvalue = 300)
                        t = newT
                        root.destroy()
                        if t == "" or t == None:
                            t = 0
                            
                    self.SystemtemperaturesForScan[0] = t
                    
            elif "/tsys/9u" in line:
                    t  = line.split("/")[2].split(",")[1]
                    try:
                        float(t)
                    except:
                        root = Tkinter.Tk()
                        root.withdraw()
                        newT = tkSimpleDialog.askfloat("System temperature error", "Got " + t + " Expected number", minvalue = 0, maxvalue = 300)
                        t = newT
                        root.destroy()
                        if t == "" or t == None:
                            t = 0
                            
                    if float(t) < 0 or float(t) > 300:
                        root = Tkinter.Tk()
                        root.withdraw()
                        newT = tkSimpleDialog.askfloat("System temperature error", "Got " + t + "Expected number", minvalue = 0, maxvalue = 300)
                        t = newT
                        root.destroy()
                        if t == "" or t == None:
                            t = 0
                            
                    self.SystemtemperaturesForScan[1] = t
                    
            elif "/bbc01=" in line:
                self.freqBBC1 =  line.split("=")[1].split(",")[0]
                
                try:
                    float(self.freqBBC1)
                except:
                    root = Tkinter.Tk()
                    root.withdraw()
                    newfreqBBC1 = tkSimpleDialog.askfloat("BBC error", "Got " + self.freqBBC1 + " Expected number", minvalue = 0)
                    self.freqBBC1 = newfreqBBC1
                    root.destroy()
                    if self.freqBBC1 == "" or self.freqBBC1 == None:
                        self.freqBBC1 = 0
                            
                if float(self.freqBBC1) < 0:
                    root = Tkinter.Tk()
                    root.withdraw()
                    newfreqBBC1 = tkSimpleDialog.askfloat("BBC error", "Got " + self.freqBBC1 + "Expected number", minvalue = 0)
                    self.freqBBC1 = newfreqBBC1
                    root.destroy()
                    if self.freqBBC1 == "" or self.freqBBC1 == None:
                        self.freqBBC1 = 0
                
            elif "/bbc02=" in line:     
                self.freqBBC2 =  line.split("=")[1].split(",")[0]
                
                try:
                    float(self.freqBBC2)
                except:
                    root = Tkinter.Tk()
                    root.withdraw()
                    newfreqBBC2 = tkSimpleDialog.askfloat("BBC error", "Got " + self.freqBBC2 + " Expected number", minvalue = 0)
                    self.freqBBC2 = newfreqBBC2
                    root.destroy()
                    if self.freqBBC2 == "" or self.freqBBC2 == None:
                        self.freqBBC2 = 0
                            
                if float(self.freqBBC2) < 0:
                    root = Tkinter.Tk()
                    root.withdraw()
                    newfreqBBC2 = tkSimpleDialog.askfloat("BBC error", "Got " + self.freqBBC2 + "Expected number", minvalue = 0)
                    self.freqBBC2 = newfreqBBC2
                    root.destroy()
                    if self.freqBBC2 == "" or self.freqBBC2 == None:
                        self.freqBBC2 = 0
            
            elif "/bbc01/ " in line:
                if self.freqBBC1 == 0:
                    self.freqBBC1 = line.split("/")[2].split(",")[0]
                    
                    try:
                        float(self.freqBBC1)
                    except:
                        root = Tkinter.Tk()
                        root.withdraw()
                        newfreqBBC1 = tkSimpleDialog.askfloat("System temperature error", "Got " + self.freqBBC1 + " Expected number", minvalue = 0)
                        self.freqBBC1 = newfreqBBC1
                        root.destroy()
                        if self.freqBBC1 == "" or self.freqBBC1 == None:
                            self.freqBBC1 = 0
                                
                    if float(self.freqBBC1) < 0:
                        root = Tkinter.Tk()
                        root.withdraw()
                        newfreqBBC1 = tkSimpleDialog.askfloat("System temperature error", "Got " + self.freqBBC1 + "Expected number", minvalue = 0)
                        self.freqBBC1 = newfreqBBC1
                        root.destroy()
                        if self.freqBBC1 == "" or self.freqBBC1 == None:
                            self.freqBBC1 = 0
                
            elif "/bbc02/ " in line:
                if self.freqBBC2 == 0:
                    self.freqBBC2 = line.split("/")[2].split(",")[0]
                    
                    try:
                        float(self.freqBBC2)
                    except:
                        root = Tkinter.Tk()
                        root.withdraw()
                        newfreqBBC2 = tkSimpleDialog.askfloat("System temperature error", "Got " + self.freqBBC2 + " Expected number", minvalue = 0)
                        self.freqBBC2 = newfreqBBC2
                        root.destroy()
                        if self.freqBBC2 == "" or self.freqBBC2 == None:
                            self.freqBBC2 = 0
                                
                    if float(self.freqBBC2) < 0:
                        root = Tkinter.Tk()
                        root.withdraw()
                        newfreqBBC2 = tkSimpleDialog.askfloat("System temperature error", "Got " + self.freqBBC2 + "Expected number", minvalue = 0)
                        self.freqBBC2 = newfreqBBC2
                        root.destroy()
                        if self.freqBBC2 == "" or self.freqBBC2 == None:
                            self.freqBBC2 = 0
                          
            elif "lo=loa" in line:
                self.loa =  line.split("=")[1].split(",")[1]
            
            elif "lo=loc" in line:
                self.loc =  line.split("=")[1].split(",")[1]
            
            elif "/gps-fmout/" in line:  
                self.clock = Decimal(line.split("/")[2])
                              
    def returnParametrs(self):
        return (self.source, self.sourceName, self.Epoch, self.ra, self.dec, self.timeStart, self.timeStop, self.SystemtemperaturesForScan, self.freqBBC1, self.freqBBC2, self.loa, self.loc, self.clock)
    
    
#
# version 1.0 -- 2019-05-17 -- JLC -- new file
#

import numpy as np
from numpy import * # necessary for eval(user expression)

from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QRadioButton, QButtonGroup, QLabel, QLineEdit,
                             QFileDialog)
from PyQt5.QtGui import QIcon

from matplotlib.backends.backend_qt5agg import  \
    FigureCanvasQTAgg as FigureCanvas,          \
    NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt


class FunctionPlot(QWidget):
    '''Plotting of Z(t) = f(X(t),Y(t), where X(t) and Y(t) are the coordinates
       of the target, and Z(t) is a Python expression given by the user.
       For example : Z(t) = np.atan2(Y(), X(t), to compute the angle of the 
       polar coordinates of the target.
    '''

    def __init__(self, mainWindow):

        # call the constructor of the base class:
        super().__init__(mainWindow)

        self.mw = mainWindow # remember the reference on thje main window

        # Attributes (persistent data in the object)
        self.__figure     = None  # the plotting figure
        self.__axe1       = None  # plot Z1 Axes
        self.__axe2       = None  # plot Z2 Axes (twinx)
        self.__canvas     = None  # used by matplotlib to plot data
        self.__toolbar    = None  # the tool bar below the plot
        self.__time       = None  # abcissa values for plot
        self.__xlim       = None  # plot xmin and xmax
        self.__z1lim      = None  # plot ymin and ymax
        self.__z2lim      = None  # plot ymin and ymax
        self.__XYLabel1   = ["",""] # X and Y plot labels
        self.__XYLabel2   = ["",""] # X and Y plot labels
        self.__Z1         = None  # data to plot: Z1(t) = f(X(t),Y(t),t)
        self.__Z1         = None  # data to plot: Z2(t) = f(X(t),Y(t),t)

        self.__labelZ1Edit  = QLabel("Z1 : Python expr. to plot", self)
        self.__lineZ1Edit   = QLineEdit("2*Y-X",self)
        self.__labelZ1label = QLabel("Z1 axis label:", self)
        self.__lineZ1label  = QLineEdit("Z1 [unit]",self)
        
        self.__labelZ2Edit  = QLabel("Z2 : Python expr. to plot", self)
        self.__lineZ2Edit   = QLineEdit("cos(2*pi*12*T)",self)
        self.__labelZ2label = QLabel("Z2 axis label:", self)
        self.__lineZ2label  = QLineEdit("Z2 [unit]",self)
        
        self.__btnPlot1  = QPushButton("Plot Z1(t)",self)
        self.__btnPlot2  = QPushButton("Plot Z2(t)",self)
        self.__btnClear1 = QPushButton("Clear Plot",self)
        self.__btnClear2 = QPushButton("Clear Plot",self)
        self.__btnClear  = QPushButton("Clear All",self)
        self.__btnCSV    = QPushButton(QIcon("icones/csv.png"),"Export CSV",
                                      self)
        self.__initUI()   # GUI initialization


    def __initUI(self):
        self.__figure, self.__axe1   = plt.subplots()
        self.__axe2 = self.__axe1.twinx()
        self.__figure.subplots_adjust(left=0.1,right=0.9,bottom=0.14,top=0.92)
        self.__canvas  = FigureCanvas(self.__figure)
        self.__toolbar = NavigationToolbar(self.__canvas, self)

        self.__btnPlot1.clicked.connect(self.PlotZ1)
        self.__btnPlot2.clicked.connect(self.PlotZ2)
        self.__btnClear1.clicked.connect(self.ClearAxe1)
        self.__btnClear2.clicked.connect(self.ClearAxe2)
        self.__btnClear.clicked.connect(self.ClearAxes)
        self.__btnCSV.clicked.connect(self.ExportCSV)
        self.__btnCSV.setEnabled(False)

        mess = 'Type a Python expression using vector X ' + \
               'and/or vector Y and/or vector T (dicrete time values)'
        self.__lineZ1Edit.setToolTip(mess)
        self.__lineZ2Edit.setToolTip(mess)

        self.__lineZ1Edit.setFixedWidth(200)
        self.__lineZ2Edit.setFixedWidth(200)
        
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        # Ligne 1 : tracé de l'image
        self.setLayout(vbox)

        hbox = QHBoxLayout()
        hbox.addWidget(self.__labelZ1Edit)
        hbox.addWidget(self.__lineZ1Edit)
        hbox.addWidget(self.__labelZ1label)
        hbox.addWidget(self.__lineZ1label)
        hbox.addStretch()
        hbox.addWidget(self.__btnClear1)
        hbox.addWidget(self.__btnPlot1)
        
        vbox.addLayout(hbox)

        hbox = QHBoxLayout()
        hbox.addWidget(self.__labelZ2Edit)
        hbox.addWidget(self.__lineZ2Edit)
        hbox.addWidget(self.__labelZ2label)
        hbox.addWidget(self.__lineZ2label)
        hbox.addStretch()
        hbox.addWidget(self.__btnClear2)
        hbox.addWidget(self.__btnPlot2)

        vbox.addLayout(hbox)
        
        vbox.addWidget(self.__canvas)

        hbox = QHBoxLayout()
        
        hbox.addWidget(self.__toolbar)
        hbox.addStretch()
        hbox.addWidget(self.__btnClear)
        hbox.addWidget(self.__btnCSV)

        vbox.addLayout(hbox)

    def __AutoSizePlotXZ1Lim(self):

        if self.mw.target_pos is None: return

        X, Z = self.__time, self.__Z1
        deltaZ = Z.max() - Z.min()
        self.__xlim  = np.array([X.min(), X.max()])
        self.__z1lim = np.array([Z.min()-0.1*deltaZ, Z.max()+0.1*deltaZ])

        self.__axe1.set_xlim(*self.__xlim)
        self.__axe1.set_ylim(*self.__z1lim)
        self.__axe1.set_xlabel(self.__XYLabel1[0])
        self.__axe1.set_ylabel(self.__XYLabel1[1])
        self.__axe1.set_aspect("auto")
        self.__canvas.draw()

    def __AutoSizePlotXZ2Lim(self):

        if self.mw.target_pos is None: return

        X, Z = self.__time, self.__Z2
        deltaZ = Z.max() - Z.min()
        self.__xlim  = np.array([X.min(), X.max()])

        if self.__Z1 is None:
            self.__z2lim = np.array([Z.min()-0.1*deltaZ, Z.max()+0.1*deltaZ])
        else:
            self.__z2lim = self.__z1lim

        self.__axe2.set_xlim(*self.__xlim)
        self.__axe2.set_ylim(*self.__z2lim)
        self.__axe2.set_xlabel(self.__XYLabel2[0])
        self.__axe2.set_ylabel(self.__XYLabel2[1])
        self.__axe2.set_aspect("auto")
        self.__canvas.draw()

    def ClearAxe1(self):
        self.__axe1.clear()
        self.__canvas.draw()
        self.__Z1 = None

    def ClearAxe2(self):
        self.__axe2.clear()
        self.__canvas.draw()
        self.__Z2 = None

    def ClearAxes(self):
        self.__axe1.clear()
        self.__axe2.clear()
        self.__canvas.draw()
        self.__btnCSV.setEnabled(False)

    def __buildTimeVector(self, target_pos):
        # Récupération de la valeur de FP (Frame per seconde) pour calcul
        # du pas de temps et des abscisses :
        X = target_pos[0]
        if self.mw.imageTab.video_FPS is not None:
            deltaT = 1./self.mw.imageTab.video_FPS
            self.__time = np.arange(len(X))*deltaT
            self.__XYLabel1[0] = "temps [s]"
            self.__XYLabel2[0] = "temps [s]"
        else:
            self.__time = np.arange(len(X))+1
            self.__XYLabel1[0] = "image #"
            self.__XYLabel2[0] = "image #"


    def PlotZ1(self):

        target_pos = self.mw.target_pos
        if target_pos is None: return

        self.__buildTimeVector(target_pos)

        X, Y, T = target_pos[0], target_pos[1], self.__time
        expr = self.__lineZ1Edit.text()
        try:
            self.__Z1 = eval(expr)
        except:
            print("cannot plot this expression <{}>".format(expr))
            return
            
        self.__XYLabel1[1] = self.__lineZ1label.text()
        self.__AutoSizePlotXZ1Lim()
        
        # tracé de courbe X(t)
        self.__axe1.plot(self.__time, self.__Z1,
                         color = self.mw.target_RGB/255,
                         marker = 'o',
                         markersize = 3,
                         label="Z1(t)="+expr)
        self.__axe1.grid(True)
        self.__axe1.legend(loc='best',fontsize=10)
        self.__canvas.draw()

        self.__btnCSV.setEnabled(True)

    def PlotZ2(self):

        target_pos = self.mw.target_pos
        if target_pos is None: return
                
        self.__buildTimeVector(target_pos)

        X, Y, T = target_pos[0], target_pos[1], self.__time
        expr = self.__lineZ2Edit.text()
        try:
            self.__Z2 = eval(expr)
        except:
            print("cannot plot this expression <{}>".format(expr))
            return
                        
        self.__XYLabel2[1] = self.__lineZ2label.text()
        self.__AutoSizePlotXZ2Lim()
        
        # tracé de courbe X(t)
        self.__axe2.plot(self.__time, self.__Z2,
                         color = 'm',
                         marker = 'o',
                         markersize = 3,
                         label="Z2(t)="+expr)
        self.__axe2.grid(True)
        self.__axe2.legend(loc='best',fontsize=10)
        self.__canvas.draw()

        self.__btnCSV.setEnabled(True)

    def ExportCSV(self):
        '''Export Data in a CSV file.'''
        if self.__Z1 is None :
            self.mw.statusBar().showMessage("No data to export")
            return

        # Lance un sélecteur de fichier pour choisir le fichier à écrire.'''
        fname = QFileDialog.getSaveFileName(self,
                                            'Choose a name for the CSV file to write',
                                            self.mw.cur_dir,
                                            'CSV file (*.csv *.txt)')
        if fname[0] == "": return 

        nbData = len(self.__time)
        if self.mw.imageTab.video_FPS is not None:
            deltaT = 1./self.mw.imageTab.video_FPS
            time = np.arange(nbData)*deltaT
            tlabel, tformat  = "T [seconde]", "%10.6e"
        else:
            time = range(1, nbImages+1)
            tlabel, tformat = "image #", "%10d"

        # building headers:
        zlabel =  self.__lineZlabel.text()
        zformat = "%10.6e"
            
        header = "{};{}".format(tlabel, zlabel)
        fmt = (tformat, zformat)
        data = []
        data.append(time)
        data.append(self.__Z1.tolist())
        data = np.array(data)

        fileName = fname[0]
        if not fileName.endswith(".csv"): fileName += ".csv"
        np.savetxt(fileName, data.transpose(), delimiter=";",
                   header=header, fmt=fmt)

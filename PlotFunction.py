#
# version 1.0 -- 2019-05-17 -- JLC -- new file
#

import numpy as np
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                             QRadioButton, QButtonGroup, QLabel, QLineEdit,
                             QFileDialog)
from PyQt5.QtGui import QIcon

from matplotlib.backends.backend_qt5agg import  \
    FigureCanvasQTAgg as FigureCanvas,          \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


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
        self.__axes       = None  # plot Axes
        self.__canvas     = None  # used by matplotlib to plot data
        self.__toolbar    = None  # the tool bar below the plot
        self.__time       = None  # abcissa values for plot
        self.__xlim       = None  # plot xmin and xmax
        self.__zlim       = None  # plot ymin and ymax
        self.__XZLabel  = ["",""] # X and Y plot labels
        self.__Z          = None  # data to plot: Z(t) = f(X(t),Y(t))

        self.__labelEdit   = QLabel("Python expression to plot:", self)
        self.__lineEdit    = QLineEdit("np.rad2deg(np.arctan2(Y,X))",self)
        self.__labelZlabel = QLabel("Z axis label:", self)
        self.__lineZlabel  = QLineEdit("Z [unit]",self)
        
        self.__btnPlot     = QPushButton("Plot Z(t)",self)
        self.__btnCSV      = QPushButton(QIcon("icones/csv.png"),"Export CSV",
                                       self)
        
        self.__initUI()   # GUI initialization


    def __initUI(self):
        self.__figure = Figure()
        self.__axes   = self.__figure.add_subplot(111)
        self.__figure.subplots_adjust(left=0.1,right=0.98,bottom=0.1,top=0.95)
        self.__canvas  = FigureCanvas(self.__figure)
        self.__toolbar = NavigationToolbar(self.__canvas, self)

        self.__btnPlot.clicked.connect(self.Plot)
        self.__btnCSV.clicked.connect(self.ExportCSV)
        self.__btnCSV.setEnabled(False)

        vbox = QVBoxLayout()
        self.setLayout(vbox)

        # Ligne 1 : tracé de l'image
        self.setLayout(vbox)

        hbox = QHBoxLayout()
        hbox.addWidget(self.__labelEdit)
        hbox.addWidget(self.__lineEdit)
        hbox.addStretch()
        hbox.addWidget(self.__labelZlabel)
        hbox.addWidget(self.__lineZlabel)
        
        vbox.addLayout(hbox)
        
        vbox.addWidget(self.__canvas)

        hbox = QHBoxLayout()
        
        hbox.addWidget(self.__toolbar)
        hbox.addStretch()
        hbox.addWidget(self.__btnPlot)
        hbox.addWidget(self.__btnCSV)

        vbox.addLayout(hbox)

    def __AutoSizePlotXZLim(self):

        if self.mw.target_pos is None: return

        X = self.__time
        Z = self.__Z
        deltaZ = Z.max() - Z.min()
        self.__xlim = np.array([X.min(), X.max()])
        self.__zlim = np.array([Z.min()-0.1*deltaZ, Z.max()+0.1*deltaZ])

        self.__axes.set_xlim(*self.__xlim)
        self.__axes.set_ylim(*self.__zlim)
        self.__axes.set_xlabel(self.__XZLabel[0])
        self.__axes.set_ylabel(self.__XZLabel[1])
        self.__axes.set_aspect("auto")
        self.__canvas.draw()

    def ClearAxes(self):
        self.__axes.clear()
        self.__canvas.draw()
        self.__btnCSV.setEnabled(False)

    def Plot(self):

        target_pos = self.mw.target_pos
        if target_pos is None: return
        
        X, Y = target_pos[0], target_pos[1]
        self.__Z = eval(self.__lineEdit.text())
        
        # Effacement automatiqe si demandé à chaque nouveau tracé :
        if self.mw.flags["autoClearTraj"]:
            self.__axes.clear()

        # Récupération de la valeur de FP (Frame per seconde) pour calcul
        # du pas de temps et des abscisses :
        if self.mw.imageTab.video_FPS is not None:
            deltaT = 1./self.mw.imageTab.video_FPS
            self.__time = np.arange(len(X))*deltaT
            self.__XZLabel[0] = "temps [s]"
        else:
            self.__time = np.arange(len(X))+1
            self.__XZLabel[0] = "image #"
            
        self.__XZLabel[1] = self.__lineZlabel.text()
        self.__AutoSizePlotXZLim()
        
        # tracé de courbe X(t)
        self.__axes.plot(self.__time, self.__Z,
                         color = self.mw.target_RGB/255,
                         marker = 'o',
                         markersize = 3,
                         label="Z(t)="+self.__lineEdit.text())
        self.__axes.grid(True)
        self.__axes.legend(loc='best',fontsize=10)
        self.__canvas.draw()

        self.__btnCSV.setEnabled(True)

    def ExportCSV(self):
        '''Export Data in a CSV file.'''
        if self.__Z is None :
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
        data.append(self.__Z.tolist())
        data = np.array(data)

        fileName = fname[0]
        if not fileName.endswith(".csv"): fileName += ".csv"
        np.savetxt(fileName, data.transpose(), delimiter=";",
                   header=header, fmt=fmt)

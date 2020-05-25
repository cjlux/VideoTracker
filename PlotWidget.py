#
# version 1.3 -- 2019-05-07 -- JLC --
#   add Export CVS
#
# version 1.4 -- 2019-05-18 -- JLC -- 
#   add PlotFunction tab.
#
# version 1.5 -- 2020-05-22 -- JLC -- 
#   add Velocity tab, with smoothing buttons
#

import numpy as np
from collections import deque
from PyQt5.Qt import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                     QRadioButton, QCheckBox, QButtonGroup, QSpinBox)

from matplotlib.backends.backend_qt5agg import  \
    FigureCanvasQTAgg as FigureCanvas,          \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class OnePlot(QWidget):
    ''' Widget de tracé d'une courbe Y=f(X)'''

    Ylabels = {"position":     ("x [pixel]",    "y [pixel]"),
               "position_mm":  ("x [mm]",       "y [mm]")
              }            
    
    def __init__(self, mainWindow):

        # call the base class constructor:
        QWidget.__init__(self, mainWindow)

        self.mw = mainWindow    # remember he application main windwos

        # Attributes (persistant data)
        self.__figure      = Figure() # the plot figure
        self.__axes        = None     # axis system
        self.__canvas      = None     # area for matplotlib plot
        self.__toolbar     = None     # plot tool bar
        self.__xlim        = None     # xmin, xmay of the plo
        self.__ylim        = None     # ymin, ymax of the plot
        self.__axes_aspect = 'equal'  # 'equal' or 'auto'

        self.btn_imageSize = QRadioButton("ImageSize", self)
        self.btn_autoSize  = QRadioButton("AutoSize", self)
        self.btn_axesEqual = QRadioButton("Equal", self)
        self.btn_axesAuto  = QRadioButton("Auto", self)

        group = QButtonGroup(self) # pour les 2 boutons imageSize, autoSize
        group.addButton(self.btn_imageSize)
        group.addButton(self.btn_autoSize)

        group = QButtonGroup(self)
        group.addButton(self.btn_axesEqual)
        group.addButton(self.btn_axesAuto)

        self.__initUI()   # Initialisation de l'interface utilisateur


    def __initUI(self):
        '''To initialize or configure all the widgets on the screen.'''
        self.__figure.subplots_adjust(left=0.1,right=0.98,bottom=0.1,top=0.95)
        self.__axes    = self.__figure.add_subplot(111)
        self.__canvas  = FigureCanvas(self.__figure)
        self.__toolbar = NavigationToolbar(self.__canvas, self)

        self.btn_axesEqual.toggled.connect(lambda : self.__SetAspect("equal"))
        self.btn_axesEqual.setEnabled(False)
        texte = "Tracé dans des axes orthonormés"
        self.btn_axesEqual.setStatusTip(texte)
        self.btn_axesEqual.setChecked(True)

        self.btn_axesAuto.toggled.connect(lambda : self.__SetAspect("auto"))
        self.btn_axesAuto.setEnabled(False)
        texte = "Tracé dans des axes non orthonormés"
        self.btn_axesAuto.setStatusTip(texte)

        self.btn_imageSize.toggled.connect(self.__ImageSizePlotXYLim)
        self.btn_imageSize.setEnabled(False)
        texte = "Tracé avec les bornes min et max de l'image"
        self.btn_imageSize.setStatusTip(texte)
        self.btn_imageSize.setChecked(True)

        self.btn_autoSize.toggled.connect(self.__AutoSizePlotXYLim)
        self.btn_autoSize.setEnabled(False)
        texte = "Tracé avec les bornes min et max de la "
        texte += "trajectoire calculée"
        self.btn_autoSize.setStatusTip(texte)
        
        vbox = QVBoxLayout()
        self.setLayout(vbox)
        vbox.addWidget(self.__canvas)
        # last raw of the display :
        #  HBox[toolbar <<<strech>>> VBox [ HBOX[Equal Auto]        ] ]
        #                                 [ HBox[ImageSize AutoSize]]
        hbox = QHBoxLayout()
        hbox.addWidget(self.__toolbar)
        
        vb = QVBoxLayout()
        hbox.addStretch()
        hbox.addLayout(vb)

        hb = QHBoxLayout()
        hb.addWidget(self.btn_axesEqual)
        hb.addWidget(self.btn_axesAuto)
        vb.addLayout(hb)
        hb = QHBoxLayout()
        hb.addWidget(self.btn_imageSize)
        hb.addWidget(self.btn_autoSize)
        vb.addLayout(hb)

        vbox.addLayout(hbox)

    def __SetAspect(self, aspect):
        self.__axes_aspect = aspect
        self.__axes.set_aspect(aspect)
        self.__canvas.draw()

    def __AutoSizePlotXYLim(self):

        if self.mw.target_pos is None: return

        xlabel, ylabel =  "X [pixels]", "Y [pixels]"
        X, Y = self.mw.target_pos[0], self.mw.target_pos[1]
        self.__xlim = np.array([np.nanmin(X), np.nanmax(X)])
        self.__ylim = np.array([np.nanmin(Y), np.nanmax(Y)])

        if self.mw.imageTab.valid_scale:
            xlabel = "X [mm]"
            ylabel = "Y [mm]"

        offset = (self.__ylim[1]-self.__ylim[0])/10
        self.__ylim += np.array([-offset, offset])

        self.__axes.set_xlim(*self.__xlim)
        self.__axes.set_ylim(*self.__ylim)
        self.__axes.set_xlabel(xlabel)
        self.__axes.set_ylabel(ylabel)

        self.__axes.set_aspect(self.__axes_aspect)
        self.__canvas.draw()


    def __ImageSizePlotXYLim(self):

        if self.mw.imageTab.video_size is None: return
        
        xlabel, ylabel =  "X [pixels]", "Y [pixels]"
        w, h = self.mw.imageTab.video_size
        self.__xlim = np.array([0, w-1], dtype=float)
        self.__ylim = np.array([0, h-1], dtype=float)

        if self.mw.imageTab.valid_scale:
            self.__xlim *= self.mw.imageTab.pix_to_mm_coeff
            self.__ylim *= self.mw.imageTab.pix_to_mm_coeff
            xlabel, ylabel = "X [mm]", "Y [mm]"

        self.__axes.set_xlim(*self.__xlim)
        self.__axes.set_ylim(*self.__ylim)
        self.__axes.set_xlabel(xlabel)
        self.__axes.set_ylabel(ylabel)

        self.__axes.set_aspect(self.__axes_aspect)
        self.__canvas.draw()

    def ClearAxes(self):
        self.__axes.clear()
        self.__canvas.draw()

    def Plot(self):

        target_pos = self.mw.target_pos
        X, Y, I = target_pos

        self.btn_imageSize.setEnabled(True)
        self.btn_autoSize.setEnabled(True)
        self.btn_axesEqual.setEnabled(True)
        self.btn_axesAuto.setEnabled(True)

        # Effacement automatique si demandé à chaque nouveau tracé :
        if self.mw.flags["autoClearTraj"]: self.__axes.clear()

        # Récupération du nom de l'alagorithme de traitement :
        algo = self.mw.imageTab.btn_algo.currentText()

        # AutoSize an EqualSize plot
        self.__ImageSizePlotXYLim()
        self.__SetAspect("equal")

        # tracé de courbe paramétrée (x(t),y(t)) :
        color = 'b' if self.mw.target_RGB is None else self.mw.target_RGB/255
        self.__axes.plot(X,Y,
                         color = color,
                         marker = 'o', markersize = 2, linewidth = .4,
                         label="Trajectoire XY / algo : {}".format(algo))
        self.__axes.grid(True)
        self.__axes.legend(loc='best',fontsize=10)
        self.__axes.set_aspect(self.__axes_aspect)
        self.__canvas.draw()


class TwoPlots(QWidget):
    ''' Widget to plot 2 curves x(t) & y(t), or Vx(t) & Vy(t)'''

    Ylabels = {"position":     ("X [pixel]",    "Y [pixel]"),
               "velocity":     ("VX [pixel/s]", "VY [pixel/s]"),
               "position_mm":  ("X [mm]",       "Y [mm]"),               
               "velocity_mm":  ("VX [mm/s]",    "VY [mm/s]")}
    
    CurveLabels = {"position": ("X(t) [{}]", "Y(t) [{}]"),
                   "velocity": ("VX(t) {}", "VY(t) {}")}
    
    def __init__(self, mainWindow, quantity):

        # appel du constructeur de la classe de base :
        QWidget.__init__(self, mainWindow)

        self.mw = mainWindow # la fenêtre de l'application principale

        # Attributs (objets persistants)
        self.__quantity   = quantity # "position" or "velocity"
        self.__data1      = None     # data for the first plot 
        self.__data2      = None     # data for tthe second 
        self.__figure     = None     # figure tracé
        self.__axes1      = None     # système d'axes tracé 1
        self.__axes2      = None     # système d'axes tracé 2
        self.__canvas     = None     # pour le tracé matplot.lib
        self.__toolbar    = None     # barre d'outils tracé
        self.__time       = None     # abcissa values for plot
        self.__xlim       = None     # xmin, xmay tracé
        self.__xlabel     = None     # étiquette axe X (n° image ou temps [s])
        self.__ylim1      = None     # ymin, ymax tracé x(t)
        self.__ylim2      = None     # ymin, ymax tracé y(t)

        
        self.btn_imageSize = QRadioButton("ImageSize", self)
        self.btn_autoSize  = QRadioButton("AutoSize", self)
            
        self.btn_smooth_Vx = QCheckBox("Lissage Vx", self)
        self.btn_smooth_Vy = QCheckBox("Lissage Vy", self)
        self.x_mav_nb_pts  = QSpinBox(parent=self)  # X velocity moving average 
        self.y_mav_nb_pts  = QSpinBox(parent=self)  # Y velocity moving average 
         
        self.__initUI()   # Initialisation de l'interface utilisateur


    def __initUI(self):

        if  self.__quantity == "position":

            for w in (self.btn_smooth_Vx, self.btn_smooth_Vy,
                      self.x_mav_nb_pts, self.y_mav_nb_pts):
                w.setVisible(False)
                w.setEnabled(False)
            
            group = QButtonGroup(self)
            group.addButton(self.btn_imageSize)
            group.addButton(self.btn_autoSize)

            self.btn_imageSize.toggled.connect(self.__ImageSizePlotXYLim)
            self.btn_imageSize.setEnabled(False)
            texte = "Tracé avec les bornes min et max de l'image"
            self.btn_imageSize.setStatusTip(texte)
            self.btn_imageSize.setChecked(True)
            
            self.btn_autoSize.toggled.connect(self.__AutoSizePlotXYLim)
            self.btn_autoSize.setEnabled(False)
            texte = "Tracé avec les bornes min et max de la "
            texte += "trajectoire calculée"
            self.btn_autoSize.setStatusTip(texte)

        elif self.__quantity == "velocity":

            for w in (self.btn_imageSize, self.btn_autoSize):
                w.setVisible(False)
                w.setEnabled(False)

            self.btn_smooth_Vx.stateChanged.connect(self.__smooth_Vx_wanted)
            self.btn_smooth_Vy.stateChanged.connect(self.__smooth_Vy_wanted)
            
            self.x_mav_nb_pts.setEnabled(False)
            self.y_mav_nb_pts.setEnabled(False)
            self.x_mav_nb_pts.setRange(3,100)
            self.y_mav_nb_pts.setRange(3,100)
            self.x_mav_nb_pts.setSingleStep(2)
            self.y_mav_nb_pts.setSingleStep(2)           
            self.x_mav_nb_pts.valueChanged.connect(self.__smooth_vX)
            self.y_mav_nb_pts.valueChanged.connect(self.__smooth_vY)
            
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        # Ligne 1 : tracé de l'image
        self.setLayout(vbox)
        self.__figure = Figure()
        self.__axes1   = self.__figure.add_subplot(211)
        self.__axes2   = self.__figure.add_subplot(212)
        self.__figure.subplots_adjust(left=0.120,right=0.99,bottom=0.11,top=0.98)
        self.__canvas  = FigureCanvas(self.__figure)
        self.__toolbar = NavigationToolbar(self.__canvas, self)
        #self.__toolbar.setMinimumWidth(450)
        vbox.addWidget(self.__canvas)

        hbox = QHBoxLayout()
        hbox.addWidget(self.__toolbar)
        hbox.addStretch()
        
        if self.__quantity == "position":
            hbox.addWidget(self.btn_imageSize)
            hbox.addWidget(self.btn_autoSize)        
            
        elif self.__quantity == "velocity":
            vb = QVBoxLayout()
            hb = QHBoxLayout()        
            hb.addWidget(self.btn_smooth_Vx)
            hb.addWidget(self.x_mav_nb_pts)
            vb.addLayout(hb)
            hb = QHBoxLayout() 
            hb.addWidget(self.btn_smooth_Vy)
            hb.addWidget(self.y_mav_nb_pts)
            vb.addLayout(hb)            
            hbox.addLayout(vb)
            
        vbox.addLayout(hbox)            

    def reset(self):
        if self.__quantity == "velocity":
            for w in (self.btn_smooth_Vx, self.btn_smooth_Vy,
                      self.x_mav_nb_pts, self.y_mav_nb_pts):
                w.setVisible(True)
                w.setEnabled(True)
            self.x_mav_nb_pts.setValue(self.x_mav_nb_pts.minimum())
            self.y_mav_nb_pts.setValue(self.y_mav_nb_pts.minimum())
                                     

    def __smooth_Vx_wanted(self, checked):
        if checked:
            self.x_mav_nb_pts.setEnabled(True)
        else:            
            self.x_mav_nb_pts.setEnabled(False)
        self.Plot()            

    def __smooth_Vy_wanted(self, checked):
        if checked:
            self.y_mav_nb_pts.setEnabled(True)
        else:            
            self.y_mav_nb_pts.setEnabled(False)
        self.Plot()
            
    def __smooth_vX(self, nb_pts):
        if self.btn_smooth_Vx.isChecked():
            self.Plot()
        else:
            pass

    def __smooth_vY(self, nb_pts):
        if self.btn_smooth_Vy.isChecked():
            self.Plot()
        else:
            pass

    def __compute_velocity(self, U, plot_id):
        """Computes the velocity with the centered finite difference of order 1 :
           V[i] = (U[i+1] - U[i-1])/(T[i+1] - T[i-1])  for i in [1,N-1]
           V[0] = (U[1] - U[0])/(T[1] - T[0])
           V[-1] = (U[-1] - U[-2])/(T[-1] - T[-2])
        """
        V = U.copy()
        T = self.__time
        V[0]  = (U[ 1]-U[ 0])/(T[ 1]-T[ 0])
        V[-1] = (U[-1]-U[-2])/(T[-1]-T[-2])
        V[1:-1] = (U[2:]-U[:-2])/(T[2:]-T[:-2])

        if plot_id == "x":
            if self.btn_smooth_Vx.isChecked():
                N = self.x_mav_nb_pts.value()
                V = self.__smooth_data(V, N)
        elif plot_id == "y":
            if self.btn_smooth_Vy.isChecked():
                N = self.y_mav_nb_pts.value()
                V = self.__smooth_data(V, N)
        return V

    def __smooth_data(self, U, nb_pts):
        """Computes the nb_pts moving average on U."""
        N = nb_pts
        V = U.copy()
        V.fill(np.nan)
        mav = deque(maxlen=N)
        # initialize the mav (moving average) 
        for e in U[:N]: mav.append(e)
        # move!
        index, count = N//2, 0
        while count < V.shape[0] - N :
            V[index] = np.mean(mav)
            mav.append(U[N+count])
            count += 1
            index += 1
            
        return V                   

    def Plot(self):

        target_pos = self.mw.target_pos
        if target_pos is None :
            return
        else:        
            self.__data1, self.__data2, I = target_pos

        if self.__quantity == "position":
            self.btn_imageSize.setEnabled(True)
            self.btn_autoSize.setEnabled(True)
        elif self.__quantity == "velocity":
            pass

        # Effacement automatiqe si demandé à chaque nouveau tracé :
        if self.mw.flags["autoClearTraj"]:
            if self.__axes1 is not None : self.__axes1.clear()
            if self.__axes2 is not None : self.__axes2.clear()
            
        # Récupération du nom de l'alagorithme de traitement :
        algo = self.mw.imageTab.btn_algo.currentText()

        # Récupération de la valeur de FP (Frame per seconde) pour calcul
        # du pas de temps et des abscisses :
        deltaT = None
        if self.mw.imageTab.video_FPS is not None:
            deltaT = 1./self.mw.imageTab.video_FPS
            self.__time = np.array(I)*deltaT
            self.__xlabel = "temps [s]"
        else:
            self.__time = np.array(I)
            self.__xlabel = "image #"

        if self.__quantity == "velocity" :
            if deltaT is not None:
                self.__data1 = self.__compute_velocity(self.__data1, "x")
                self.__data2 = self.__compute_velocity(self.__data2, "y")
                if self.btn_smooth_Vx.isChecked():
                    N = self.x_mav_nb_pts.value()
                if self.btn_smooth_Vy.isChecked():
                    N = self.y_mav_nb_pts.value()
                self.__AutoSizePlotXYLim()
            else:
                self.__data1, self.__data2 = None, None
            self.mw.target_veloc = np.array([self.__data1, self.__data2])
        else:
            self.__ImageSizePlotXYLim()
        
        if self.__data1 is None or self.__data2 is None: return
        
        curveLabelX, curveLabelY = TwoPlots.CurveLabels[self.__quantity]
        if self.__quantity == "position" :
            Xlabel, Ylabel = curveLabelX.format(algo), curveLabelY.format(algo)
        else:
            Xlabel, Ylabel = curveLabelX.format(""), curveLabelY.format("")

        color = 'b' if self.mw.target_RGB is None else self.mw.target_RGB/255

        # tracé de courbe x(t)
        self.__axes1.plot(self.__time, self.__data1,
                          color = color,
                          marker = 'o', markersize = 2,
                          linewidth = .4,
                          label=Xlabel)
        self.__axes1.grid(True)
        #self.__axes1.legend(fontsize=9, framealpha=0.7,
        #                   bbox_to_anchor=(-0.1, 1.1), loc='upper left')
        self.__axes1.legend(loc='best',fontsize=10)

        # tracé de courbe y(t)
        self.__axes2.plot(self.__time, self.__data2,
                          color = color,
                          marker = 'o', markersize = 2,
                          linewidth = .4, 
                          label=Ylabel)
        self.__axes2.grid(True)
        #self.__axes2.legend(fontsize=9, framealpha=0.7,
        #                   bbox_to_anchor=(1.1, 1.1), loc='upper right')
        self.__axes2.legend(loc='best',fontsize=10)

        self.__canvas.draw()

    def __AutoSizePlotXYLim(self):

        if self.mw.target_pos is None: return

        y1label, y2label =  TwoPlots.Ylabels[self.__quantity]
        self.__xlim  = np.array([np.nanmin(self.__time), np.nanmax(self.__time)])

        if not self.btn_smooth_Vx.isChecked():
            self.__ylim1 = np.array([np.nanmin(self.__data1), np.nanmax(self.__data1)])
            offset = (self.__ylim1[1]-self.__ylim1[0])/10
            self.__ylim1 += np.array([-offset, offset])
        else:
            #self.__ylim1 = self.__axes1.get_ylim()
            pass

        if not self.btn_smooth_Vy.isChecked():
            self.__ylim2 = np.array([np.nanmin(self.__data2), np.nanmax(self.__data2)])
            offset = (self.__ylim2[1]-self.__ylim2[0])/10
            self.__ylim2 += np.array([-offset, offset])
        else:
            #self.__ylim2 = self.__axes2.get_ylim()
            pass
        
        if self.mw.imageTab.valid_scale:
            y1label, y2label = TwoPlots.Ylabels[self.__quantity+"_mm"]

        self.__axes1.set_xlim(*self.__xlim)
        self.__axes2.set_xlim(*self.__xlim)
        self.__axes1.set_ylim(*self.__ylim1)
        self.__axes2.set_ylim(*self.__ylim2)
        self.__axes1.set_ylabel(y1label)
        self.__axes2.set_ylabel(y2label)
        self.__axes2.set_xlabel(self.__xlabel)

        self.__canvas.draw()


    def __ImageSizePlotXYLim(self):

        if self.mw.target_pos is None: return
        
        y1label, y2label = TwoPlots.Ylabels[self.__quantity]
        w, h = self.mw.imageTab.video_size
        self.__xlim  = np.array([np.nanmin(self.__time), np.nanmax(self.__time)])
        self.__ylim1 = np.array([0, w-1], dtype=float)
        self.__ylim2 = np.array([0, h-1], dtype=float)

        if self.mw.imageTab.valid_scale:
            self.__ylim1 *= self.mw.imageTab.pix_to_mm_coeff
            self.__ylim2 *= self.mw.imageTab.pix_to_mm_coeff
            y1label, y2label = TwoPlots.Ylabels[self.__quantity+"_mm"]

        self.__axes1.set_xlim(*self.__xlim)
        self.__axes2.set_xlim(*self.__xlim)
        self.__axes1.set_ylim(*self.__ylim1)
        self.__axes2.set_ylim(*self.__ylim2)
        self.__axes1.set_ylabel(y1label)
        self.__axes2.set_ylabel(y2label)
        self.__axes2.set_xlabel(self.__xlabel)

        self.__canvas.draw()

    def ClearAxes(self):
        if self.__axes1 is not None : self.__axes1.clear()
        if self.__axes2 is not None : self.__axes2.clear()
        self.__canvas.draw()

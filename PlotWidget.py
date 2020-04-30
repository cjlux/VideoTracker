#
# version 1.3 -- 2019-05-07 -- JLC --
#   add Export CVS
#
# version 1.4 -- 2019-05-18 -- JLC -- 
#   add PlotFunction tab.
#
import numpy as np
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout,\
                            QRadioButton, QButtonGroup

from matplotlib.backends.backend_qt5agg import  \
    FigureCanvasQTAgg as FigureCanvas,          \
    NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class OnePlot(QWidget):
    ''' Widget de tracé d'une courbe Y=f(X)'''

    def __init__(self, mainWindow):

        # appel du constructeur de la classe de base :
        QWidget.__init__(self, mainWindow)

        self.mw = mainWindow    # fenêtre de l'application

        # Attributs (objets persistants)
        self.__figure      = None  # figure tracé
        self.__axes        = None  # sysrème d'axes tracé
        self.__canvas      = None  # pour le tracé matplot.lib
        self.__toolbar     = None  # barre d'outils tracé
        self.__xlim        = None  # xmin, xmay tracé
        self.__ylim        = None  # ymin, ymax tracé
        self.__axes_aspect = 'equal' # 'equal' ou 'auto'

        self.__btn_imageSize = QRadioButton("ImageSize", self)
        self.__btn_autoSize  = QRadioButton("AutoSize", self)
        self.btn_axesEqual = QRadioButton("Equal", self)
        self.btn_axesAuto  = QRadioButton("Auto", self)
        group = QButtonGroup(self) # pour les 2 boutons imageSize, autoSize
        group.addButton(self.__btn_imageSize)
        group.addButton(self.__btn_autoSize)        

        self.__initUI()   # Initialisation de l'interface utilisateur


    def __initUI(self):

        self.__figure  = Figure()
        self.__axes    = self.__figure.add_subplot(111)
        self.__figure.subplots_adjust(left=0.1,right=0.98,bottom=0.1,top=0.95)
        self.__canvas  = FigureCanvas(self.__figure)
        self.__toolbar = NavigationToolbar(self.__canvas, self)

        self.btn_axesEqual.toggled.connect(lambda : self.__SetAspect("equal"))
        self.btn_axesEqual.setEnabled(False)
        texte = "Tracé dans des axes orthonormés"
        self.btn_axesEqual.setStatusTip(texte)

        self.btn_axesAuto.toggled.connect(lambda : self.__SetAspect("auto"))
        self.btn_axesAuto.setEnabled(False)
        texte = "Tracé dans des axes non orthonormés"
        self.btn_axesAuto.setStatusTip(texte)
        self.btn_axesAuto.setChecked(True)

        self.__btn_imageSize.toggled.connect(self.__ImageSizePlotXYLim)
        self.__btn_imageSize.setEnabled(False)
        texte = "Tracé avec les bornes min et max de l'image"
        self.__btn_imageSize.setStatusTip(texte)

        self.__btn_autoSize.toggled.connect(self.__AutoSizePlotXYLim)
        self.__btn_autoSize.setEnabled(False)
        texte = "Tracé avec les bornes min et max de la "
        texte += "trajectoire calculée"
        self.__btn_autoSize.setStatusTip(texte)
        self.__btn_autoSize.setChecked(True)

        vbox = QVBoxLayout()
        self.setLayout(vbox)

        #self.__toolbar.setMinimumWidth(450)
        vbox.addWidget(self.__canvas)

        hbox = QHBoxLayout()
        hbox.addWidget(self.__toolbar)
        hbox.addStretch()
        hbox.addWidget(self.btn_axesEqual)
        hbox.addWidget(self.btn_axesAuto)
        hbox.addWidget(self.__btn_imageSize)
        hbox.addWidget(self.__btn_autoSize)

        vbox.addLayout(hbox)

    def __SetAspect(self, aspect):
        self.__axes_aspect = aspect
        self.__axes.set_aspect(aspect)
        self.__canvas.draw()

    def __AutoSizePlotXYLim(self):

        if self.mw.target_pos is None: return

        xlabel, ylabel =  "X [pixels]", "Y [pixels]"
        X, Y = self.mw.target_pos[0], self.mw.target_pos[1]
        self.__xlim = np.array([X.min(), X.max()])
        self.__ylim = np.array([Y.min(), Y.max()])

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

        xlabel, ylabel =  "X [pixels]", "Y [pixels]"
        w, h = self.mw.imageTab.video_size
        self.__xlim = np.array([0, w-1], dtype=float)
        self.__ylim = np.array([0, h-1], dtype=float)

        if self.mw.imageTab.valid_scale:
            self.__xlim *= self.mw.imageTab.pix_to_mm_coeff
            self.__ylim *= self.mw.imageTab.pix_to_mm_coeff
            xlabel = "X [mm]"
            ylabel = "Y [mm]"

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

        self.__btn_imageSize.setEnabled(True)
        self.__btn_autoSize.setEnabled(True)
        self.btn_axesEqual.setEnabled(True)
        self.btn_axesAuto.setEnabled(True)

        # Effacement automatique si demandé à chaque nouveau tracé :
        if self.mw.flags["autoClearTraj"]: self.__axes.clear()

        # Récupération du nom de l'alagorithme de traitement :
        algo = self.mw.imageTab.btn_algo.currentText()

        # Définition du label Y :
        self.__AutoSizePlotXYLim()

        # tracé de courbe paramétrée (X(t),Y(t)) :
        self.__axes.plot(X,Y,
                       color = self.mw.target_RGB/255,
                       marker = 'o',
                       markersize = 3,
                       label="Trajectoire XY / algo : {}".format(algo))

        self.__axes.grid(True)
        self.__axes.legend(loc='best',fontsize=10)
        self.__axes.set_aspect(self.__axes_aspect)
        self.__canvas.draw()


class TwoPlots(QWidget):
    ''' Widget de tracé de deux courbes X(t) et Y(t)'''

    def __init__(self, mainWindow):

        # appel du constructeur de la classe de base :
        QWidget.__init__(self, mainWindow)

        self.mw = mainWindow # la fenêtre de l'application principale

        # Attributs (objets persistants)
        self.__figure     = None  # figure tracé
        self.__axes1      = None  # système d'axes tracé X(t)
        self.__axes2      = None  # système d'axes tracé Y(t)
        self.__canvas     = None  # pour le tracé matplot.lib
        self.__toolbar    = None  # barre d'outils tracé
        self.__time       = None  # abcissa values for plot
        self.__xlim       = None  # xmin, xmay tracé
        self.__xlabel     = None  # étiquette axe X (n° image ou temps [s])
        self.__ylim1      = None  # ymin, ymax tracé X(t)
        self.__ylim2      = None  # ymin, ymax tracé Y(t)

        self.__btn_imageSize = QRadioButton("ImageSize", self)
        self.__btn_autoSize  = QRadioButton("AutoSize", self)

        self.__initUI()   # Initialisation de l'interface utilisateur


    def __initUI(self):

        self.__btn_imageSize.toggled.connect(self.__ImageSizePlotXYLim)
        self.__btn_imageSize.setEnabled(False)
        texte = "Tracé avec les bornes min et max de l'image"
        self.__btn_imageSize.setStatusTip(texte)

        self.__btn_autoSize.toggled.connect(self.__AutoSizePlotXYLim)
        self.__btn_autoSize.setEnabled(False)
        self.__btn_autoSize.setChecked(True)
        
        texte = "Tracé avec les bornes min et max de la "
        texte += "trajectoire calculée"
        self.__btn_autoSize.setStatusTip(texte)

        vbox = QVBoxLayout()
        self.setLayout(vbox)

        # Ligne 1 : tracé de l'image
        self.setLayout(vbox)
        self.__figure = Figure()
        self.__axes1   = self.__figure.add_subplot(211)
        self.__axes2   = self.__figure.add_subplot(212)
        self.__figure.subplots_adjust(left=0.15,right=0.98,bottom=0.11,top=0.98)
        self.__canvas  = FigureCanvas(self.__figure)
        self.__toolbar = NavigationToolbar(self.__canvas, self)
        #self.__toolbar.setMinimumWidth(450)
        vbox.addWidget(self.__canvas)

        hbox = QHBoxLayout()
        hbox.addWidget(self.__toolbar)
        hbox.addStretch()
        hbox.addWidget(self.__btn_imageSize)
        hbox.addWidget(self.__btn_autoSize)

        vbox.addLayout(hbox)


    def __AutoSizePlotXYLim(self):

        if self.mw.target_pos is None: return

        y1label, y2label =  "X [pixels]", "Y [pixels]"
        X, Y = self.mw.target_pos[0], self.mw.target_pos[1]
        self.__xlim = np.array([self.__time.min(), self.__time.max()])
        self.__ylim1 = np.array([X.min(), X.max()])
        self.__ylim2 = np.array([Y.min(), Y.max()])

        if self.mw.imageTab.valid_scale:
            y1label = "X [mm]"
            y2label = "Y [mm]"

        offset = (self.__ylim1[1]-self.__ylim1[0])/10
        self.__ylim1 += np.array([-offset, offset])
        offset = (self.__ylim2[1]-self.__ylim2[0])/10
        self.__ylim2 += np.array([-offset, offset])

        self.__axes1.set_xlim(*self.__xlim)
        self.__axes2.set_xlim(*self.__xlim)
        self.__axes1.set_ylim(*self.__ylim1)
        self.__axes2.set_ylim(*self.__ylim2)
        self.__axes1.set_ylabel(y1label)
        self.__axes2.set_ylabel(y2label)
        self.__axes2.set_xlabel(self.__xlabel)

        self.__canvas.draw()


    def __ImageSizePlotXYLim(self):

        y1label, y2label =  "X [pixels]", "Y [pixels]"
        w, h = self.mw.imageTab.video_size
        self.__xlim  = np.array([self.__time.min(), self.__time.max()])
        self.__ylim1 = np.array([0, w-1], dtype=float)
        self.__ylim2 = np.array([0, h-1], dtype=float)

        if self.mw.imageTab.valid_scale:
            self.__ylim1 *= self.mw.imageTab.pix_to_mm_coeff
            self.__ylim2 *= self.mw.imageTab.pix_to_mm_coeff
            y1label = "X [mm]"
            y2label = "Y [mm]"

        self.__axes1.set_xlim(*self.__xlim)
        self.__axes2.set_xlim(*self.__xlim)
        self.__axes1.set_ylim(*self.__ylim1)
        self.__axes2.set_ylim(*self.__ylim2)
        self.__axes1.set_ylabel(y1label)
        self.__axes2.set_ylabel(y2label)
        self.__axes2.set_xlabel(self.__xlabel)

        self.__canvas.draw()

    def ClearAxes(self):
        self.__axes1.clear()
        self.__axes2.clear()
        self.__canvas.draw()

    def Plot(self):

        target_pos = self.mw.target_pos
        X, Y, I = target_pos

        self.__btn_imageSize.setEnabled(True)
        self.__btn_autoSize.setEnabled(True)

        # Effacement automatiqe si demandé à chaque nouveau tracé :
        if self.mw.flags["autoClearTraj"]:
            self.__axes1.clear()
            self.__axes2.clear()

        # Récupération du nom de l'alagorithme de traitement :
        algo = self.mw.imageTab.btn_algo.currentText()

        # Récupération de la valeur de FP (Frame per seconde) pour calcul
        # du pas de temps et des abscisses :
        if self.mw.imageTab.video_FPS is not None:
            deltaT = 1./self.mw.imageTab.video_FPS
            self.__time = np.array(I)*deltaT
            self.__xlabel = "temps [s]"
        else:
            self.__time = np.array(I)
            self.__xlabel = "image #"

        self.__AutoSizePlotXYLim()

        # tracé de courbe X(t)
        self.__axes1.plot(self.__time,X,
                        color = self.mw.target_RGB/255,
                        marker = 'o',
                        markersize = 3,
                        label="Courbe X(t) [algo : {}]".format(algo))
        self.__axes1.grid(True)
        self.__axes1.legend(loc='best',fontsize=10)

        # tracé de courbe Y(t)
        self.__axes2.plot(self.__time,Y,
                        color = self.mw.target_RGB/255,
                        marker = 'o',
                        markersize = 3,
                        label="Courbe Y(t) [algo : {}]".format(algo))
        self.__axes2.grid(True)
        self.__axes2.legend(loc='best',fontsize=10)

        self.__canvas.draw()


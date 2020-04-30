#
# version 1.3 -- 2019-05-07 -- JLC -- 
#   add Export CVS
#   self.__target_pos is moved in class MyApp
#
# version 1.4 -- 2019-05-18 -- JLC -- 
#   add PlotFunction tab.
#
# version 1.5 -- 2020-04-24 -- JLC -- 
#   add IPython console tab.
#

import numpy as np
import os, sys, platform

from PyQt5.Qt import (QApplication, QFileDialog, QMainWindow,
                      QDesktopWidget, QTabWidget, QAction, QIcon)

from ImageWidget import ImageDisplay
from PlotWidget import OnePlot, TwoPlots
from PlotFunction import FunctionPlot
from PythonConsoleWidget import PythonConsole

class MyApp(QMainWindow):

    icone_dir   = "icones/"
    image_fmt   = "image{:04d}.png" # to format image names
    cur_dir     = os.getcwd()+"/"   # working directory
    image_dir   = os.getcwd()+"/Images/" # directory for extracted images foldes

    def __init__(self):

        # Gestion des répertoires statiques
        if not os.path.isdir(MyApp.icone_dir) :
            print("Répertoire des icônes non trouvé.")

        if not os.path.isdir(MyApp.image_dir) :
            msg = "Répertoire des images créés :\n\t'{}'"
            print(msg.format(MyApp.image_dir))
            os.mkdir(MyApp.image_dir)

        # Simple syntaxe to call the base class contsructor
        super(MyApp, self).__init__()

        #
        # *** Bonnes pratiques  ***
        #   Définir dans le constructeur les données persistantes en tant qu'attributs,
        #   et si con ne connaît pas leur valeur à ce endroit on utilise None:
        #

        # Attributes (persistant objects)

        self.video_path  = None # last loaded video path
        self.images_dir  = None # Dossier contenant les images
        self.img_idx     = None # Rank of current displayed image
        self.img_path    = None # current image path
        self.nb_img      = None # number of extracted images

        # self.flags : dictionnary of flags :
        #  debug         -> display or not various informations 
        #  displayInfo   -> display or non information windows
        #  autoClearTraj -> automatically clear trajectory plot before a new plot
        #  drawTargetSelection -> draw/not draw the selected color area
        
        self.flags = {"debug":          False,
                      "displayInfo":    True,
                      "autoClearTraj":  True,
                      "drawTargetSelection": False}

        self.__target_pos = None # target position x, y
            
        self.__initUI()   # User Interface initialisation
        self.show()       # Display this window

    @property
    def target_pos(self): return self.__target_pos

    @target_pos.setter
    def target_pos(self, data):
        if not isinstance(data, np.ndarray):
            raise Exception("target_pos should be a numpy.ndarray object !")
        self.__target_pos = data

    def center(self):
        '''To center the current window in the current display'''
        desktop = QApplication.desktop()
        n = desktop.screenNumber(self.cursor().pos())
        screen_center = desktop.screenGeometry(n).center()
        geo_window = self.frameGeometry()
        geo_window.moveCenter(screen_center)
        self.move(geo_window.topLeft())

    def __initUI(self):
        self.resize(800, 600)
        self.center()
        self.setWindowTitle('Application de tracking vidéo')
        self.statusBar()  # status bar at the bottom of the window

        # QTabWidget of the application showing the 5 tabs
        self.tabs = QTabWidget()
        # tab1: display video images & video metadata
        self.imageTab = ImageDisplay(self)
        # tab2: plot (Y(t), X(t))
        self.onePlot  = OnePlot(self)
        # tab3: plot curves X(t) and Y(t)
        self.twoPlots = TwoPlots(self)
        # tab4: plot of f(t)=f(X(t), Y(t), t)
        self.functionOfXY = FunctionPlot(self)
        # tab5: IPython shell
        self.pythonConsole = PythonConsole(self)

        self.tabs.addTab(self.imageTab,"Visualisation images")
        self.tabs.addTab(self.onePlot,"Trajectoire cible ")
        self.tabs.addTab(self.twoPlots,"Courbes X(t), Y(t)")
        self.tabs.addTab(self.functionOfXY,"function Z(t)=Z(X(t),Y(t))")
        self.tabs.addTab(self.pythonConsole,"IPython console")
        self.setCentralWidget(self.tabs)

        # Menu(s)
        self.menubar = self.menuBar()
        if platform.uname().system.startswith('Darw') :
            # Mac OS specificity:
            self.menubar.setNativeMenuBar(False)

        ###### Menu 'Files'
        fileMenu = self.menubar.addMenu('&Fichier')

        ### Open images directory:
        qa = QAction(QIcon(MyApp.icone_dir+'/open.png'),
                           'Ouvrir dossier images', self)
        qa.setShortcut('Ctrl+D')
        qa.setStatusTip("Ouvre un dossier contenant déjà "+\
                             "les images d'une vidéo")
        # connexion avec la méthode 'load_images_from_directory' qui est
        # définie dans l'objet 'imageTab' :
        qa.triggered.connect(self.imageTab.load_images_from_directory)
        fileMenu.addAction(qa)

        ### Load a video file :
        qa = QAction(QIcon(MyApp.icone_dir+'/open.png'),
                           "Charger un fichier vidéo", self)
        qa.setShortcut('Ctrl+O')
        qa.setStatusTip('Ouvre un fihier vidéo et le '+\
                             'découpe en images successives...')
        # connexion avec la méthode 'open_video' qui est définie dans
        # l'objet 'imageTab' :
        qa.triggered.connect(self.imageTab.open_video)
        fileMenu.addAction(qa)

        ### Quit :
        qa = QAction(QIcon(MyApp.icone_dir+'/exit.png'),\
                          'Quitter', self)
        qa.setShortcut('Ctrl+Q')
        qa.setStatusTip("Quitter l'application")
        qa.triggered.connect(self.close)
        fileMenu.addAction(qa)

        ### Export CSV:
        qa = QAction(QIcon(MyApp.icone_dir+'/csv.png'),\
                          'Export data to CSV file', self)
        qa.setStatusTip("Exporte les données extraites de la vidéo dans un"+\
                        "fichier CSV.")
        qa.triggered.connect(self.ExportCSV)
        fileMenu.addAction(qa)

        ######  Le menu 'Options'
        optionMenu = self.menubar.addMenu('&Options')

        ### Display info box windows:
        qa = QAction('Afficher boîtes info',
                                 self, checkable=True)
        text = 'Afficher ou non les boîtes de dialogue d\'information'
        qa.setStatusTip(text)# message in the status bar
        qa.setChecked(True)
        qa.triggered.connect(lambda e: self.set_flag("displayInfo",e))
        optionMenu.addAction(qa)

        ### Verbose mode :
        qa = QAction('Mode verbeux', self, checkable=True)
        text  = 'Afficher ou non des informations dans le shell Python'
        qa.setStatusTip(text)    # message in the status bar
        qa.setChecked(True)
        qa.triggered.connect(lambda e: self.set_flag("debug", e))
        optionMenu.addAction(qa)

        ### Clear trajectory plots before a new plot:
        qa = QAction('Effacement trajectoire avant tracé',
                                self, checkable=True)
        text  = 'Effacer automatiquement le tracé des onglets <Trajectoires> et '
        text += '<X(t) et Y(t)> un nouveau tracé ?'
        qa.setStatusTip(text)  # message in the status bar
        qa.setChecked(True)
        qa.triggered.connect(lambda e: self.set_flag("autoClearTraj", e) )
        optionMenu.addAction(qa)

        ### draw/not draw the selected color area
        qa = QAction('Dessiner la sélection couluer de la cible',
                                self, checkable=True)
        text  = 'Dessine la zone sélectionnée pour la couleur de la cible'
        qa.setStatusTip(text)  # message in the status bar
        qa.setChecked(True)
        qa.triggered.connect(lambda e: self.set_flag("drawTargetSelection", e))
        optionMenu.addAction(qa)

    def set_flag(self, flag, state):
        if self.flags["debug"]: print("{} -> {}".format(flag, state))
        self.flags[flag] = state
        if self.flags["debug"]: print("set_flag: {} -> {}".format(flag, self.flags[flag]))

    def clearPlots(self):
        self.onePlot.ClearAxes()
        self.twoPlots.ClearAxes()
        self.functionOfXY.ClearAxes()

    def ExportCSV(self):
        '''Export Data in a CSV file.'''
        if self.__target_pos is None :
            self.statusBar().showMessage("pasq de données à exporter.")
            return

        # Lance un sélecteur de fichier pour choisir le fichier à écrire.'''
        fname = QFileDialog.getSaveFileName(self,
                                            'Choisir un nom de fichier CSV à écrire',
                                            self.cur_dir,
                                            'Fichier CSV (*.csv *.txt)')
        if fname[0] == "": return 

        nbImages = len(self.__target_pos[0])
        if self.imageTab.video_FPS is not None:
            deltaT = 1./self.imageTab.video_FPS
            time = np.arange(nbImages)*deltaT
            tlabel, tformat = "T [seconde]", "%10.6e"
        else:
            time = range(1, nbImages+1)
            tlabel, tformat = "image #", "%10d"

        # building headers:
        xlabel, ylabel   =  "X [pixels]", "Y [pixels]"
        xformat, yformat = "%10d", "%10d"
        if self.imageTab.valid_scale:
            xlabel, ylabel   = "X [mm]", "Y [mm]"
            xformat, yformat = "%10.6e", "%10.6e"
            
        header = "{};{};{}".format(tlabel, xlabel, ylabel)
        fmt = (tformat, xformat, yformat)
        data = []
        data.append(time)
        data.append(self.__target_pos[0].tolist())
        data.append(self.__target_pos[1].tolist())
        data = np.array(data)

        fileName = fname[0]
        if not fileName.endswith(".csv"): fileName += ".csv"
        np.savetxt(fileName, data.transpose(), delimiter=";",
                   header=header, fmt=fmt)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    my  = MyApp()
    sys.exit(app.exec_())

#
# version 1.3 -- 2019-05-07 -- JLC -- 
#   add Export CVS
#   self.__target_pos is moved in class MyApp
#
# version 1.4 -- 2019-05-18 -- JLC -- 
#   add PlotFunction tab.
#

import numpy as np
import os, sys, platform

from PyQt5.QtWidgets import (QApplication, QFileDialog, QMainWindow,
                             QDesktopWidget, QTabWidget, QAction)
from PyQt5.QtGui import QIcon

from ImageWidget import ImageDisplay
from PlotWidget import OnePlot, TwoPlots
from PlotFunction import FunctionPlot

class MyApp(QMainWindow):

    icone_dir   = "icones"
    image_fmt   = "image{:04d}.png" # Nom automatique des images
    cur_dir     = os.getcwd()+"/"   # Répertoire de travail
    image_dir   = os.getcwd()+"/Images/" # Dossier des images

    def __init__(self):

        # Gestion des répertoires statiques
        if not os.path.isdir(MyApp.icone_dir) :
            print("Répertoire des icônes non trouvé.")

        if not os.path.isdir(MyApp.image_dir) :
            msg = "Répertoire des images créés :\n\t'{}'"
            print(msg.format(MyApp.image_dir))
            os.mkdir(MyApp.image_dir)

        # Style simple pour l'appel du constructeur de la classe de base :
        super().__init__()

        #
        # *** Bonnes pratiques  ***
        #   Définir dans le constructeur les données persistantes en tant qu'attributs,
        #   et si con ne connaît pas leur valeur à ce endroit on utilise None:
        #

        # Attributs (objets persistants)

        self.video_path  = None # Chemin de la dernière vidéo
        self.images_dir  = None # Dossier contenant les images
        self.img_idx     = None # Rang de l'image affichée
        self.img_path    = None # nom du chemin de l'image courante
        self.nb_img      = None # nombre d'images

        # self.flags : dictionnaire des flags :
        #  debug         -> affiche ou pas des informations pendant
        #                   l'exécution de l'application
        #  displayInfo   -> contrôle l'affichage des boîtes d'information
        #  autoClearTraj -> effacer automatiquement le tracé trajectoire
        #                   avant un nouveau tracé
        self.flags = {"debug":          False,
                      "displayInfo":    True,
                      "autoClearTraj":  True}

        self.__target_pos = None # target position x, y
            
        self.__initUI()   # Initialisation de l'interface utilisateur
        self.show()       # Affichage

    @property
    def target_pos(self): return self.__target_pos

    @target_pos.setter
    def target_pos(self, data):
        if not isinstance(data, np.ndarray):
            raise Exception("target_pos should be a numpy.ndarray object !")
        self.__target_pos = data

    def center(self):
        '''Pour centrer la fenêtre dans l'écran'''
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
        self.statusBar()  # Barre de statut

        # Création d'un objet QTabWidget avec 3 onglets
        self.tabs = QTabWidget()
        # onglet 1 : affichage des images de la vidéos + méta-données
        self.imageTab = ImageDisplay(self)
        # onglet 2 : tracé de la courbe paramétrée (Y(t), X(t))
        self.onePlot  = OnePlot(self)
        # onglet 3 : tracé des courbes X(t) et Y(t)
        self.twoPlots = TwoPlots(self)
        # onglet 4 : tracé de f(t)=f(X(t), Y(t))
        self.functionOfXY = FunctionPlot(self)

        self.tabs.addTab(self.imageTab,"Visualisation images")
        self.tabs.addTab(self.onePlot,"Trajectoire cible ")
        self.tabs.addTab(self.twoPlots,"Courbes X(t), Y(t)")
        self.tabs.addTab(self.functionOfXY,"function f(t)=f(X(t),Y(t))")
        self.setCentralWidget(self.tabs)

        # Menu(s)

        self.menubar = self.menuBar()
        if platform.uname().system.startswith('Darw') :
            # programme exécuté sur une plateforme Apple :
            self.menubar.setNativeMenuBar(False)

        ###### Le menu 'Fichier'
        fileMenu = self.menubar.addMenu('&Fichier')

        ### Ouvrir dossier images :
        qa = QAction(QIcon(MyApp.icone_dir+'open.png'),
                           'Ouvrir dossier images', self)
        qa.setShortcut('Ctrl+D')
        qa.setStatusTip("Ouvre un dossier contenant déjà "+\
                             "les images d'une vidéo")
        # connexion avec la méthode 'load_images_from_directory' qui est
        # définie dans l'objet 'imageTab' :
        qa.triggered.connect(self.imageTab.load_images_from_directory)
        fileMenu.addAction(qa)

        ### Charger un fichier vidéo :
        qa = QAction(QIcon(MyApp.icone_dir+'open.png'),
                           "Charger un fichier vidéo", self)
        qa.setShortcut('Ctrl+O')
        qa.setStatusTip('Ouvre un fihier vidéo et le '+\
                             'découpe en images successives...')
        # connexion avec la méthode 'open_video' qui est définie dans
        # l'objet 'imageTab' :
        qa.triggered.connect(self.imageTab.open_video)
        fileMenu.addAction(qa)

        ### Quitter :
        qa = QAction(QIcon(MyApp.icone_dir+'exit.png'),\
                          'Quitter', self)
        qa.setShortcut('Ctrl+Q')
        qa.setStatusTip("Quitter l'application")
        qa.triggered.connect(self.close)
        fileMenu.addAction(qa)

        ### Export CSV:
        qa = QAction(QIcon(MyApp.icone_dir+'csv.png'),\
                          'Export data to CSV file', self)
        qa.setStatusTip("Exporte les données extraites de la vidéo dans un"+\
                        "fichier CSV.")
        qa.triggered.connect(self.ExportCSV)
        fileMenu.addAction(qa)

        ######  Le menu 'Options'
        optionMenu = self.menubar.addMenu('&Options')

        ### Afficher boîtes info :
        qa = QAction('Afficher boîtes info',
                                 self, checkable=True)
        text = 'Afficher ou non les boîtes de dialogue d\'information'
        qa.setStatusTip(text)# message dans la barre de status
        qa.setChecked(True)
        qa.triggered.connect(lambda e: self.set_flag("displayInfo",e))
        optionMenu.addAction(qa)

        ### Mode verbeux :
        qa = QAction('Mode verbeux', self, checkable=True)
        text  = 'Afficher ou non des informations dans le shell Python'
        qa.setStatusTip(text)    # message dans la barre de status
        qa.setChecked(True)
        qa.triggered.connect(lambda e: self.set_flag("debug", e) )
        optionMenu.addAction(qa)

        ### Effacement trajectoire avant tracé :
        qa = QAction('Effacement trajectoire avant tracé',
                                self, checkable=True)
        text  = 'Effacer automatiquement le tracé des onglets <Trajectoires> et '
        text += '<X(t) et Y(t)> un nouveau tracé ?'
        qa.setStatusTip(text)  # message dans la barre de status
        qa.setChecked(True)
        qa.triggered.connect(lambda e: self.set_flag("autoClearTraj", e) )
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

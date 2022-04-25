#
# version 1.3 -- 2019-05-07 -- JLC -- 
#   add Export CVS
#   self.__target_pos is moved in class VideoTracker
#
# version 1.4 -- 2019-05-18 -- JLC -- 
#   add PlotFunction tab.
#
# version 1.5 -- 2020-04-24 -- JLC -- 
#   add IPython console tab.
#
# version 1.6 -- 2020-05-23 -- JLC -- 
#   add CVS import.
#
# version 1.7 -- 2021-04-28 -- JLC -- 
#   Fix bug: data in exported CSV file are not scaled.
#

import numpy as np
import os, sys, platform
import pandas

from PyQt5.Qt import (QApplication, QFileDialog, QMainWindow, QMessageBox,
                      QDesktopWidget, QTabWidget, QAction, QIcon, QPixmap)

from ImageWidget import ImageDisplay
from PlotWidget import OnePlot, TwoPlots
from PlotFunction import FunctionPlot
from PythonConsoleWidget import PythonConsole

class VideoTracker(QMainWindow):

    image_fmt   = "image{:04d}.png" # to format image names
    icone_dir   = "icones/"         # directory of icones
    cur_dir     = os.getcwd()       # working directory
    image_dir   = os.path.join(os.getcwd(), "Images") # directory of images
    csv_dir     = os.path.join(cur_dir, "CSV")        # directory of CSV files

    def __init__(self):

        if not os.path.isdir(VideoTracker.icone_dir) :
            print("Répertoire des icônes non trouvé.")

        if not os.path.isdir(VideoTracker.image_dir) :
            msg = "Répertoire des images créés :\n\t'{}'"
            print(msg.format(VideoTracker.image_dir))
            os.mkdir(VideoTracker.image_dir)
            
        if not os.path.isdir(VideoTracker.csv_dir) :
            msg = "Répertoire CSV créé :\n\t'{}'"
            print(msg.format(VideoTracker.csv_dir))
            os.mkdir(VideoTracker.csv_dir)
            

        # Simple syntaxe to call the base class contsructor
        super(VideoTracker, self).__init__()

        #
        # *** Bonnes pratiques  ***
        #   Définir dans le constructeur les données persistantes en tant qu'attributs,
        #   et si on ne connaît pas leur valeur à ce endroit on utilise None:
        #

        self.csv_dir = os.path.join(VideoTracker.cur_dir, "CSV")
        
        # self.flags : dictionnary of flags :
        #  debug         -> display or not various informations 
        #  displayInfo   -> display or non information windows
        #  autoClearTraj -> automatically clear trajectory plot before a new plot
        #  drawTargetSelection -> draw/not draw the selected color area
        
        self.flags = {"debug":          False,
                      "displayInfo":    True,
                      "autoClearTraj":  True,
                      "drawTargetSelection": True}
        self.csv_dataFrame  = None # Data 
        self.__target_pos   = None # target positions x, y
        self.__target_veloc = None # target velocities x, y
        self.__target_accel = None # target accelerations x, y
        self.target_RGB     = None # color plor drawing plots
        self.unit_dict      = None
            
        self.__initUI()   # User Interface initialisation
        self.show()       # Display this window

    @property
    def target_pos(self): return self.__target_pos

    @target_pos.setter
    def target_pos(self, data):
        if not isinstance(data, np.ndarray):
            raise Exception("target_pos should be a numpy.ndarray object !")
        self.__target_pos = data

    @property
    def target_veloc(self): return self.__target_veloc

    @target_veloc.setter
    def target_veloc(self, data):
        if not isinstance(data, np.ndarray):
            raise Exception("target_veloc should be a numpy.ndarray object !")
        self.__target_veloc = data
    @property
    def target_accel(self): return self.__target_accel

    @target_accel.setter
    def target_accel(self, data):
        if not isinstance(data, np.ndarray):
            raise Exception("target_accel should be a numpy.ndarray object !")
        self.__target_accel = data

    def center(self):
        '''To center the current window in the current display'''
        desktop = QApplication.desktop()
        n = desktop.screenNumber(self.cursor().pos())
        screen_center = desktop.screenGeometry(n).center()
        geo_window = self.frameGeometry()
        geo_window.moveCenter(screen_center)
        self.move(geo_window.topLeft())

    def __initUI(self):
        self.resize(850, 650)
        self.center()
        self.setWindowTitle('Application de tracking vidéo')
        self.statusBar()  # status bar at the bottom of the window

        # QTabWidget of the application showing the 5 tabs
        self.tabs = QTabWidget()
        # tab1: display video images & video metadata
        self.imageTab = ImageDisplay(self)
        # tab2: plot (y(t), x(t))
        self.onePlot  = OnePlot(self)
        # tab3: plot curves x(t) and y(t)
        self.twoPlots_xy = TwoPlots(self, "position")
        # tab4: plot curves Vx(t) and Vy(t)
        self.twoPlots_VxVy = TwoPlots(self, "velocity")
        # tab5: plot curves Ax(t) and Ay(t)
        self.twoPlots_AxAy = TwoPlots(self, "acceleration")
        # tab6: plot of f(t)=f(x(t), y(t), t)
        self.functionOfXY = FunctionPlot(self)
        # tab7: IPython shell
        self.pythonConsole = PythonConsole(self)

        self.tabs.addTab(self.imageTab,"Images visualisation")
        self.tabs.addTab(self.onePlot,"Trajectories")
        self.tabs.addTab(self.twoPlots_xy,"Positions")
        self.tabs.addTab(self.twoPlots_VxVy,"Velocities")
        self.tabs.addTab(self.twoPlots_AxAy,"Accelerations")
        self.tabs.addTab(self.functionOfXY,"Drawing tool")
        self.tabs.addTab(self.pythonConsole,"IPython")
        self.setCentralWidget(self.tabs)

        # Menu(s)
        self.menubar = self.menuBar()
        if platform.uname().system.startswith('Darw') :
            # Mac OS specificity:
            self.menubar.setNativeMenuBar(False)

        ###### Menu 'Files'
        fileMenu = self.menubar.addMenu('&Fichier')

        ### Open images directory:
        qa = QAction(QIcon(VideoTracker.icone_dir+'/open.png'),
                           'Ouvrir dossier images', self)
        qa.setShortcut('Ctrl+D')
        qa.setStatusTip("Ouvre un dossier contenant déjà "+\
                             "les images d'une vidéo")
        # connexion avec la méthode 'load_images_from_directory' qui est
        # définie dans l'objet 'imageTab' :
        qa.triggered.connect(self.imageTab.load_images_from_directory)
        fileMenu.addAction(qa)

        ### Load a video file :
        qa = QAction(QIcon(VideoTracker.icone_dir+'/open.png'),
                           "Charger un fichier vidéo", self)
        qa.setShortcut('Ctrl+O')
        qa.setStatusTip('Ouvre un fihier vidéo et le '+\
                             'découpe en images successives...')
        # connexion avec la méthode 'open_video' qui est définie dans
        # l'objet 'imageTab' :
        qa.triggered.connect(self.imageTab.open_video)
        fileMenu.addAction(qa)

        ### Export CSV:
        qa = QAction(QIcon(VideoTracker.icone_dir+'/exportCSV.png'),\
                          'Export CSV', self)
        qa.setStatusTip("Exporte les positions extraites de la vidéo dans un"+\
                        "fichier CSV.")
        qa.triggered.connect(self.ExportCSV)
        fileMenu.addAction(qa)

        ### Import CSV:
        qa = QAction(QIcon(VideoTracker.icone_dir+'/importCSV.png'),\
                          'Import CSV', self)
        qa.setStatusTip("Importe les données depuis un fichier CSV forgé par VideoTracker.")
        qa.triggered.connect(self.ImportCSV)
        fileMenu.addAction(qa)

        ### Quit :
        qa = QAction(QIcon(VideoTracker.icone_dir+'/exit.png'),\
                          'Quitter', self)
        qa.setShortcut('Ctrl+Q')
        qa.setStatusTip("Quitter l'application")
        qa.triggered.connect(self.close)
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
        qa = QAction('Dessiner la sélection couleur de la cible',
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
        self.twoPlots_xy.ClearAxes()
        self.twoPlots_VxVy.ClearAxes()
        self.twoPlots_AxAy.ClearAxes()
        self.functionOfXY.ClearAxes()

    def ImportCSV(self):
        '''Import Data from CSV file.'''

        # Lance un sélecteur de fichier pour choisir le fichier à écrire.'''
        fname = QFileDialog.getOpenFileName(self,
                                            'Choisir un nom de fichier CSV à importer',
                                            VideoTracker.csv_dir,
                                            'Fichier CSV (*.csv *.txt)')
        if fname[0] == "": return

        with open(fname[0], 'r', encoding="utf8") as F:
            data = F.readlines()

        if "VIDEOTRACKER MADE THIS FILE!" not in data[0]:
            rep = QMessageBox.critical(
                    None,        # QMessageBox parent widget
                    'Erreur',    # window bar
                    "Désolé, le fichier CSV <{}> n'a pas été\forgé par VideoTracker..."\
                    .format(os.path.basename(fname[0])), QMessageBox.Ok)
            return

        self.clearPlots()
        
        # Extract the meta-data dictionary and fill the field in the Image display:
        exec("self.imageTab.dico_video="+data[1].split('#')[1].strip())
        self.imageTab.parse_meta_data()
        self.imageTab.setTextInfoVideoGrid()

        # Extract the unit-scale dictionary and fill the field in the Image display:
        unit_data = data[2].split('#')[1].strip()
        exec("self.unit_dict={}".format(unit_data))
        print("self.unit_dict:",self.unit_dict)
        self.imageTab.scale_pixel.setText(str(self.unit_dict["pixels"]))
        self.imageTab.scale_mm.setText(str(self.unit_dict["mm"]))
        self.imageTab.scale_XY()
        self.imageTab.scaleInfoVisible(True)

        # Extract algo information:
        algo = data[3].split('#')[1].strip()
        try:
            index = ImageDisplay.algo_traj.index(algo)
        except:
            rep = QMessageBox.critical(
            None,        # QMessageBox parent widget
            'Erreur',    # window bar
            "L'information sur l'algorithme <{}> n'est pas reconnue".format(algo))
            return
        self.imageTab.btn_algo.setCurrentIndex(index)
        print('index:', index,
              'self.imageTab.btn_algo.currentText():',
              self.imageTab.btn_algo.currentText())
            
        # Extract RGB target color:
        RGB = data[4].split('#')[1].strip()
        print("self.target_RGB=np."+RGB)
        try:
            exec("self.target_RGB=np."+RGB)
        except:
            rep = QMessageBox.critical(
            None,        # QMessageBox parent widget
            'Erreur',    # window bar
            "L'information RGB <{}> n'est pas reconnue".format(RGB))
            return

        # Read the CSV file with pandas:
        self.csv_dataFrame = pandas.read_csv(fname[0],
                                             header=5,
                                             delimiter=';',
                                             encoding="utf8")
        data = self.csv_dataFrame.values
        data = [data[:,1], data[:,2], data[:,3]]
        self.target_pos = np.array(data)        
        self.imageTab.display_plots()

        # Clear display tab:
        self.imageTab.btn_algo.clear()
        self.imageTab.buttonsState(importCSV=True)
        self.imageTab.img_lbl.setPixmap(QPixmap())
        
        self.twoPlots_VxVy.reset()
        self.twoPlots_AxAy.reset()


    def ExportCSV(self):
        '''Export Data in a CSV file.'''
        if self.__target_pos is None :
            self.statusBar().showMessage("pas de données à exporter.")
            return

        # Lance un sélecteur de fichier pour choisir le fichier à écrire.'''
        video_name = self.imageTab.dico_video['videoname'].replace(".mp4","")
        cvs_name = os.path.join(VideoTracker.csv_dir, video_name)
        fname = QFileDialog.getSaveFileName(self,
                                            'Choisir un nom de fichier CSV à écrire',
                                            cvs_name,
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
        unit_dict = {"pixels": "?", "mm":"?"}
        scale = 1.
        if self.imageTab.valid_scale:
            xlabel, ylabel   = "X [mm]", "Y [mm]"
            xformat, yformat = "%10.6e", "%10.6e"
            unit_dict["pixels"] = float(self.imageTab.scale_pixel.text())
            unit_dict["mm"]     = float(self.imageTab.scale_mm.text())
            # retrieve scale
            scale = self.imageTab.pix_to_mm_coeff

        header = "VIDEOTRACKER MADE THIS FILE!\n"
        header += str(self.imageTab.dico_video)+"\n"
        header += str(unit_dict)+"\n"
        header += self.imageTab.btn_algo.currentText()+"\n"
        header += repr(self.target_RGB)+"\n"
        header += "{};{};{}; num image".format(tlabel, xlabel, ylabel)
        fmt = (tformat, xformat, yformat, "%d")
        data = []
        data.append(time)
        data.append((self.__target_pos[0]*scale).tolist())
        data.append((self.__target_pos[1]*scale).tolist())
        data.append(self.__target_pos[2].tolist())
        data = np.array(data)

        fileName = fname[0]
        if not fileName.endswith(".csv"): fileName += ".csv"
        np.savetxt(fileName, data.transpose(), delimiter=";",
                   header=header, fmt=fmt, encoding="utf8")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    VT  = VideoTracker()
    sys.exit(app.exec_())

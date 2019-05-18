#
# version 1.3 -- 2019-05-07 -- JLC --
#   add Export CVS
#

import cv2
from scipy.misc import imread
import numpy as np
import os

from PyQt5.QtWidgets import (QWidget, QPushButton, QComboBox,
                             QRubberBand, QLabel, QFrame,
                             QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLineEdit, QFileDialog, QMessageBox,
                             QSpinBox)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt,QEvent, QRect, QSize

from ProgressBar import ProgressBar

class staticproperty(property):
    """ Création du décorateur '@staticproperty'"""
    def __get__(self, cls, owner):
        return staticmethod(self.fget).__get__(None, owner)()

class ImageDisplay(QWidget):

    video_infos = ['vidéo','nb frames','taille','FPS','durée']
    algo_traj   = ['barycentre','minmax']

    def __init__(self, mainWindow):

        # appel du constructeur de la classe de base :
        QWidget.__init__(self, mainWindow)

        self.mw = mainWindow

        # Attributs (objets persistants)
        self.img_lbl = QLabel(self)           # affichage l'image courante
        self.img_lbl.installEventFilter(self) # filtre pour capter les événements
                                              # souris dans l'objet QLabel

        self.rubberBand  = QRubberBand(QRubberBand.Line, self)

        # Boutons pour avancer/reculer
        self.btn_prev  = QPushButton(QIcon("icones/go-prev.png"),  "", self)
        self.btn_next  = QPushButton(QIcon("icones/go-next.png"), "", self)
        self.btn_first = QPushButton(QIcon("icones/go-first.png"),  "", self)
        self.btn_last  = QPushButton(QIcon("icones/go-last.png"), "", self)
        self.btn_traj  = QPushButton(QIcon("icones/extract.png"),
                                     "Extraire...", self)
        self.btn_clear = QPushButton(QIcon("icones/clear.png"),
                                     "Effacer courbes...", self)
        self.__btn_exportCSV = QPushButton(QIcon("icones/csv.png"),
                                           "Export CSV", self)
        self.btn_algo  = QComboBox(self)

        self.video_path     = None  # Chemin de la dernière vidéo
        self.images_dir     = None  # Dossier contenant les images
        self.img_idx        = None  # Rang de l'image affichée
        self.img_path       = None  # nom du chemin de l'image courante
        self.nb_img         = None  # nombre d'images

        self.video_name     = None  # nom de la video ("aaaaaa.mp4")
        self.video_nframes  = None  # nombre d'images dans la video
        self.video_size     = None  # taille (width, height) des images
        self.video_FPS      = None  # nombre d'images par seconde
        self.video_duration = None  # durée de la video en secondes
        self.videoLabels    = []    # liste de QLabel contenant les infos vidéo
        self.dico_video     = {}    # dictionnaire des méta-données

        self.scale_pixel    = None  # nombre de pixels pour conversion en mm
        self.scale_mm       = None  # nbre de mm pour scale_pixel

        self.lbl_epsilon    = None  # label epsilon
        self.epsi_spin      = None  # boite de choix de epsilon
    
        self.valid_scale    = False # données de l'échelle valides ou pas
        self.pix_to_mm_coeff= None  # le coefficient de converion pixels -> mm
        self.dicoScale      = {}    # dictionnaire des QWidget d'info scale

        # créer l'onglet de visualisation image """
        self.__initUI()
        self.__scaleInfoVisible(False)
        self.__epsilonVisible(False)

    def __initUI(self):
        # Onglet "Visualisation images"
        vbox = QVBoxLayout()

        # Ligne 1 : extraction trajec
        ligne1 = QHBoxLayout()
        ligne1.addStretch(1)
        ligne1.addWidget(self.btn_algo)
        ligne1.addWidget(self.btn_traj)
        ligne1.addWidget(self.btn_clear)
        ligne1.addWidget(self.__btn_exportCSV)
        ligne1.addStretch(1)

        # Ligne 2 : infos video + visu image
        ligne2 = QHBoxLayout()

        # boîte d'infos sur la vidéo
        infoVBox = QVBoxLayout()
        for i, name  in enumerate(ImageDisplay.video_infos):
            label = QLabel(self)
            label.setFrameStyle(QFrame.StyledPanel | QFrame.Plain);
            infoVBox.addWidget(label)
            self.videoLabels.append(label)
        infoVBox.addStretch()

        widget = QLabel("Conversion pixels -> mm", self)
        self.dicoScale['Pixels-mm'] = widget
        infoVBox.addWidget(widget)

        grid = QGridLayout()
        infoVBox.addLayout(grid)

        widget = QLabel("pixels  ",self)
        self.dicoScale['pixels'] = widget
        grid.addWidget(widget,1,1)

        self.scale_pixel = QLineEdit(self)
        self.dicoScale['pixelsForMM'] = self.scale_pixel
        grid.addWidget(self.scale_pixel,1,2)

        widget = QLabel("millimètres ",self)
        self.dicoScale['millimeters'] = widget
        grid.addWidget(widget,2,1)

        self.scale_mm = QLineEdit(self)
        self.dicoScale['mmForPixels'] = self.scale_mm
        grid.addWidget(self.scale_mm,2,2)

        self.lbl_epsilon = QLabel("Epsilon ",self)
        grid.addWidget(self.lbl_epsilon,5,1)

        self.epsi_spin = QSpinBox(self)
        self.epsi_spin.setRange(1,50)
        self.epsi_spin.setSingleStep(1)
        self.epsi_spin.setValue(5)
        grid.addWidget(self.epsi_spin,5,2)
        
        infoVBox.addStretch()

        ligne2.addLayout(infoVBox)
        ligne2.addStretch(1)
        ligne2.addWidget(self.img_lbl) # le QLabel por afficher l'image
        ligne2.addStretch(1)

        # Ligne 3 : boutons de navigation
        ligne3 = QHBoxLayout()
        ligne3.addStretch(1)
        ligne3.addWidget(self.btn_first)
        ligne3.addWidget(self.btn_prev)
        ligne3.addWidget(self.btn_next)
        ligne3.addWidget(self.btn_last)
        ligne3.addStretch(1)

        vbox.addLayout(ligne1)
        vbox.addStretch(1)
        vbox.addLayout(ligne2)
        vbox.addStretch(1)
        vbox.addLayout(ligne3)

        self.setLayout(vbox)

        self.__buttonsStateAndConnect()
        self.__setVideoLabelVisible(False)

    def __setVideoLabelVisible(self, state):
        for label in self.videoLabels:
            label.setVisible(state)

    def __buttonsStateAndConnect(self):

        self.btn_traj.setEnabled(False)
        self.btn_traj.setStatusTip('Extrait la trajectoire de la cible'+
            'dont la couleur a été choisie')
        self.btn_traj.clicked.connect(self.extract_trajectoire)

        self.btn_clear.setEnabled(False)
        self.btn_clear.setStatusTip('Nettoye tous les tracés des onglets'+
            '<trajectoire> et <X(t), Y(t)>')
        self.btn_clear.clicked.connect(self.mw.clearPlots)

        self.__btn_exportCSV.clicked.connect(self.mw.ExportCSV)
        self.__btn_exportCSV.setEnabled(False)
        texte = "Export des données dans un fichier CSV"
        self.__btn_exportCSV.setStatusTip(texte)

        self.btn_algo.addItems(ImageDisplay.algo_traj)
        self.btn_algo.setEnabled(False)

        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_prev.setEnabled(False)
        self.btn_prev.setStatusTip("affiche l'image précédente")

        self.btn_next.clicked.connect(self.next_image)
        self.btn_next.setEnabled(False)
        self.btn_next.setStatusTip("affiche l'image suivante")

        self.btn_first.clicked.connect(self.first_image)
        self.btn_first.setEnabled(False)
        self.btn_first.setStatusTip("affiche la première image")

        self.btn_last.clicked.connect(self.last_image)
        self.btn_last.setEnabled(False)
        self.btn_last.setStatusTip("affiche la dernière image")

    def __setTextInfoVideoGrid(self):
        keys  = ['videoname','nframes','size','fps','duration']

        for field, name, key in zip(self.videoLabels,
                                    ImageDisplay.video_infos,
                                    keys):
            mess = name +' : '+str(self.dico_video.get(key,'?'))
            field.setText(mess)
        self.__setVideoLabelVisible(True)            

    def __scaleInfoVisible(self, state):
        for widget in self.dicoScale.values():
            widget.setVisible(state)

    def __epsilonVisible(self, state):
        self.lbl_epsilon.setVisible(state)
        self.epsi_spin.setVisible(state)

    def open_video(self):
        '''Lance un sélecteur de fichier pour choisir la vidéo à traiter.'''
        fname = QFileDialog.getOpenFileName(None,
                                            'Choisir une vidéo',
                                            self.mw.cur_dir,
                                            'Fichier vidéo (*.mp4)')
        if fname[0]  != '' :
            # un fichier vidéo a été chosi :
            vp = fname[0]
            if self.video_path == vp :
                name = os.path.basename(vp)
                rep = QMessageBox.question(self,        # widget parent de QMessageBox
                    'Question',                     # texte du bandeau de la fenêtre
                    'Voulez-vous recharger le fichier video {} ?'.format(name),
                    QMessageBox.Yes | QMessageBox.No,   # afficher les boutons Yes et No
                    QMessageBox.No)                     # bouton No sélectionné par défaut
                if rep == QMessageBox.No: return
            # fichier vidéo à traiter => faire le split des images :
            self.video_path = vp
            self.extract_images_from_video()



    def load_images_from_directory(self):
        '''Charge les images '*.png' contenue dans le répertoire
           des images choisi avec un sélecteur graphique.'''

        # Choix du répertoire avec un sélecteur de fichier :
        dname = QFileDialog.getExistingDirectory(None,
                                                 'Choisir un dossier images',
                                                 self.mw.image_dir)
        if dname != '' :
            # un répertoire valide a été choisi :
            self.video_path = None
            self.images_dir = dname + "/"

            try:
                # Lecture du fichier ascii des méta-données
                with open(self.images_dir + "metaData.txt", "r") as F:
                    data = F.read()
                exec('self.dico_video = '+data)
            except:
                rep = QMessageBox.critical(
                    None,             # widget parent de QMessageBox
                    'Erreur',    # bandeau de la fenêtre
                    'Pas de fichier de méta-données dans le répertoire'+\
                    ' <{}>'.format(os.path.basename(dname)),
                    QMessageBox.Ok)
                return



            print("méta données :", self.dico_video)

            self.parse_meta_data()
            self.__setTextInfoVideoGrid()

            # Mettre à jour l'application avec les nouvelles images chargées :
            self.update_images()


    def extract_trajectoire(self):
        '''Méthode utilisée pour extraire la trajectoire du centre de la
           cible pour toutes les images de la vidéo.'''

        # Récupérer l'algorithme de calcul du centre de la cible :
        algo = self.btn_algo.currentText()

        # Définition de la liste dans laquelle on va récupérer les coordonnées
        # du centre cible pour toutes les images :
        target_pos = []

        # Création d'un objet ProgressBar qui va lancer le travail
        # d'extraction de la cible dans les images tout en affichant une
        # barre d'avancement :
        pg = ProgressBar(self.images_dir, self)
        pg.configure_for_target_extraction(self.mw.target_RGB,
                                           algo,
                                           self.epsi_spin.value(),
                                           target_pos)
        ret = pg.exec_() # lance la barre et le travail d'extraction...
        print("retour de pg.exec_() :",ret)

        target_pos = np.array(target_pos)
        width, height = self.video_size
        # l'axe verticale est retourné et decalé:
        target_pos[1] = height - target_pos[1]
        self.scale_XY(target_pos)

        self.mw.target_pos = target_pos
        self.mw.clearPlots()
        
        # tracer la courbe (X(t), Y(t)) :
        self.mw.onePlot.setEnabled(True)
        self.mw.onePlot.Plot()

        # tracer les trajectoires X(t) et Y(t)
        self.mw.twoPlots.setEnabled(True)
        self.mw.tabs.setCurrentWidget(self.mw.twoPlots)
        self.mw.twoPlots.Plot()

        # remettre le bouton extraire_trajectoire disabled:
        self.btn_traj.setEnabled(False)
        self.btn_algo.setEnabled(False)
        self.__btn_exportCSV.setEnabled(True)

    def extract_images_from_video(self) :
        # nom du fichier video, sans chemin d'accès ni suffixe '.mp4' :
        videoname = os.path.basename(self.video_path)[:-4]

        # répertoire pour stocker les images :
        self.images_dir = self.mw.image_dir + videoname + "/"

        if os.path.isdir(self.images_dir) :
            print("Effacement de tous les fichiers de '{}'"\
                  .format(self.images_dir))
            for fn in os.listdir(self.images_dir) :
                os.remove(self.images_dir+fn)
        else :
            os.mkdir(self.images_dir)

        video = cv2.VideoCapture(self.video_path)
        
        self.dico_video['nframes']   = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.dico_video['size']      = (int(video.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                        int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)))    
        self.dico_video['fps']       = int(video.get(cv2.CAP_PROP_FPS))
        self.dico_video['duration']  = video.get(cv2.CAP_PROP_FRAME_COUNT)/video.get(cv2.CAP_PROP_FPS)
        self.dico_video['videoname'] = os.path.basename(self.video_path)
                                            
        self.parse_meta_data()
        self.dico_video["videoname"] = videoname+".mp4"
        self.__setTextInfoVideoGrid()

        

        # Création d'un objet ProgressBar qui va lancer le travail
        # d'extraction des images tout en affichant une barre d'avancement :
        pg = ProgressBar(self.images_dir, self)
        pg.configure_for_video_extraction(video, self.mw.image_fmt)
        ret = pg.exec_()
        print("retour de pg.exec_() :", ret)

        # MAJ de la liste des fichiers images :
        self.update_images()

        # écriture des méta-data dans le fichier 'nom_video'.info
        with open(self.mw.image_dir+videoname+"/metaData.txt", "w") as F:
            F.write(str(self.dico_video))

    def computeTargetColor(self, draw_selection=False):
        col_min,row_min,col_max,row_max = self.selection.getCoords()
        print("Pixels selectionnés : lignes [{},{}] colonnes [{},{}]".\
              format(row_min, row_max, col_min, col_max))

        tab = imread(self.img_path)
        self.target_pix = tab[row_min:row_max+1, col_min:col_max+1, :]
        R = round(self.target_pix[:,:,0].mean())
        G = round(self.target_pix[:,:,1].mean())
        B = round(self.target_pix[:,:,2].mean())
        self.mw.target_RGB = np.array([R, G, B], dtype=int)
        print("RGB sélection dans <{}> :".format(os.path.basename(self.img_path)),
              self.mw.target_RGB)

        if draw_selection:
            tab[row_min, col_min:col_max+1, :] = 255 - tab[row_min, col_min:col_max+1, :]
            tab[row_max, col_min:col_max+1, :] = 255 - tab[row_max, col_min:col_max+1, :]
            tab[row_min:row_max+1, col_min, :] = 255 - tab[row_min:row_max+1, col_min, :]
            tab[row_min:row_max+1, col_max, :] = 255 - tab[row_min:row_max+1, col_max, :]

            # écraser le fichier image avec la nouvelle image et afficher
            cv2.imwrite(self.img_path, tab)
            self.show_image()

        self.btn_traj.setEnabled(True)
        self.btn_algo.setEnabled(True)
        self.btn_clear.setEnabled(True)


    def update_images(self) :
        '''Méthode à exécuter quand de nouvelles images sont apparues
           après une extraction d'images depuis une vidéo par exemple.
           Cette méthode :
           - met à jour des attributs qui dépendant de la liste des images,
           - met à jour l'état de certains boutons
           - fait afficher la première image et un message d'information.'''

        if self.images_dir is None :
            self.img_idx = None
            self.btn_prev.setEnabled(False)
            self.btn_prev.setStatusTip("")
            self.btn_next.setEnabled(False)
            self.btn_next.setStatusTip("")
        else :
            # liste des noms des fichiers image pour avoir leur nombre :
            file_names = [ f for f in os.listdir(self.images_dir) \
                           if f.endswith('.png')]
            self.nb_img = len(file_names)

            # MAJ des boutons prev et next
            self.img_idx = 1
            self.btn_prev.setEnabled(False)
            self.btn_last.setEnabled(False)

            self.btn_prev.setStatusTip("charge l'image précédente")

            self.btn_next.setEnabled(True)
            self.btn_last.setEnabled(True)
            self.btn_next.setStatusTip("afficher "+self.mw.image_fmt.format(2))

            self.show_image()
            self.__scaleInfoVisible(True)
            self.__epsilonVisible(True)
            self.mw.tabs.setCurrentWidget(self)

            self.scale_mm.clear()
            self.scale_mm.setText("???")
            self.scale_pixel.clear()
            try:
                text = str(self.video_size[1])
            except:
                text = ""
            self.scale_pixel.setText(text)

            if self.mw.flags["displayInfo"]:
                rep = QMessageBox.information(
                    None,             # widget parent de QMessageBox
                    'Information',    # bandeau de la fenêtre
                    'Vous pouvez maintenant sélectionner une couleur de cible'+\
                    'avec la souris...',
                    QMessageBox.Ok)

    def show_image(self) :
        '''Affiche l'image dont le numéro est donné par l'attribut 'img_idx'.'''
        if self.img_idx is None :
            self.img_path = ''
        else :
            self.img_path = self.images_dir+self.mw.image_fmt.format(self.img_idx)
        pixmap = QPixmap(self.img_path)
        self.img_lbl.setPixmap(pixmap)
        self.img_lbl.setStatusTip(os.path.basename(self.img_path))

    def first_image(self) :
        if self.img_idx == None : return
        self.img_idx = 1

        # MAJ du bouton next
        self.btn_next.setEnabled(True)
        self.btn_last.setEnabled(True)
        tip = "afficher "+self.mw.image_fmt.format(self.img_idx+1)
        self.btn_next.setStatusTip(tip)  # MAJ statusTip btn next
        # première image ! désactiver btn prev et vider statusTip
        self.btn_prev.setEnabled(False)
        self.btn_first.setEnabled(False)
        tip = ""
        self.btn_prev.setStatusTip(tip)
        self.mw.statusBar().showMessage(tip) # rafraîchir statusBar
        self.show_image()

    def prev_image(self) :
        if self.img_idx == None : return
        self.img_idx -= 1

        # MAJ du bouton next
        self.btn_next.setEnabled(True)
        self.btn_last.setEnabled(True)

        tip = "afficher "+self.mw.image_fmt.format(self.img_idx+1)
        self.btn_next.setStatusTip(tip)  # MAJ statusTip btn next
        if self.img_idx == 1 :
            # première image ! désactiver btn prev et vider statusTip
            self.btn_prev.setEnabled(False)
            self.btn_first.setEnabled(False)
            tip = ""
            self.btn_prev.setStatusTip(tip)
        else :
            self.btn_first.setEnabled(True)
            tip = "afficher "+self.mw.image_fmt.format(self.img_idx-1)
            self.btn_prev.setStatusTip(tip) # MAJ statusTip btn prev
        self.mw.statusBar().showMessage(tip) # rafraîchir statusBar
        self.show_image()

    def last_image(self) :
        if self.img_idx == None : return
        self.img_idx = self.nb_img # index de la dernière image

        # MAJ du bouton previous
        self.btn_first.setEnabled(True)
        self.btn_prev.setEnabled(True)
        tip = "afficher "+self.mw.image_fmt.format(self.img_idx-1)
        self.btn_prev.setStatusTip(tip)    # MAJ statusTip btn prev
        # dernière image : désactiver btn next
        self.btn_next.setEnabled(False)
        self.btn_last.setEnabled(False)
        tip = ""
        self.btn_next.setStatusTip(tip)
        self.mw.statusBar().showMessage(tip)     # rafraîchir statusBar
        self.show_image()

    def next_image(self) :
        if self.img_idx == None : return
        self.img_idx += 1

        # MAJ du bouton previous
        self.btn_prev.setEnabled(True)
        self.btn_first.setEnabled(True)
        tip = "afficher "+self.mw.image_fmt.format(self.img_idx-1)
        self.btn_prev.setStatusTip(tip)    # MAJ statusTip btn prev
        if self.img_idx == self.nb_img :
            # dernière image : désactiver btn next
            self.btn_next.setEnabled(False)
            self.btn_last.setEnabled(False)
            tip = ""
            self.btn_next.setStatusTip(tip)
        else :
            self.btn_next.setEnabled(True)
            self.btn_last.setEnabled(True)
            tip = "afficher "+self.mw.image_fmt.format(self.img_idx+1)
            self.btn_next.setStatusTip(tip) # MAJ statusTip btn prev
        self.mw.statusBar().showMessage(tip)     # rafraîchir statusBar
        self.show_image()

    def parse_meta_data(self):
        self.video_nframes  = self.dico_video.get('nframes', None)
        self.video_size     = self.dico_video.get('size', None)
        self.video_FPS      = self.dico_video.get('fps', None)
        self.video_duration = self.dico_video.get('duration', None)
        self.video_name     = self.dico_video.get('videoname',"none.mp4")

        if self.mw.flags["debug"]:
            info= " nb images    : {},\n taille image : {},\n FPS : {} image/sec,\n durée : {} sec."
            info = info.format(self.video_nframes,
                               self.video_size,
                               self.video_FPS,
                               self.video_duration)
            QMessageBox.about(None,     # widget parent de QMessageBox
                              'Informations video {}'.format(self.video_name),
                              info)


    def eventFilter(self, object, event):
        if object == self.img_lbl :
            if event.type() == QEvent.MouseButtonPress:
                self.mousePressInLabel(event)
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                self.mouseReleaseInLabel(event)
                return True
            elif event.type() == QEvent.MouseMove:
                self.mouseMoveInLabel(event)
                return True
        return False

    def mousePressInLabel(self, event):
        if event.button() == Qt.LeftButton:
            self.pt1 = event.pos()
            self.pt1_rect = self.img_lbl.mapTo(self, self.pt1)
            print("\nCoord. pt1 image :",self.pt1)
            self.rubberBand.setGeometry(QRect(self.pt1_rect, QSize()))
            self.rubberBand.show()
            self.mw.statusBar().showMessage('sélection en cours....')

    def mouseMoveInLabel(self, event):
        if not self.pt1.isNull():
            pt = self.img_lbl.mapTo(self,event.pos())
            self.rubberBand.setGeometry(QRect(self.pt1_rect, pt).normalized())

    def mouseReleaseInLabel(self, event):
        if event.button() == Qt.LeftButton:
            self.pt2 = event.pos()
            print("Coord. pt2 image :", self.pt2)
            self.rubberBand.hide()
            self.selection = QRect(self.pt1, self.pt2).normalized()
            print(self.selection)
            self.computeTargetColor()


    def scale_XY(self, target_pos):

        self.valid_scale = False
        try :
            pixels = float(self.scale_pixel.text())
            mm     = float(self.scale_mm.text())
        except :
            if self.mw.flags["displayInfo"]:
                info = 'Les données de conversion Pixels -> mm n\'ont pas été '
                info += 'complétées.. les ordonnées des tracés seront en pixels.'
                rep = QMessageBox.information(None,  # parent de QMessageBox
                        'Info',               # bandeau de la fenêtre
                        info, QMessageBox.Ok)
            return
        self.valid_scale = True
        self.pix_to_mm_coeff = mm/pixels
        print("valid sacle : ", self.pix_to_mm_coeff)
        target_pos *= self.pix_to_mm_coeff



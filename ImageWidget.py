#
# version 1.3 -- 2019-05-07 -- JLC --
#   add Export CVS
#

import cv2

import scipy
if scipy.__version__ < "1.3":
    from scipy.misc import imread
else:
    import imageio
    from imageio import imread
    
import numpy as np
import os

from PyQt5.Qt import (QWidget, QPushButton, QComboBox, QRubberBand, QLabel, QFrame,
                      QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QFileDialog,
                      QMessageBox, QSpinBox, QIcon, QPixmap, QPainter, QPen,
                      Qt,QEvent, QRect, QSize, QColor)

from ProgressBar import ProgressBar

class staticproperty(property):
    """ Création du décorateur '@staticproperty'"""
    def __get__(self, cls, owner):
        return staticmethod(self.fget).__get__(None, owner)()

class ImageDisplay(QWidget):

    video_infos     = ['vidéo : {}','nb frames : {}','taille : {}','FPS : {}','durée : {:.2f} sec']
    video_keys      = ['videoname','nframes','size','fps','duration']
    algo_traj       = ['barycentre','minmax']

    def __init__(self, mainWindow):

        # acall the base class constructor:
        super().__init__(mainWindow)

        self.mw = mainWindow

        # Attributs (objets persistants)
        self.img_lbl = QLabel(self)           # to display the current image
        self.img_lbl.installEventFilter(self) # filter to catch evenements
        self.selectTargetRect = None          # display a rectangle to show teh target color selection

        self.rubberBand  = QRubberBand(QRubberBand.Line, self)

        # Boutons pour avancer/reculer
        self.btn_prev  = QPushButton(QIcon("icones/go-prev.png"),  "", self)
        self.btn_next  = QPushButton(QIcon("icones/go-next.png"), "", self)
        self.btn_first = QPushButton(QIcon("icones/go-first.png"),  "", self)
        self.btn_last  = QPushButton(QIcon("icones/go-last.png"), "", self)
        self.btn_traj  = QPushButton(QIcon("icones/extract.png"), "Extraire...", self)
        self.btn_clear = QPushButton(QIcon("icones/clear.png"), "Effacer courbes...", self)
        self.btn_exportCSV = QPushButton(QIcon("icones/exportCSV.png"), "Export CSV", self)
        self.btn_algo      = QComboBox(self)
        self.image_index   = QLabel(self)
        
        # widget QSpinBox
        self.images_step      = QSpinBox(parent=self)
        self.images_firstRank = QSpinBox(parent=self) 
        self.images_lastRank  = QSpinBox(parent=self) 

        # QLabel to display the target color
        self.target_color_label = QLabel("target color",parent=self) 
        self.picked_color       = QLabel(self)
    
        self.video_path     = None  # Chemin de la dernière vidéo
        self.images_dir     = None  # Dossier contenant les images
        self.__img_idx      = None  # Rang de l'image affichée
        self.img_path       = None  # nom du chemin de l'image courante
        self.nb_img         = None  # nombre d'images

        self.video_name     = None  # nom de la video ("aaaaaa.mp4")
        self.video_nframes  = None  # nombre d'images dans la video
        self.video_size     = None  # taille (width, height) des images
        self.video_FPS      = None  # nombre d'images par seconde
        self.video_duration = None  # durée de la video en secondes
        self.videoLabels    = []    # liste de QLabel contenant les infos vidéo
        self.dico_video     = {}    # dictionnaire des méta-données

        self.dico_unit      = {}    # dictionary "pixels", "mm"
        self.scale_pixel    = None  # nombre de pixels pour conversion en mm
        self.scale_mm       = None  # nbre de mm pour scale_pixel
        self.valid_scale    = False # données de l'échelle valides ou pas
        self.pix_to_mm_coeff= 1.    # le coefficient de converion pixels -> mm
        self.dicoScale      = {}    # dictionnaire des QWidget d'info scale

        self.lbl_epsilon    = None  # label epsilon
        self.epsi_spin      = None  # boite de choix de epsilon    

        # créer l'onglet de visualisation image """
        self.__initUI()
        self.scaleInfoVisible(False)
        self.__epsilonVisible(False)

    def __initUI(self):

        # Onglet "Visualisation images"
        vbox = QVBoxLayout()

        # Ligne 1 : extraction trajec
        self.picked_color.setFrameStyle(QFrame.StyledPanel | QFrame.Plain);
        
        line1 = QHBoxLayout()
        line1.addStretch(1)
        line1.addWidget(self.btn_algo)
        line1.addWidget(self.btn_traj)
        line1.addWidget(self.target_color_label)
        line1.addWidget(self.picked_color)
        line1.addWidget(self.btn_clear)
        line1.addWidget(self.btn_exportCSV)
        line1.addStretch(1)

        # Ligne 2 : infos video + visu image
        line2 = QHBoxLayout()

        # boîte d'infos sur la vidéo
        infoVBox = QVBoxLayout()
        for _ in ImageDisplay.video_infos:
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
        self.epsi_spin.setValue(10)
        grid.addWidget(self.epsi_spin,5,2)
        
        infoVBox.addStretch()

        line2.addLayout(infoVBox)
        line2.addStretch(1)
        line2.addWidget(self.img_lbl) # le QLabel por afficher l'image
        line2.addStretch(1)

        # line 3 : navigation boutons
        self.image_index.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.image_index.setText("       ")
        line3 = QHBoxLayout()
        line3.addStretch(1)
        line3.addWidget(self.btn_first)
        line3.addWidget(self.btn_prev)
        line3.addWidget(self.image_index)
        line3.addWidget(self.btn_next)
        line3.addWidget(self.btn_last)
        line3.addStretch(1)

        # line 4 : first , step, last image selection
        line4 = QHBoxLayout()
        line4.addStretch(1)
        line4.addWidget(self.images_firstRank)
        line4.addWidget(self.images_step)
        line4.addWidget(self.images_lastRank)
        line4.addStretch(1)

        vbox.addLayout(line1)
        vbox.addStretch(1)
        vbox.addLayout(line2)
        vbox.addStretch(1)
        vbox.addLayout(line3)
        vbox.addLayout(line4)

        self.setLayout(vbox)

        self.buttonsState()
        self.__buttonsConnect()
        self.__setVideoLabelVisible(False)

    def __setVideoLabelVisible(self, state):
        for label in self.videoLabels:
            label.setVisible(state)

    def __buttonsConnect(self):            
        self.btn_traj.clicked.connect(self.extract_trajectoire)
        self.btn_clear.clicked.connect(self.mw.clearPlots)
        self.btn_exportCSV.clicked.connect(self.mw.ExportCSV)
        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_next.clicked.connect(self.next_image)
        self.btn_first.clicked.connect(self.first_image)
        self.btn_last.clicked.connect(self.last_image)
        self.images_step.valueChanged.connect(self.__step_changed)
        self.images_firstRank.valueChanged.connect(self.__first_rank_changed)
        self.images_lastRank.valueChanged.connect(self.__last_rank_changed)

    def buttonsState(self, importCSV=False):

        self.btn_traj.setEnabled(False)
        self.picked_color.setText("X")
        self.picked_color.setEnabled(False)
        
        self.btn_traj.setStatusTip('Extrait la trajectoire de la cible'+
            'dont la couleur a été choisie')

        self.target_color_label.setEnabled(False)
        self.picked_color.setStyleSheet('background-color : rgb(255, 255, 255)')
        
        self.btn_clear.setEnabled(False)
        self.btn_clear.setStatusTip('Nettoye tous les tracés des onglets'+
            '<trajectoire> et <X(t), Y(t)>')

        self.btn_exportCSV.setEnabled(False)
        texte = "Export des données dans un fichier CSV"
        self.btn_exportCSV.setStatusTip(texte)

        if not importCSV: self.btn_algo.addItems(ImageDisplay.algo_traj)
        self.btn_algo.setEnabled(False)

        self.btn_prev.setEnabled(False)
        self.btn_prev.setStatusTip("affiche l'image précédente")

        self.btn_next.setEnabled(False)
        self.btn_next.setStatusTip("affiche l'image suivante")

        self.btn_first.setEnabled(False)
        self.btn_first.setStatusTip("affiche la première image à traiter")

        self.btn_last.setEnabled(False)
        self.btn_last.setStatusTip("affiche la dernière image à traiter")

        # SpinBoxes parameters:
        self.images_step.setRange(1,1000)
        self.images_step.setSingleStep(1)
        self.images_step.setValue(1)
        self.images_step.setPrefix("step: ")
        self.images_step.setEnabled(False)
        self.images_step.setStatusTip("Fixe le pas pour passer d'une image à l'autre")
        
        self.images_firstRank.setRange(1,1000)
        self.images_firstRank.setSingleStep(1)
        self.images_firstRank.setValue(1)
        self.images_firstRank.setPrefix("first: ")
        self.images_firstRank.setEnabled(False)
        self.images_firstRank.setStatusTip("Fixe le rang de la première image à traiter")
        
        self.images_lastRank.setRange(1,10000)
        self.images_lastRank.setSingleStep(1)
        self.images_lastRank.setValue(1)
        self.images_lastRank.setPrefix("last: ")
        self.images_lastRank.setEnabled(False)
        self.images_lastRank.setStatusTip("Fixe le rang de la dernière image à traiter")

    def __first_rank_changed(self, val):
        if self.img_idx is None: return
        if self.img_idx < val:
            self.img_idx = val
            self.show_image()
            
    def __last_rank_changed(self, val):
        if self.img_idx is None: return
        if self.img_idx > val:
            self.img_idx = val
            self.show_image()

    def __step_changed(self, val):
        if self.img_idx is None: return

    def setTextInfoVideoGrid(self):
        
        for field, name, key in zip(self.videoLabels,
                                    ImageDisplay.video_infos,
                                    ImageDisplay.video_keys):
            mess = name.format(self.dico_video.get(key,'?'))
            field.setText(mess)
        self.__setVideoLabelVisible(True)            

    def scaleInfoVisible(self, state):
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
            self.setTextInfoVideoGrid()

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
        
        first = self.images_firstRank.value()
        last  = self.images_lastRank.value()
        step  = self.images_step.value()
        
        last = last - (last - first) % step
        first_last_step = (first, last, step)
        pg = ProgressBar(self.images_dir, self)
        pg.configure_for_target_extraction(self.mw.target_RGB,
                                           algo,
                                           self.epsi_spin.value(),
                                           target_pos,
                                           first_last_step)
        ret = pg.exec_() # lance la barre et le travail d'extraction...
        print("retour de pg.exec_() :",ret)

        if ret != 0:
            self.mw.target_pos = None
            return

        target_pos = np.array(target_pos)
        width, height = self.video_size
        # l'axe verticale est retourné et decalé:
        target_pos[1] = height - target_pos[1]
        self.scale_XY()

        self.mw.target_pos = target_pos
        self.display_plots()
        
        # remettre le bouton extraire_trajectoire disabled:
        self.btn_exportCSV.setEnabled(True)

    def display_plots(self):
        self.mw.clearPlots()
        
        # Plot trajectory (X(t), Y(t)) :
        self.mw.onePlot.setEnabled(True)
        self.mw.onePlot.Plot()

        # Plot curves X(t) and Y(t)
        self.mw.twoPlots_xy.setEnabled(True)
        self.mw.tabs.setCurrentWidget(self.mw.twoPlots_xy)
        self.mw.twoPlots_xy.Plot()

        # Plot curves VX(t) and VY(t)
        self.mw.twoPlots_VxVy.setEnabled(True)
        self.mw.tabs.setCurrentWidget(self.mw.twoPlots_xy)
        self.mw.twoPlots_VxVy.Plot()

        # Plot curves AX(t) and AY(t)
        self.mw.twoPlots_AxAy.setEnabled(True)
        self.mw.tabs.setCurrentWidget(self.mw.twoPlots_xy)
        self.mw.twoPlots_AxAy.Plot()


    def extract_images_from_video(self) :
        # name of the video file without path and suffix:
        videoname = os.path.basename(self.video_path)[:-4]

        # directory where to put extracted iamges:
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
        self.setTextInfoVideoGrid()

        # Création d'un objet ProgressBar qui va lancer le travail
        # d'extraction des images tout en affichant une barre d'avancement :
        pg = ProgressBar(self.images_dir, self)
        pg.configure_for_video_extraction(video, self.mw.image_fmt)
        ret = pg.exec_()
        print("retour de pg.exec_() :", ret)
        if ret != 0: return

        # MAJ de la liste des fichiers images :
        self.update_images()

        # écriture des méta-data dans le fichier 'nom_video'.info
        with open(self.mw.image_dir+videoname+"/metaData.txt", "w") as F:
            F.write(str(self.dico_video))

    def computeTargetColor(self, draw_selection=False):
        col_min,row_min,col_max,row_max = self.selection.getCoords()
        print(f"Pixels selectionnés : lignes [{row_min},{row_max}] colonnes [{col_min},{col_max}]")

        tab = imread(self.img_path)
        self.target_pix = tab[row_min:row_max+1, col_min:col_max+1, :]
        R = round(self.target_pix[:,:,0].mean())
        G = round(self.target_pix[:,:,1].mean())
        B = round(self.target_pix[:,:,2].mean())
        self.mw.target_RGB = np.array([R, G, B], dtype=int)
        print("RGB sélection dans <{}> :".format(os.path.basename(self.img_path)),
              self.mw.target_RGB)

        draw_selection = self.mw.flags["drawTargetSelection"]
        if draw_selection:
            self.show_image()
            print("drawTargetSelection")
            #if self.selectTargetRect is not None : del self.selectTargetRect
            # create painter instance with pixmap
            self.selectTargetRect = QPainter(self.img_lbl.pixmap())

            # set rectangle color and thickness
            self.penRectangle = QPen(QColor(0,0,0))
            self.penRectangle.setWidth(2)

            # draw rectangle on painter
            self.selectTargetRect.begin(self)
            self.selectTargetRect.setPen(self.penRectangle)
            self.selectTargetRect.drawRect(col_min,row_min,
                                          col_max-col_min,row_max-row_min)
            self.selectTargetRect.setOpacity(0.1)
            self.selectTargetRect.end()
            #self.show_image()

        self.btn_traj.setEnabled(True)
        self.btn_algo.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.target_color_label.setEnabled(True)
        self.picked_color.setStyleSheet('background-color : rgb({},{},{})'.format(R, G, B))

    @property
    def img_idx(self): return self.__img_idx

    @img_idx.setter
    def img_idx(self, index):
        self.__img_idx = index
        self.image_index.setText(str(index))
                                 
    def update_images(self) :
        '''Méthode à exécuter quand de nouvelles images sont apparues
           après une extraction d'images depuis une vidéo par exemple.
           Cette méthode :
           - met à jour des attributs qui dépendant de la liste des images,
           - met à jour l'état de certains boutons
           - fait afficher la première image et un message d'information.'''

        if self.images_dir is None :
            self.__img_idx = None
            #self.btn_prev.setEnabled(False)
            self.btn_prev.setStatusTip("")
            #self.btn_next.setEnabled(False)
            self.btn_next.setStatusTip("")
            self.images_step.setEnabled(False)
            self.images_firstRank.setEnabled(False)
            self.images_lastRank.setEnabled(False)
            
        else :
            self.buttonsState()
            self.mw.clearPlots()
            self.mw.twoPlots_VxVy.reset()
            
            # liste des noms des fichiers image pour avoir leur nombre :
            file_names = [ f for f in os.listdir(self.images_dir) \
                           if f.endswith('.png')]
            file_names.sort()
            self.nb_img = len(file_names)

              # Update spinBox:
            self.images_step.setEnabled(True)
            self.images_firstRank.setEnabled(True)
            self.images_lastRank.setEnabled(True)

            self.images_firstRank.setValue(1)
            self.images_step.setValue(1)
            self.images_lastRank.setValue(self.nb_img)

            self.images_firstRank.setMaximum(self.nb_img)
            self.images_lastRank.setMaximum(self.nb_img)
            self.images_step.setMaximum(self.nb_img)

            # MAJ des boutons prev et next
            self.img_idx = self.images_firstRank.value()
            self.btn_prev.setEnabled(True)
            self.btn_first.setEnabled(True)

            self.btn_prev.setStatusTip("charge l'image précédente")

            self.btn_next.setEnabled(True)
            self.btn_last.setEnabled(True)
            self.btn_next.setStatusTip("afficher "+self.mw.image_fmt.format(\
                self.img_idx+self.images_step.value()))
          
            self.show_image()
            self.scaleInfoVisible(True)
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

            self.mw.twoPlots_VxVy.reset()
            

            if self.mw.flags["displayInfo"]:
                rep = QMessageBox.information(
                    None,             # widget parent de QMessageBox
                    'Information',    # bandeau de la fenêtre
                    'Vous pouvez maintenant sélectionner une couleur de cible'+\
                    'avec la souris...',
                    QMessageBox.Ok)
                

    def show_image(self):
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
        self.img_idx = self.images_firstRank.value()
        self.mw.statusBar().showMessage("")
        self.show_image()

    def prev_image(self) :
        if self.img_idx == None : return
        if self.img_idx >= self.images_firstRank.value() + self.images_step.value():
            self.img_idx -= self.images_step.value()
        self.mw.statusBar().showMessage("")
        self.show_image()

    def last_image(self) :
        if self.img_idx == None : return
        self.img_idx = self.images_lastRank.value() # rank of last image to process
        self.mw.statusBar().showMessage("")
        self.show_image()

    def next_image(self) :
        if self.img_idx == None : return
        if self.img_idx <= self.images_lastRank.value()-self.images_step.value():
            self.img_idx += self.images_step.value()
        self.mw.statusBar().showMessage("")
        self.show_image()

    def parse_meta_data(self):
        self.video_nframes  = self.dico_video.get('nframes', None)
        self.video_size     = self.dico_video.get('size', None)
        self.video_FPS      = self.dico_video.get('fps', None)
        self.video_duration = self.dico_video.get('duration', None)
        self.video_name     = self.dico_video.get('videoname',"none.mp4")

        if self.mw.flags["debug"]:
            info= " nb images    : {},\n taille image : {},\n FPS : {} image/sec,\n durée : {.2f} sec."
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

    def scale_XY(self):

        self.valid_scale = False
        self.pix_to_mm_coeff = 1.
        
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
        print("valid scale : ", self.pix_to_mm_coeff)



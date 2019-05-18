#
# version 1.2 -- 2019-05-07 -- JLC -- 
#   revision from "tracker video JLC solution".
#

import os
import cv2
from PyQt5.QtWidgets import (QDialog, QLabel, QProgressBar, QPushButton,
                             QVBoxLayout, QHBoxLayout, QMessageBox)
from PyQt5.QtCore import Qt
from ThreadedWork import SplitVideoInImagesThread, ExtractTargetFomImagesThread

class ProgressBar(QDialog):

    def __init__(self, __images_dir, parent=None):

        QDialog.__init__(self, parent=parent)

        self.__thread      = None       # l'objet QThread qui fera le calcul
        self.__images_dir  = __images_dir # le dossier des images
        self.__images_list = None       # la liste des images *.png à traiter
        self.__vMin        = None       # la valeur min de la barre
        self.__vMax        = None       # la valeur max de la barre

        self.title = QLabel("",self)
        self.pbar  = QProgressBar(self)
        self.pbar.setGeometry(30, 40, 250, 25)

        self.btnOk = QPushButton('OK', self)
        self.btnOk.clicked.connect(self.close)
        self.btnOk.setEnabled(False)

        self.btnCancel = QPushButton('Cancel', self)
        self.btnCancel.clicked.connect(self.Cancel)
        self.btnCancel.setEnabled(True)

        vbox = QVBoxLayout()
        vbox.addWidget(self.title)
        vbox.addWidget(self.pbar)
        hbox = QHBoxLayout()
        hbox.addWidget(self.btnOk)
        hbox.addWidget(self.btnCancel)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.setModal(True)
        self.setWindowModality(Qt.ApplicationModal)
        self.show()

    def configure_for_video_extraction(self, videoCapture, imagesFormat):
        self.__vMin = 1
        self.__vMax = int(videoCapture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.pbar.setRange(self.__vMin, self.__vMax)
        self.pbar.setValue(self.__vMin)

        self.setWindowTitle('Traitement de la vidéo')
        self.title.setText("Extraction images : ")

        self.__thread = SplitVideoInImagesThread(videoCapture,
                                               self.__images_dir,
                                               imagesFormat)

        self.__thread.ImageExtractedSig.connect(self.updateProgressBar)
        self.__thread.ImageProblemSig.connect(self.updateProgressBar)
        self.__thread.start()

    def configure_for_target_extraction(self,
                                        target_RGB,
                                        algo,
                                        marge_couleur,
                                        target_pos):

        self.__images_list = [ f for f in os.listdir(self.__images_dir) if f.endswith(".png")]
        self.__images_list.sort()

        self.__vMin = 1
        self.__vMax = len(self.__images_list)
        self.pbar.setRange(self.__vMin, self.__vMax)
        self.pbar.setValue(self.__vMin)

        self.setWindowTitle('Traitement des images du dossier {}'\
                            .format(self.__images_dir))

        # Lancer un __thread pour le travil d'extraction des images de la vidéo :
        self.__thread = ExtractTargetFomImagesThread(self.__images_dir,
                                                   self.__images_list,
                                                   target_RGB,
                                                   algo,
                                                   marge_couleur,
                                                   target_pos)
        self.__thread.TargetExtractedSig.connect(self.updateProgressBar)
        self.__thread.TargetProblemSig.connect(self.updateProgressBar)
        self.__thread.start()

    def Cancel(self):
        # Appui sur le bouton Cancel.

        # Arrêter le Thread en cours :
        self.__thread.quit()
        # Fermer la fenêtre QDialog avec un code retour à -1 :
        self.done(-1)

    def updateProgressBar(self, value):
        if value >= 0:
            # l'image N° <value> vient d'être traitée avec succès :
            self.pbar.setValue(value)
            if value == 0 or value == self.pbar.maximum():
                self.btnOk.setEnabled(True)
            mess = "{:3d}/{:3d}".format(value,self.__vMax)
        else:
            # l'image N° <value> a provoqué une erreur :
            mess = self.title.text()
            mess += '\n Erreur image {}'.format(-value)

        self.title.setText("Extraction images : " + mess)

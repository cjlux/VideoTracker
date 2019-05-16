#
# version 1.2 -- 2018-10-10 -- JLC -- version issue de coorigéJLC.
#

import cv2
import numpy as np
from scipy.misc import imread
from PyQt5.QtCore import QThread, pyqtSignal

class SplitVideoInImagesThread(QThread):
    '''Thread chargé de l'extraction des images, avec envoi
       du signal ImageProblemSig à la barre de progression'''

    # Définition de 2 signaux associés à un paramètre entier (n° image) :
    ImageExtractedSig = pyqtSignal(int)
    ImageProblemSig   = pyqtSignal(int)

    def __init__(self, videoCapture, imageDir, imagesFormat):
        super().__init__()
        self.__video = videoCapture      # l'objet openCV.VideoCapture 
        self.__imDir = imageDir           # le répertoire où écrire les images
        self.__fileNameFormat = imagesFormat  # le format des noms d'images

    def run(self):
        if self.__video.isOpened():
            i = 0
            while True:
                returnVal, frame = self.__video.read()
                if returnVal == False :
                    self.ImageExtractedSig.emit(0) # -> fin barre progression
                    break
                i += 1
                img_path = self.__imDir + self.__fileNameFormat.format(i)
                cv2.imwrite(img_path,frame)                
                # émettre le signal ImageExtractedSig avec le n° d'image
                # pour faire avancer la barre de progression connectée
                # à ce signal :
                self.ImageExtractedSig.emit(i)                                                                
        else:
            print("Some problem occured...")
            
class ExtractTargetFomImagesThread(QThread):
    '''Thread chargé de l'extraction de la cible colorée dans les images,
       avec envoi du signal TargetExtractedSig pour la progression de la
       barre et du dignal ExtractTargetProblemSig en cas de problème.'''

    # Définition de 2 signaux associés à un paramètre entier (n° image) :
    TargetExtractedSig = pyqtSignal(int)
    TargetProblemSig   = pyqtSignal(int)

    def __init__(self,
                 images_dir,    # le répertoire des images à traiter
                 images_list,   # la liste des images à traiter
                 target_RGB,    # couleurs RGB de la cible à extraire
                 algo,          # l'algorithme de calcul du centre cible
                 marge_couleur, # pour la couleur à epsilon près
                 target_pos):   # liste des lignes, colonnes des centres cible

        super().__init__()
        self.__images_dir    = images_dir
        self.__images_list   = images_list
        self.__target_RGB    = target_RGB
        self.__algo          = algo
        self.__epsilon       = marge_couleur
        self.__target_pos    = target_pos

    def run(self):
        #### <à compléter>
        #### pour remplir liste target_pos avec les 2 listes listeX et listeY
        #### des coordonnées (X,Y) du centre cible dans chaque image.

        print("Calcul du centre cible dans les images avec l'algorithme '{}'"\
              .format(self.__algo))

        r,g,b = self.__target_RGB # les couleurs à rechercher
        listeX, listeY = [], []

        # Parcourir les images à la recherche des pixels
        for i, image in enumerate(self.__images_list, start=1):
            path = self.__images_dir + image
            try :
                pixelsTab = imread(path)
                tab_bool = (abs(pixelsTab[:,:,0]-r) <= self.__epsilon)* \
                           (abs(pixelsTab[:,:,1]-g) <= self.__epsilon)* \
                           (abs(pixelsTab[:,:,2]-b) <= self.__epsilon)*1
                Y,X = np.array(np.nonzero(tab_bool))

                if X.size != 0 and Y.size != 0:
                    # Calcul du centre en fonction de l'algorithme:
                    if self.__algo == 'barycentre':
                        x, y = X.mean(), Y.mean()
                    elif self.__algo == 'minmax':
                        x, y = (X.min()+X.max())/2, (Y.min()+Y.max())/2
                        
                listeX.append(x)
                listeY.append(y)
                # émettre le signal TargetExtractedSig avec le n° d'image
                # pour faire avancer la barre de progression connectée à
                # ce signal :
                self.TargetExtractedSig.emit(i)
            except :
                print("erreur extraction cible, image {}...".format(image))
                # émettre le signal ImageProblemSig, avec le n° de l'image à PB
                self.TargetProblemSig.emit(-i)

        # Mettre à jour la liste target_pos :
        self.__target_pos.extend([listeX, listeY])

        ########## <fin à compléter>

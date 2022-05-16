#
# version 1.0 -- 2020-04-24 -- JLC -- Initial revision
#

import numpy as np
from copy import copy
from PyQt5.Qt import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox)

from PythonEmbeded import ConsoleWidget

class PythonConsole(QWidget):
    ''' Widget to display an IPython console'''

    def __init__(self, mainWindow):

        # call the base class constructor:
        super().__init__(mainWindow)

        self.mw = mainWindow    # fenêtre de l'application

        # Attributs (objets persistants)
        self.__IpythonConsole = ConsoleWidget()
        self.__btn_loadData   = QPushButton("Load Data", self)
        self.__btn_clearData  = QPushButton("Clear Data", self)
        
        self.__initUI()   # Initialisation de l'interface utilisateur


    def __initUI(self):

        self.__btn_loadData.clicked.connect(self.__loadData)
        self.__btn_loadData.setEnabled(True)
        texte = "Load current X, Y, VX, VY & T vectors"
        self.__btn_loadData.setStatusTip(texte)

        self.__btn_clearData.clicked.connect(self.__clearData)
        self.__btn_clearData.setEnabled(True)
        texte = "Clears all data"
        self.__btn_clearData.setStatusTip(texte)
        

        vbox = QVBoxLayout()
        self.setLayout(vbox)

        hbox = QHBoxLayout()
        hbox.addWidget(self.__btn_loadData)
        hbox.addWidget(self.__btn_clearData)

        vbox.addLayout(hbox)
        vbox.addWidget(self.__IpythonConsole)

        self.__IpythonConsole.setFocus() # give focus to the IPython console

    def __loadData(self):
        # send global variable to IPython console:
        if self.mw.target_pos is None:
            self.mw.statusBar().showMessage("No data to load, sorry...")
            return

        target_pos    = copy(self.mw.target_pos)
        target_veloc  = copy(self.mw.target_veloc)
        target_accel  = copy(self.mw.target_accel)
        csv_dataFrame = copy(self.mw.csv_dataFrame)
        X, Y   = target_pos[0], target_pos[1]
        VX, VY = target_veloc[0], target_veloc[1]
        AX, AY = target_accel[0], target_accel[1]
        
        #print(target_pos)
        
        if self.mw.imageTab.video_FPS is not None:
            T = np.arange(len(X))/self.mw.imageTab.video_FPS
        else:
            T = np.arange(len(X))+1
        dico = {'X':X, 'Y':Y, 'VX':VX, 'VY':VY, 'AX': AX, 'AY': AY, 'T':T, 'target_pos':target_pos, 'csv_dataFrame':csv_dataFrame}
        print("dico:",dico)
        self.__IpythonConsole.push_vars(dico)
        self.__IpythonConsole.setFocus() # give focus to the IPython console
        rep = QMessageBox.information(
                  None,         # no parent widget for QMessageBox
                  'Message',    # bandeau de la fenêtre
                  'Objects X, Y, VX, VY,AX, AY, T and target_pos have been loaded',
                   QMessageBox.Ok)


    def __clearData(self):
        try:                                 
            self.__IpythonConsole.execute_command('if "X" in dir(): del X')
            self.__IpythonConsole.execute_command('if "Y" in dir(): del Y')
            self.__IpythonConsole.execute_command('if "target_pos" in dir():del target_pos')
            self.__IpythonConsole.execute_command('if "VX" in dir(): del VX')
            self.__IpythonConsole.execute_command('if "VY" in dir(): del VY')
            self.__IpythonConsole.execute_command('if "AX" in dir(): del AX')
            self.__IpythonConsole.execute_command('if "AY" in dir(): del AY')
            self.__IpythonConsole.execute_command('clear')
            rep = QMessageBox.information(
                  None,         # no parent widget for QMessageBox
                  'Message',    # bandeau de la fenêtre
                  'Objects X, Y, VX, VY, AX, AY T and and target_pos have been deleted',
                   QMessageBox.Ok)
            self.__IpythonConsole.print_text("")
            
        except:
            pass
        
        self.__IpythonConsole.setFocus() # give focus to the IPython console

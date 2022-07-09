import os
from pathlib import Path
import sys
from typing import overload

from PyQt5.QtWidgets import *
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
import __init__
import gOut
import gRead
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QImage,QPixmap
from PyQt5.QtWidgets import  QWidget, QMainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile
import cv2
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QImage, QPalette, QBrush
import numpy as np
import serial
import time
import argparse
import serial.tools.list_ports
import winreg
import utlis
import itertools
import threading


class main(QMainWindow):
    Port=" "
    def __init__(self):
        super(main, self).__init__()
        self.setFixedSize(1300, 650)
        call=uic.loadUi('form.ui',self)
        call.camOn.clicked.connect(self.camClicked)
        call.sendGcode.clicked.connect(self.sendGClicked)
        call.takePhoto.clicked.connect(self.takePhotoClicked)
        call.refreshPorts.clicked.connect(self.refreshPortClicked)
        self.infoScreen.setText("--")
        self.infoScreen.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.infoScreen.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.infoScreen.setWordWrap(True)
        self.camOn.setVisible(True)
        self.sendGcode.setVisible(True)
        self.takePhoto.setVisible(False)
        self.bar1.setVisible(False)
        self.bar2.setVisible(False)
        self.t1.setVisible(False)
        self.t2.setVisible(False)
        self.bar1.setStyleSheet("background:transparent")
        self.bar2.setStyleSheet("background:transparent")
        self.t1.setStyleSheet("background:transparent")
        self.t2.setStyleSheet("background:transparent")
        image = QIcon("camera.png")         
        call.takePhoto.setIcon(image)
        size = QSize(100, 100)
        call.takePhoto.setIconSize(size)
        call.takePhoto.setStyleSheet("background:transparent")
        imageRefresh = QIcon("reload.png")         
        call.refreshPorts.setIcon(imageRefresh)
        sizeRefresh = QSize(6,6)
        call.refreshPorts.setIconSize(size)
        call.refreshPorts.setStyleSheet("background:transparent")
        self.serial_ports()
        self.refreshPortClicked()

    def refreshPortClicked(self):
        self.serial_ports()
        self.Port=self.comboBox.currentText()

    def serial_ports(self) -> list:
        self.comboBox.clear()
        path = 'HARDWARE\DEVICEMAP\SERIALCOMM'
        

        ports = []

        for i in itertools.count():
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                ports.append(winreg.EnumValue(key, i)[1])
                self.comboBox.addItem(winreg.EnumValue(key, i)[1])
            except EnvironmentError:
                break
        return ports


    def removeComment(self, string):
        if (string.find(';')==-1):
            return string
        else:
            return string[:string.index(';')]
    
    def camClicked(self):
        print("camClicked")
        self.infoScreen.setText(self.infoScreen.text()+"\n--Die Kamera war eingeschaltet.")  
        self.logic=0
        self.bar1.setMaximum(255)
        self.bar1.setMinimum(0)
        self.bar2.setMaximum(255)
        self.bar2.setMinimum(0)
        self.bar2.setValue(200)
        self.bar1.setValue(200)
        count = 0
        self.oriImage.setVisible(True)
        self.workedImage.setVisible(True)
        self.camOn.setVisible(False)
        self.sendGcode.setVisible(False)
        self.takePhoto.setVisible(True)
        self.bar1.setVisible(True)
        self.bar2.setVisible(True)
        self.t1.setVisible(True)
        self.t2.setVisible(True)
        print("Cam ON")
        widthImg = 400
        heightImg = 400
        cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)
        cap.set(10, 160)
        
        kernel = np.ones((5,5), np.uint8)

        while True:
            success, img = cap.read()
            img = cv2.resize(img, (widthImg, heightImg))  
            imgBlank = np.zeros((heightImg, widthImg, 3), np.uint8) 
            imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  
            imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)  
            imgThreshold = cv2.Canny(imgBlur, self.bar1.value(), self.bar2.value())  
            kernel = np.ones((5, 5))
            imgDial = cv2.dilate(imgThreshold, kernel, iterations=2) 
            imgThreshold = cv2.erode(imgDial, kernel, iterations=1)  
            imgWarpColored=None

            imgContours = img.copy() 
            imgBigContour = img.copy() 
            contours, hierarchy = cv2.findContours(imgThreshold, cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)  
            cv2.drawContours(imgContours, contours, -1, (0, 255, 0), 10) 

            biggest, maxArea = utlis.biggestContour(contours)  
            if biggest.size != 0:
                biggest = utlis.reorder(biggest)
                cv2.drawContours(imgBigContour, biggest, -1, (0, 255, 0), 20)  
                imgBigContour = utlis.drawRectangle(imgBigContour, biggest, 2)
                pts1 = np.float32(biggest) 
                pts2 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]]) 
                matrix = cv2.getPerspectiveTransform(pts1, pts2)
                imgWarpColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg))

                imgWarpColored = imgWarpColored[20:imgWarpColored.shape[0] - 20, 20:imgWarpColored.shape[1] - 20]
                imgWarpColored = cv2.resize(imgWarpColored, (widthImg, heightImg))

                imgWarpGray = cv2.cvtColor(imgWarpColored, cv2.COLOR_BGR2GRAY)
                imgAdaptiveThre = cv2.adaptiveThreshold(imgWarpGray, 255, 1, 1, 7, 2)
                imgAdaptiveThre = cv2.bitwise_not(imgAdaptiveThre)
                imgAdaptiveThre = cv2.medianBlur(imgAdaptiveThre, 3)

                imageArray = ([imgContours])
                imageArray2 = ([imgWarpColored])

            else:
                imageArray = ([imgContours])
                imageArray2= ([imgBlank])

            lables = [["Original", "Gray", "Threshold", "Contours"],
                    ["Biggest Contour", "Warp Prespective", "Warp Gray", "Adaptive Threshold"]]

            stackedImage = utlis.stackImages(imageArray, 1)
            stackedImage2 = utlis.stackImages(imageArray2, 1)
            self.displayImage(self.oriImage,stackedImage[:400],1)
            self.displayImage(self.workedImage,stackedImage2[:400],1)

            if not success:
                break

        
            if self.logic==2:
                print("Cam OFF")
                self.camOn.setVisible(True)
                self.sendGcode.setVisible(True)
                self.takePhoto.setVisible(False)
                self.bar1.setVisible(False)
                self.bar2.setVisible(False)
                self.t1.setVisible(False)
                self.t2.setVisible(False)
                break 

            if cv2.waitKey(1) & self.logic==1:
                try:
                    cv2.imwrite("Scanned/myImage.png", imgWarpColored)
                    cv2.rectangle(stackedImage, ((int(stackedImage.shape[1] / 2) - 230), int(stackedImage.shape[0] / 2) + 50),
                                (1100, 350), (0, 255, 0), cv2.FILLED)
                    cv2.putText(stackedImage, "Scan Saved", (int(stackedImage.shape[1] / 2) - 200, int(stackedImage.shape[0] / 2)),
                                cv2.FONT_HERSHEY_DUPLEX, 3, (0, 0, 255), 5, cv2.LINE_AA)
                    self.infoScreen.setText(self.infoScreen.text()+"\n--Das Foto wurde gemacht.")
                    cv2.waitKey(300)

                    if os.path.isfile("Scanned/myImage.png"):
                        paths = gRead.imToPaths("Scanned/myImage.png")
                        outfile = "Scanned/myImage.gcode"
                        gOut.toTextFile(outfile, paths)
                        self.infoScreen.setText(self.infoScreen.text()+"\n--G-Code wurde erstellt.") 
                    count += 1
                except:
                    self.infoScreen.setText(self.infoScreen.text()+"\n--Das Dokument konnte nicht bestimmt werden.")
                    self.infoScreen.setText(self.infoScreen.text()+"\n--Bitte versuche es erneut!")
                self.logic=2
        cap.release() 
        for i in range(1,10):
            cv2.destroyAllWindows()
            cv2.waitKey(1)
        self.sendGcode.setVisible(True)
        self.oriImage.setVisible(True)
        self.logic=0 
    
    def displayImage(self,lbl, img,window=1):
        qformat=QImage.Format_Indexed8

        if len(img.shape)==3:
            if(img.shape[2])==4:
                qformat=QImage.Format_RGBA8888

            else:
                qformat=QImage.Format_RGB888

        img=QImage(img,img.shape[1],img.shape[0],qformat)
        img=img.rgbSwapped()
        lbl.setPixmap(QPixmap.fromImage(img))
        lbl.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)


    def takePhotoClicked(self):
        self.logic=1

    def sendGClicked(self):

        self.infoScreen.setText(self.infoScreen.text()+"\n--Der G-Code-Sendevorgang wurde gestartet und Druckvorgang wurde gestartet.\n--\n--\n--")
        self.Port=self.comboBox.currentText()
        parser = argparse.ArgumentParser(description='This is a basic gcode sender. http://crcibernetica.com')
        args = parser.parse_args()
        args.port=self.Port.lower()
        args.file="Scanned\myImage.gcode"
        thread_svg=threading.Thread(target=self.sendG,args=(args.port, args.file),daemon=True)
        thread_svg.start()

    
    def sendG(self, com, file):
        print("sendGCodeClicked")
        print("COM : " , com)
        self.infoScreen.setText(self.infoScreen.text()+"\n--USB Port: %s" % com)
        self.infoScreen.setText(self.infoScreen.text()+"\n--Gcode file: %s" % file)
        print ("USB Port: %s" % com )
        print ("Gcode file: %s" % file )
        try:
            s = serial.Serial(com, 115200)
            try:
                f = open(file,'r')
                time.sleep(2)  
                s.flushInput()  
                a=True
                for line in f:
                    l = self.removeComment(line)
                    l = l.strip() 
                    if a==True:
                        self.infoScreen.setText(self.infoScreen.text()+"\n--Druckvorgang wurde gestartet...")
                        self.sendGcode.setEnabled(False)
                        self.camOn.setEnabled(False)
                        a=False
                    print(l)
                    if  (l.isspace()==False and len(l)>0) :
                        s.write((l + '\n').encode()) 
                        grbl_out = s.readline() 
                        print(grbl_out)
                self.infoScreen.setText(self.infoScreen.text()+"\n--Druckvorgang ist fertig.")   
                self.sendGcode.setEnabled(True)
                self.camOn.setEnabled(True)
                f.close()
                s.close()
            except:
                self.sendGcode.setEnabled(True)
                self.camOn.setEnabled(True)
                self.infoScreen.setText(self.infoScreen.text()+"\n--Das G-Code-Verzeichnis ist falsch oder der es wurde nicht gefunden.")   
                print("--Das G-Code-Verzeichnis ist falsch oder der es wurde nicht gefunden.")
        except:
            self.sendGcode.setEnabled(True)
            self.camOn.setEnabled(True)
            self.infoScreen.setText(self.infoScreen.text()+"\n--Der Zeichenroboter ist nicht angeschlossen oder es ist an den falschen Anschluss angeschlossen.")  
            print("arduino bağlanmadı ya da arduino yanlış porta bağlı.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = main()
    widget.show()
    sys.exit(app.exec_())
    
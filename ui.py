import sys
import random
import main
from PySide6 import QtCore, QtWidgets, QtGui
class rectangle(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(30,30,600,400)
        
        self.show()
    def background(self,qp):
        br = QtGui.QBrush(QtGui.QColor(10, 10, 10, 40))  
        qp.setBrush(br) 
        begin = QtCore.QPoint()
        end = QtCore.QPoint()  
        begin.setX(0)
        begin.setY(0)
        end.setX(self.width())
        end.setY(self.height())
        qp.drawRect(QtCore.QRect(begin, end))  
    def pianoRoll(self,qp):
        pen = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        keyWidth = 20
        keyLength = 100
        for i in range(0,self.width()-keyWidth):
            qp.setBrush(pen)
            begin = QtCore.QPoint()
            end = QtCore.QPoint()  
            begin.setX(0+(keyWidth+2)*i)
            begin.setY(self.height()-keyLength)
            end.setX(keyWidth+(keyWidth+2)*i)
            end.setY(self.height())
            qp.drawRect(QtCore.QRect(begin, end))
        for i in range(0,self.width()-keyWidth):

            if i % 7 == 0 or i % 7 == 1 or i % 7 == 3 or i % 7 == 4 or i % 7 == 5:
                begin.setX((0+keyWidth/2+(keyWidth+2)*i)+keyWidth/4)
                begin.setY(self.height()-keyLength)
                end.setX(begin.x()+keyWidth/2 + 2)
                end.setY(self.height()-keyLength/2)

                qp.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
                qp.drawRect(QtCore.QRect(begin, end))   
    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        self.background(qp)
        self.pianoRoll(qp)

    
                     


    def mousePressEvent(self, event):
        pass
        # self.begin = event.pos()
        # self.end = event.pos()
        # self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        print(self.begin,self.end) 

        self.update()

    def mouseReleaseEvent(self, event):
        pass
        # self.begin = event.pos()
        # self.end = event.pos()
        # self.update()
class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()


        self.button = QtWidgets.QPushButton("Start!")

        self.layout = QtWidgets.QVBoxLayout(self)
        # self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)
        self.layout.addWidget(rectangle())

        self.button.clicked.connect(self.startSong)

    @QtCore.Slot()
    def startSong(self):
        
        # self.text.setText(random.choice(self.hello))
        main.main()
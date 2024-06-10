import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QTableWidget,
    QTableWidgetItem, QSlider, QLabel, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsRectItem,
    QInputDialog, QGraphicsItem
)
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QBrush, QColor, QPixmap

class ResizableRect(QGraphicsRectItem):
    def __init__(self, *args):
        super().__init__(*args)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setBrush(QBrush(Qt.blue))

    def mouseMoveEvent(self, event):
        newX = event.scenePos().x()
        if newX > 0:
            self.setRect(0, 0, newX, self.rect().height())
        super().mouseMoveEvent(event)

class LEDSequencer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('LED Sequencer')
        self.setGeometry(100, 100, 1200, 800)

        self.ledCount = 5
        self.stateCount = 10

        mainWidget = QWidget()
        self.setCentralWidget(mainWidget)
        
        self.mainLayout = QVBoxLayout()

        self.setupTable()
        self.setupControls()
        self.setupSimulation()

        mainWidget.setLayout(self.mainLayout)

    def setupTable(self):
        self.table = QTableWidget(self.ledCount, self.stateCount)
        self.table.setHorizontalHeaderLabels([f'Time {i+1}' for i in range(self.stateCount)])
        self.table.setVerticalHeaderLabels([f'LED {i+1}' for i in range(self.ledCount)])

        for row in range(self.ledCount):
            for col in range(self.stateCount):
                rectItem = ResizableRect(0, 0, 50, 20)
                self.table.setCellWidget(row, col, QGraphicsView())
                self.table.cellWidget(row, col).setScene(QGraphicsScene())
                self.table.cellWidget(row, col).scene().addItem(rectItem)
                self.table.cellWidget(row, col).setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.table.cellWidget(row, col).setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.table.cellWidget(row, col).setAlignment(Qt.AlignCenter)

        self.mainLayout.addWidget(self.table)

    def setupControls(self):
        controlLayout = QHBoxLayout()

        self.addLEDButton = QPushButton('Add LED')
        self.addLEDButton.clicked.connect(self.addLED)
        controlLayout.addWidget(self.addLEDButton)

        self.addStateButton = QPushButton('Add State')
        self.addStateButton.clicked.connect(self.addState)
        controlLayout.addWidget(self.addStateButton)

        self.saveButton = QPushButton('Save to JSON')
        self.saveButton.clicked.connect(self.saveToJson)
        controlLayout.addWidget(self.saveButton)

        self.testButton = QPushButton('Test Simulation')
        self.testButton.clicked.connect(self.runSimulation)
        controlLayout.addWidget(self.testButton)

        self.mainLayout.addLayout(controlLayout)

    def setupSimulation(self):
        self.simulationLabel = QLabel()
        self.simulationLabel.setFixedHeight(200)
        self.simulationScene = QGraphicsScene()
        self.simulationView = QGraphicsView(self.simulationScene)
        self.carPixmap = QPixmap('car.png')
        self.simulationScene.addPixmap(self.carPixmap)
        self.ledGraphics = []
        self.ledPositions = [
            (50, 50), (100, 50), (150, 50), (200, 50), (250, 50)
        ]
        for pos in self.ledPositions:
            led = QGraphicsEllipseItem(QRectF(pos[0], pos[1], 20, 20))
            led.setBrush(QBrush(Qt.black))
            self.simulationScene.addItem(led)
            self.ledGraphics.append(led)
        self.mainLayout.addWidget(self.simulationView)

    def addLED(self):
        self.ledCount += 1
        self.table.setRowCount(self.ledCount)
        self.table.setVerticalHeaderLabels([f'LED {i+1}' for i in range(self.ledCount)])

        for col in range(self.stateCount):
            rectItem = ResizableRect(0, 0, 50, 20)
            self.table.setCellWidget(self.ledCount - 1, col, QGraphicsView())
            self.table.cellWidget(self.ledCount - 1, col).setScene(QGraphicsScene())
            self.table.cellWidget(self.ledCount - 1, col).scene().addItem(rectItem)
            self.table.cellWidget(self.ledCount - 1, col).setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.table.cellWidget(self.ledCount - 1, col).setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.table.cellWidget(self.ledCount - 1, col).setAlignment(Qt.AlignCenter)

    def addState(self):
        self.stateCount += 1
        self.table.setColumnCount(self.stateCount)
        self.table.setHorizontalHeaderLabels([f'Time {i+1}' for i in range(self.stateCount)])

        for row in range(self.ledCount):
            rectItem = ResizableRect(0, 0, 50, 20)
            self.table.setCellWidget(row, self.stateCount - 1, QGraphicsView())
            self.table.cellWidget(row, self.stateCount - 1).setScene(QGraphicsScene())
            self.table.cellWidget(row, self.stateCount - 1).scene().addItem(rectItem)
            self.table.cellWidget(row, self.stateCount - 1).setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.table.cellWidget(row, self.stateCount - 1).setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.table.cellWidget(row, self.stateCount - 1).setAlignment(Qt.AlignCenter)

    def saveToJson(self):
        sequences = []

        for col in range(self.table.columnCount()):
            states = []
            for row in range(self.table.rowCount()):
                rect = self.table.cellWidget(row, col).scene().items()[0]
                width = rect.rect().width()
                if width > 0:
                    states.append(1)
                else:
                    states.append(0)
            duration = width * 10  # Convert width to duration
            sequences.append({"states": states, "duration": duration})

        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)
        if filePath:
            with open(filePath, 'w') as file:
                json.dump(sequences, file, separators=(',', ':'))
                file.write('\n')

    def runSimulation(self):
        self.simulationIndex = 0
        self.simulationData = []

        for col in range(self.table.columnCount()):
            states = []
            for row in range(self.table.rowCount()):
                rect = self.table.cellWidget(row, col).scene().items()[0]
                width = rect.rect().width()
                if width > 0:
                    states.append(1)
                else:
                    states.append(0)
            duration = width * 10  # Convert width to duration
            self.simulationData.append((states, duration))

        self.simulationTimer = QTimer()
        self.simulationTimer.timeout.connect(self.updateSimulation)
        self.simulationTimer.start(100)

    def updateSimulation(self):
        if self.simulationIndex < len(self.simulationData):
            states, duration = self.simulationData[self.simulationIndex]
            for i, state in enumerate(states):
                if state == 1:
                    self.ledGraphics[i].setBrush(QBrush(Qt.white))
                else:
                    self.ledGraphics[i].setBrush(QBrush(Qt.black))
            self.simulationIndex += 1
            self.simulationTimer.setInterval(duration)
        else:
            self.simulationTimer.stop()

def main():
    app = QApplication(sys.argv)
    ex = LEDSequencer()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

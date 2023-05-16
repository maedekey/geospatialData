import os
import webbrowser

from dateutil.parser import parse
from PyQt5.QtWidgets import QComboBox, QDateEdit, QApplication, QWidget, QPushButton, \
    QVBoxLayout, QLabel, QLineEdit, QTabWidget, QHBoxLayout, QGridLayout, QSpacerItem, QSizePolicy, \
    QMessageBox
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import QDate, Qt
from datetime import datetime
import osmnx as ox
import visualization

"""
To execute this code for the first time, please run db.py then dashboard.py
You will need to put the gtfsrt data in a directory called 'data', in in the directory where you execute your program.
The file 'stops.txt' should also be in the directory where you execute your program
"""

def setLayouts(departure, destination, page2):
    """
    Method adding multiple qwidgets to the layout of pyqt
    :param departure: qwidget holding the departure station name
    :param destination: qwidget holding the destination station name
    :param page2: qwidget holding the second page of the window
    :return:
    """
    slayout1 = QHBoxLayout()
    slayout1.addWidget(page2.lab1, Qt.AlignLeft)
    slayout1.addWidget(page2.hours)
    slayout1.addWidget(page2.lab2)
    slayout1.addWidget(page2.minutes)
    slayout2 = QHBoxLayout()
    slayout2.addWidget(page2.lab5, Qt.AlignLeft)
    slayout2.addWidget(page2.date)
    slayout1.setContentsMargins(0, 0, 0, 0)
    layout1 = QVBoxLayout()
    layout2 = QGridLayout()
    layout2.addWidget(page2.lab0, 0, 0)
    layout2.addLayout(slayout2, 1, 0)
    layout2.addLayout(slayout1, 2, 0)
    layout2.addWidget(page2.lab3, 3, 0)
    layout2.addWidget(departure, 4, 0)
    layout2.addWidget(page2.lab4, 5, 0)
    layout2.addWidget(destination, 6, 0)
    layout2.addWidget(page2.search, 7, 0)
    verticalSpacer = QSpacerItem(40, 30, QSizePolicy.Minimum, QSizePolicy.Expanding)
    layout2.addItem(verticalSpacer, 7, 0, Qt.AlignTop)
    page2.setLayout(layout2)


def setTime(page2):
    """
    Function allowing to propose to the user to enter a date and hour for the trip he wants to visualize
    :param page2:
    :return:
    """
    page2.hours = QLineEdit("13")
    page2.minutes = QLineEdit("24")
    page2.date = QDateEdit()
    page2.date.setDisplayFormat("dd-MM-yyyy")
    page2.date.setDate(QDate.currentDate())
    page2.date.setStyleSheet("QDateEdit {padding: 3px; margin: 10px; width:110px}")


def setScrollBox(page2, station_names):
    """
    Function allowing to add multiple stations to a scrollbox, to facilitate the selection of departure and destination
    for the user
    :param page2: page on which the scrollbox will show
    :param station_names: names of stations to add to the scrollbox
    :return:
    """
    with open('stops.txt', 'r') as file:
        trips = file.readlines()[1:]
    departure = QComboBox(page2)
    destination = QComboBox(page2)
    for line in trips:
        trip_list = line.split(',')
        trip = trip_list[2].split(' ')[0]
        if trip not in station_names:
            station_names.add(trip)
            departure.addItem(trip)
            destination.addItem(trip)
    return departure, destination


def setLabels(page2):
    """
    Function adding labels to the window
    :param page2:
    :return:
    """
    page2.lab0 = QLabel("My travel")
    page2.lab0.setStyleSheet("QLabel { font: 15pt; font-family:'Cambria'; margin: 10px 0 20px 160px }")
    page2.lab1 = QLabel("Time:")
    page2.lab2 = QLabel(":")
    page2.lab3 = QLabel("From:")
    page2.lab4 = QLabel("To:")
    page2.lab5 = QLabel("Date:")


def showNoTripFound():
    """
    Function allowing to show a popup message when the user entered a non-existent trip
    :return:
    """
    message_box = QMessageBox()
    message_box.setText("No trip found.")
    message_box.setWindowTitle("Invalid travel")
    message_box.setIcon(QMessageBox.Information)
    message_box.setStandardButtons(QMessageBox.Ok)
    result = message_box.exec_()


def showInvalidTrip():
    """
    Function allowing to show a pop up message when the user selected the same departure as destination
    :return:
    """
    message_box = QMessageBox()
    message_box.setText("Departure station cannot be the same as arrival station.")
    message_box.setWindowTitle("Invalid travel")
    message_box.setIcon(QMessageBox.Information)
    message_box.setStandardButtons(QMessageBox.Ok)
    result = message_box.exec_()


class Fenetre(QWidget):
    def __init__(self):
        """
        Method initializing the dashboard. First, we load the graphml file (osm) data into the class to avoid reloading
        it at every user search, optimizing the execution time. Then, we initialize graphic objects to set up the view.
        """
        QWidget.__init__(self)
        graphPath = 'railwayGraph.graphml'
        if os.path.exists(graphPath):
            G = ox.load_graphml(graphPath)
        else:
            place_name = "Belgium"
            G = ox.graph_from_place(place_name, custom_filter='["railway"]')
            ox.save_graphml(G, graphPath)
        self.osmdata = G

        self.initWindow()

        self.page2 = self.createTabs()

        self.setpage(self.page2)

        # Add tabs to main window
        self.setTabs(self.page2)

    def setTabs(self, page2):
        """
        Method that creates tabs in the qwindow
        :param page2:
        :return:
        """
        self.qtw = QTabWidget(self)
        self.qtw.addTab(page2, "Trip details")
        # Stylize the main window
        self.setMinimumWidth(1500)
        self.setMinimumHeight(900)
        # Stylize the sub-pages
        self.qtw.setMinimumWidth(1400)
        self.qtw.setMinimumHeight(850)
        self.qtw.move(60, 60)
        self.setWindowTitle("Dashboard")

    def setpage(self, page2):
        """
        Method that sets the content of the page 2 together in the layout
        :param page2:
        :return:
        """
        setLabels(page2)
        station_names = set()
        self.departure, self.destination = setScrollBox(page2, station_names)
        setTime(page2)
        setLayouts(self.departure, self.destination, page2)

    def createTabs(self):
        """
        Method that creates tabs in the page
        :return: the page with the new tabs in it
        """
        page2 = QWidget()
        page2.setStyleSheet("QLabel {margin-top: 10px}")
        self.setStyleSheet("QLineEdit {max-width:30px; padding: 3px}")
        page2.setStyleSheet("QComboBox {margin-bottom: 10px; padding: 5px}")
        page2.search = QPushButton("Search")
        page2.search.clicked.connect(self.retrieveTrip)
        return page2

    def initWindow(self):
        """
        Method that configures the initial parameters of the qwindow
        :return:
        """
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor('#cccccc'))
        self.setPalette(palette)

    def retrieveTrip(self):
        """
        Method that retrieves the user input departure station and arrival station), checks it and shows a visualisation
         of the train between the 2 stations by opening it in the browser
        :return:
        """
        time = self.retrieveTime()
        departureStation = self.departure.currentText()
        arrivalStation = self.destination.currentText()
        if departureStation == arrivalStation:
            showInvalidTrip()
        else:
            data = visualization.gtfsData(self.osmdata, [departureStation, arrivalStation, time])
            if data.found:
                file = data.file
                webbrowser.open(file)
            else:
                showNoTripFound()

    def retrieveTime(self):
        """
        Method that retrieves the user input (time and date) and that converts it into epoch time, to facilitate
        db queries
        :return: epoch time in from of integer
        """
        hours = int(self.page2.hours.text())  # we do -2 because we live in gmt +2
        minutes = int(self.page2.minutes.text())
        date = self.page2.date.date().toString()
        dateObj = parse(date)

        time = datetime(dateObj.year, dateObj.month, dateObj.day, hours, minutes)
        epochTime = time.timestamp()
        return int(epochTime)


app = QApplication.instance()
if not app:
    app = QApplication([])

fen = Fenetre()
fen.show()

app.exec_()

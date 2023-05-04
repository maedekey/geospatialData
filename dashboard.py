from PyQt5.QtWidgets import QComboBox, QDateEdit, QApplication, QWidget, QPushButton, \
    QVBoxLayout, QLabel, QLineEdit, QTabWidget, QHBoxLayout, QGridLayout, QSpacerItem, QSizePolicy, \
    QMessageBox

from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import QDate, Qt


class Fenetre(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        # Background color
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor('#cccccc'))
        self.setPalette(palette)


        # Create tab pages
        page1 = QWidget()
        page1.bouton = QPushButton("Click me")

        page2 = QWidget()
        page2.setStyleSheet("QLabel {margin-top: 10px}")
        self.setStyleSheet("QLineEdit {max-width:30px; padding: 3px}")
        page2.setStyleSheet("QComboBox {margin-bottom: 10px; padding: 5px}")

        page2.search = QPushButton("Search")

        # Ajout des labels
        page2.lab0 = QLabel("My travel")
        page2.lab0.setStyleSheet("QLabel { font: 15pt; font-family:'Cambria'; margin: 10px 0 20px 160px }")

        page2.lab1 = QLabel("Please input an hour:")
        page2.lab2 = QLabel(":")
        page2.lab3 = QLabel("From:")
        page2.lab4 = QLabel("To:")
        page2.lab5 = QLabel("Please input a date:")

        # table to contain the list of trips
        station_names = set()

        # collecting trips from the gtfs file
        with open('stops.txt','r') as file:
            trips = file.readlines()[1:]

        # Ajout de la sélection du départ et destination
        departure = QComboBox(page2)
        destination = QComboBox(page2)

        # Retrieving all stops in the file
        for line in trips:
            trip_list = line.split(',')
            trip = trip_list[2].split(' ')[0]
            if trip not in station_names:
                station_names.add(trip)
                departure.addItem(trip)
                destination.addItem(trip)




        # Edition de l'heure
        page2.hrs1 = QLineEdit("13")
        page2.hrs2 = QLineEdit("24")

        # Edition de la date
        page2.date1 = QDateEdit()
        page2.date1.setDisplayFormat("dd-MM-yyyy")
        page2.date1.setDate(QDate.currentDate())
        page2.date1.setStyleSheet("QDateEdit {padding: 3px; margin: 10px; width:110px}")

        # Sub-layouts
        slayout1 = QHBoxLayout()
        slayout1.addWidget(page2.lab1, Qt.AlignLeft)

        slayout1.addWidget(page2.hrs1)
        slayout1.addWidget(page2.lab2)
        slayout1.addWidget(page2.hrs2)

        #slayout1.setContentsMargins(0, 0, 0, 0)
        #slayout1.setSpacing(0)


        # Date sub-layout
        slayout2 = QHBoxLayout()
        slayout2.addWidget(page2.lab5, Qt.AlignLeft)
        slayout2.addWidget(page2.date1)

        slayout1.setContentsMargins(0, 0, 0, 0)
        # slayout1.setSpacing(0)


        # Layouts
        layout1 = QVBoxLayout()
        layout1.addWidget(page1.bouton)


        # Layout page 2
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

        page1.setLayout(layout1)
        page2.setLayout(layout2)

        # Add tabs to main window
        self.qtw = QTabWidget(self)
        self.qtw.addTab(page1, "Realtime Visualization")
        self.qtw.addTab(page2, "QoS KPIs")

        # Stylize the main window
        self.setMinimumWidth(1500)
        self.setMinimumHeight(900)

        # Stylize the sub-pages
        self.qtw.setMinimumWidth(1400)
        self.qtw.setMinimumHeight(850)
        self.qtw.move(60, 60)

        self.setWindowTitle("Dashboard")



    # on définit une méthode à connecter au signal envoyé
    def appui_bouton_copie(self):
        # la méthode "text" de QLineEdit permet d'obtenir le texte à copier
        texte_a_copier = self.champ.text()
        # la méthode "setText" de QLabel permet de changer
        # le texte de l'étiquette
        self.label.setText(texte_a_copier)






app = QApplication.instance()
if not app:
    app = QApplication([])

fen = Fenetre()
fen.show()

app.exec_()

import webbrowser
from urllib.request import urlopen
from google.transit import gtfs_realtime_pb2
import pydeck as pdk
import folium
from google.protobuf.json_format import MessageToDict


def preprocessing(url):
    gtfs_realtime = gtfs_realtime_pb2.FeedMessage()
    gtfs_realtime.ParseFromString(urlopen(url).read())
    dict_obj = MessageToDict(gtfs_realtime)
    return dict_obj


def addLocations(stopId, line, positionsDict):
    location = line.split(',')[2]
    longitude = line.split(',')[4]
    lattitude = line.split(',')[5]

    positionsDict[stopId] = [location, longitude, lattitude]


class gtfsData:
    def __init__(self):
        url = "file:////home/maedekey/Bureau/geo/1680202355.gtfsrt"
        gtfsDict = preprocessing(url)
        self.gtfsValues = list(gtfsDict.values())[1]
        self.positionsDict = self.findPositions()
        self.visualizeTrains()


    def findPositions(self):
        path = "/home/maedekey/Bureau/geo/gtfs/stops.txt"
        valuesSeen = set()
        positionsDict = {}
        with open(path, 'r') as f:
            for line in f:
                stopId = line.split(',')[0]

                if '_' in stopId:
                    stopId = stopId.split('_')[0]
                if stopId not in valuesSeen and stopId.isdigit():
                    valuesSeen.add(stopId)
                    addLocations(stopId, line, positionsDict)
        return positionsDict

    def visualizeTrains(self):
        pass

    def visualizeStations(self):
        belgium_coords = [50.5039, 4.4699]
        m = folium.Map(location=belgium_coords, zoom_start=8)
        for position in self.positionsDict:
            folium.Marker([self.positionsDict[position][1], self.positionsDict[position][2]],
                          popup=self.positionsDict[position][0]).add_to(m)
        m.save('map.html')




gtfs = gtfsData()

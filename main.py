import json
import webbrowser
from datetime import datetime
from urllib.request import urlopen
from geopy.distance import distance
from folium.plugins import TimestampedGeoJson
from google.transit import gtfs_realtime_pb2
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


def createGeoJSON():
    coordinates = [
        {"coordinates": [-122.4194, 37.7749], "time": "2023-04-30T12:00:00Z"},
        {"coordinates": [-122.4195, 37.7748], "time": "2023-04-30T12:01:00Z"},
        {"coordinates": [-122.4196, 37.7747], "time": "2023-04-30T12:02:00Z"},
        # Add more coordinates with timestamps here
    ]
    # Create a GeoJSON FeatureCollection with a LineString feature
    feature_collection = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [coord["coordinates"] for coord in coordinates]
            },
            "properties": {
                "times": [coord["time"] for coord in coordinates]
            }
        }]
    }
    return feature_collection


def findStationPositions():
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


def calculateDistance(stations):
    if len(stations) > 1:
        stationDistance = distance([float(stations[0][1]), float(stations[0][2])],
                                   [float(stations[1][1]), float(stations[1][2])]).m
        return stationDistance
    else:
        return 0


def calculateAverageSpeed(stations, distance):
    travelTime = int(stations[3]) - int(stations[2])
    averageSpeed = distance/travelTime
    return averageSpeed


def locateTrain(speed, stations, distanceStations):
    print(stations)
    currentTime = 1680193500
    time = currentTime - int(stations[2])
    trainDistance = speed * time
    ratio = trainDistance / distanceStations

    longitude = float(stations[0][1]) + (float(stations[1][1]) - float(stations[0][1])) * ratio
    latitude = float(stations[0][2]) + (float(stations[1][2]) - float(stations[0][2])) * ratio
    print(longitude, latitude)


class gtfsData:
    def __init__(self):
        url = "file:////home/maedekey/Bureau/geo/1680202355.gtfsrt"
        gtfsDict = preprocessing(url)

        self.gtfsValues = list(gtfsDict.values())[1]
        self.positionsDict = findStationPositions()

        self.findTrainLocation()
        # self.visualizeTrains()

    def findTrainLocation(self):
        stations = self.findStations()
        distanceStations = calculateDistance(stations)
        speed = calculateAverageSpeed(stations, distanceStations)
        locateTrain(speed, stations, distanceStations)

    def findStations(self):

        currentTime = 1680193500
        stops = self.gtfsValues[5]['tripUpdate']['stopTimeUpdate']
        for i in range(len(stops) - 1):

            if int(stops[i]['departure']['time']) < currentTime < int(stops[i + 1]['arrival']['time']):
                return [self.positionsDict[stops[i]['stopId']], self.positionsDict[stops[i + 1]['stopId']],
                        stops[i]['departure']['time'], stops[i + 1]['arrival']['time']]
            elif i < len(stops) - 2:
                if int(stops[i + 1]['departure']['time']) >= currentTime >= int(stops[i + 1]['arrival']['time']):
                    return [self.positionsDict[stops[i + 1]['stopId']]]
        return []

    def visualizeTrains(self):
        m = folium.Map(location=[37.7749, -122.4194], zoom_start=14)

        feature_collection = createGeoJSON()

        # Add the GeoJSON data to the map
        TimestampedGeoJson(
            json.dumps(feature_collection),
            period="PT1S",  # update frequency in seconds
            add_last_point=True,  # add a marker at the last point of the trajectory
            auto_play=True,  # autoplay the animation
            loop=True,  # loop the animation
        ).add_to(m)

        # Show the map in PyCharm
        m.save("map.html")
        webbrowser.open('map.html')

    def visualizeStations(self):
        belgium_coords = [50.5039, 4.4699]
        m = folium.Map(location=belgium_coords, zoom_start=8)
        for position in self.positionsDict:
            folium.Marker([self.positionsDict[position][1], self.positionsDict[position][2]],
                          popup=self.positionsDict[position][0]).add_to(m)
        m.save('map.html')


gtfs = gtfsData()

import json
import webbrowser
from datetime import datetime
from urllib.request import urlopen
from geopy.distance import distance
from folium.plugins import TimestampedGeoJson
from google.transit import gtfs_realtime_pb2
import folium
from google.protobuf.json_format import MessageToDict


# todo: make a pin per train
# todo: segment railways on discord for better path
# todo: add delays

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


def retrieveCoordinates():
    coordinates = []
    with open('sortedTravels.txt', 'r') as travels:
        for i, line in enumerate(travels):
            if i > 0:
                longitude = float(line.split(',')[0])
                latitude = float(line.split(',')[1])
                epochTime = float(line.split(',')[2])
                coordinates.append({"coordinates": [latitude, longitude],
                                    "time": datetime.fromtimestamp(float(epochTime)).isoformat() + "Z"})
        return coordinates


def sortLines():
    with open('unsortedTravels.txt', 'r') as f_input:
        lines = f_input.readlines()
        lines = [line.strip().split(',') for line in lines]  # split each line into a list of values

        sortedLines = sorted(lines, key=lambda line: int(line[-1]))  # sort the lines based on the epoch value

        uniqueLines = []  # create an empty list to store the unique lines
        prevLine = None  # initialize prevLine variable to None
        for line in sortedLines:
            if line != prevLine:  # check if the line is different from the previous line
                uniqueLines.append(line)  # add the line to the uniqueLines list
                prevLine = line  # set the prevLine variable to the current line

    return uniqueLines


def writeSortedTravels():
    uniqueLines = sortLines()
    with open('sortedTravels.txt', 'a+') as f_output:
        for line in uniqueLines:
            f_output.write(','.join(line) + '\n')


def createGeoJSON():
    coordinates = retrieveCoordinates()
    print(coordinates)

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
    path = "C:/Users/maeva/Desktop/geo/gtfs/stops.txt"
    # path = "/home/maedekey/Bureau/geo/gtfs/stops.txt"

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
    if len(stations) < 2:
        return 0
    travelTime = int(stations[3]) - int(stations[2])
    averageSpeed = distance / travelTime
    return averageSpeed


def locateTrain(speed, stations, distanceStations, currentTime):
    time = currentTime - int(stations[2])
    trainDistance = speed * time
    ratio = trainDistance / distanceStations

    longitude = float(stations[0][1]) + (float(stations[1][1]) - float(stations[0][1])) * ratio
    latitude = float(stations[0][2]) + (float(stations[1][2]) - float(stations[0][2])) * ratio
    return [longitude, latitude]


def visualizeTrains():
    belgium_coords = [51.17147, 4.142963]
    m = folium.Map(location=belgium_coords, zoom_start=8)

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


def writeStaticObjectCoordinates(i, previousPosition, stations):
    distanceStations = calculateDistance(stations)
    speed = calculateAverageSpeed(stations, distanceStations)
    previousPosition = [locateTrain(speed, stations, distanceStations, i)]
    with open('unsortedTravels.txt', 'a+') as travels:
        travels.write(f"{previousPosition[0][0]},{previousPosition[0][1]},{i}\n")
        travels.close()
    return previousPosition


def writeMovingobjectCoordinates(i, previousPosition, stations):
    with open('unsortedTravels.txt', 'a+') as travels:
        travels.write(f"{stations[0][1]},{stations[0][2]},{i}\n")
        travels.close()
    previousPosition = [stations[0][1], stations[0][2]]
    return previousPosition


class gtfsData:
    def __init__(self):
        url = "file:///C:/Users/maeva/Desktop/geo/1680127355.gtfsrt"
        # url = "file:////home/maedekey/Bureau/geo/1680202355.gtfsrt"

        gtfsDict = preprocessing(url)

        self.gtfsValues = list(gtfsDict.values())[1]
        self.positionsDict = findStationPositions()


        self.findTrainLocation()
        visualizeTrains()


    def findTrainLocation(self):
        startTime = self.findStartTime()
        endTime = self.gtfsValues[5]['tripUpdate']['stopTimeUpdate'][-1]['arrival']['time']
        previousPosition = None
        previousTripId = None
        for i in range(startTime, int(endTime), 60):
            stations, previousTripId = self.findStations(i, previousTripId)

            if len(stations) == 1 and [stations[0][1], stations[0][2]] != previousPosition:
                previousPosition = writeMovingobjectCoordinates(i, previousPosition, stations)

            elif len(stations) > 1:
                previousPosition = writeStaticObjectCoordinates(i, previousPosition, stations)

        writeSortedTravels()

    def findStations(self, currentTime, previousTripId):
        stops = self.gtfsValues[5]['tripUpdate']['stopTimeUpdate']
        for i in range(len(stops) - 1):
            if self.gtfsValues[5]['tripUpdate']['trip']['tripId'] != previousTripId:
                previousTripId = self.gtfsValues[5]['tripUpdate']['trip']['tripId']

            if int(stops[i]['departure']['time']) < currentTime < int(stops[i + 1]['arrival']['time']):
                return [self.positionsDict[stops[i]['stopId']], self.positionsDict[stops[i + 1]['stopId']],
                        stops[i]['departure']['time'], stops[i + 1]['arrival']['time']], previousTripId

            elif i < len(stops) - 2:
                if int(stops[i + 1]['departure']['time']) >= currentTime >= int(stops[i + 1]['arrival']['time']):
                    return [self.positionsDict[stops[i + 1]['stopId']]], previousTripId
            else:
                return [self.positionsDict[stops[i + 1]['stopId']]], previousTripId

    def findStartTime(self):
        startTime = self.gtfsValues[5]['tripUpdate']['trip']['startTime']
        startDate = self.gtfsValues[5]['tripUpdate']['trip']['startDate']
        startDateTime = datetime.strptime(startDate + startTime, '%Y%m%d%H:%M:%S')
        epochTime = int(startDateTime.timestamp())
        return epochTime

    def visualizeStations(self):
        belgium_coords = [50.5039, 4.4699]
        m = folium.Map(location=belgium_coords, zoom_start=8)
        for position in self.positionsDict:
            folium.Marker([self.positionsDict[position][1], self.positionsDict[position][2]],
                          popup=self.positionsDict[position][0]).add_to(m)
        m.save('map.html')


gtfs = gtfsData()

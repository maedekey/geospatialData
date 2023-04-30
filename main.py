import json
import webbrowser
from datetime import datetime
from urllib.request import urlopen
from geopy.distance import distance
from folium.plugins import TimestampedGeoJson
from google.transit import gtfs_realtime_pb2
import folium
from google.protobuf.json_format import MessageToDict

# todo: make a pin per trip
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
        for line in travels:
            longitude = float(line.split(',')[0])
            latitude = float(line.split(',')[1])
            epochTime = float(line.split(',')[2])
            coordinates.append({"coordinates": [latitude, longitude],
                                "time": datetime.fromtimestamp(float(epochTime)).isoformat() + "Z"})
    return coordinates


def sortLines():
    # Open the input and output files
    with open('unsortedTravels.txt', 'r') as f_input, open('sortedTravels.txt', 'w') as f_output:
        # Read the lines from the input file
        lines = f_input.readlines()

        # Sort the lines based on the last parameter
        sorted_lines = sorted(lines, key=lambda line: int(line.split(',')[-1]))

        # Write the sorted lines to the output file
        f_output.writelines(sorted_lines)


def createGeoJSON():
    coordinates = retrieveCoordinates()
    print(coordinates)
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
    m = folium.Map(location=belgium_coords, zoom_start=10)

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
        previousPosition = None
        for i in range(1680048000, 1680134400, 30):
            stations = self.findStations(i)

            if len(stations) == 1 and [stations[0][1], stations[0][2]] != previousPosition:
                with open('unsortedTravels.txt', 'a+') as travels:
                    travels.write(f"{stations[0][1]},{stations[0][2]},{i}\n")
                    travels.close()
                previousPosition = [stations[0][1], stations[0][2]]

            elif len(stations) > 1:
                distanceStations = calculateDistance(stations)
                speed = calculateAverageSpeed(stations, distanceStations)
                with open('unsortedTravels.txt', 'a+') as travels:
                    travels.write(f"{stations[0][1]},{stations[0][2]},{i}\n")
                    travels.close()
                previousPosition = [locateTrain(speed, stations, distanceStations, i)]
        sortLines()

    def findStations(self, currentTime):
        stops = self.gtfsValues[5]['tripUpdate']['stopTimeUpdate']
        for i in range(len(stops) - 1):
            if int(stops[i]['departure']['time']) < currentTime < int(stops[i + 1]['arrival']['time']):
                return [self.positionsDict[stops[i]['stopId']], self.positionsDict[stops[i + 1]['stopId']],
                        stops[i]['departure']['time'], stops[i + 1]['arrival']['time']]
            elif i < len(stops) - 2:
                if int(stops[i + 1]['departure']['time']) >= currentTime >= int(stops[i + 1]['arrival']['time']):
                    return [self.positionsDict[stops[i + 1]['stopId']]]
            else:
                return [self.positionsDict[stops[i + 1]['stopId']]]

    def visualizeStations(self):
        belgium_coords = [50.5039, 4.4699]
        m = folium.Map(location=belgium_coords, zoom_start=8)
        for position in self.positionsDict:
            folium.Marker([self.positionsDict[position][1], self.positionsDict[position][2]],
                          popup=self.positionsDict[position][0]).add_to(m)
        m.save('map.html')


gtfs = gtfsData()

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
# todo: parametrize paths of gtfs directory and gtfsrt file


def preprocessing(url):
    """
    Allows to retrieve the gtfsrt file content and put it into a dictionary
    :param url: path of the file under the url format
    :return: the dictionary object
    """
    gtfs_realtime = gtfs_realtime_pb2.FeedMessage()
    gtfs_realtime.ParseFromString(urlopen(url).read())
    dict_obj = MessageToDict(gtfs_realtime)
    return dict_obj


def addLocations(stopId, line, positionsDict):
    """
    Function that allows retrieving the name, longitude and latitude of a station based on its ID
    :param stopId: ID of the station
    :param line: line of the file "stops.txt", where all the information about stations are written
    :param positionsDict: dictionary to which is appended the new location, longitude and latitude
    as values, and the stopID as key
    :return: dictionary mentioned earlier
    """

    location = line.split(',')[2]
    longitude = line.split(',')[4]
    lattitude = line.split(',')[5]

    positionsDict[stopId] = [location, longitude, lattitude]


def retrieveCoordinates():
    """
    Function that allows retrieving coordinates from the sortedTravels.txt file and add it into a
    coordinate object, used to create a json object
    :return: the coordinate object
    """
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
    """
    Function that allows storing the files lines into a list. Then, this list is sorted based on the
    time (epoch format), and all the consecutive duplicates are deleted.
    What we call consecutive duplicates is: at different moments, the object has same longitude and
    same latitude
    :return: sorted list without consecutive duplicates
    """
    with open('unsortedTravels.txt', 'r') as f_input:
        lines = f_input.readlines()
        lines = [line.strip().split(',') for line in lines]

        sortedLines = sorted(lines, key=lambda line: int(line[-1]))

        # delete all consecutive duplicates
        uniqueLines = []
        prevLine = None
        for line in sortedLines:
            if line != prevLine:
                uniqueLines.append(line)
                prevLine = line

    return uniqueLines


def writeSortedTravels():
    """
    Function that writes in a "storedTravels.txt" all the sorted and non duplicated lines of the trip
    """
    uniqueLines = sortLines()
    with open('sortedTravels.txt', 'a+') as f_output:
        for line in uniqueLines:
            f_output.write(','.join(line) + '\n')


def createGeoJSON():
    """
    Function that creates a geoJSON object. We pass it coordinates so the pin on the map can move
    according to a determined time
    :return:
    """
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
    """
    Opens the gtfs/stops.txt and retrieves each line. In each line, we retrieve the information of
    the station, based on the stopID.
    IMPORTANT: please change the path to the location of your gtfs/stops.txt file
    :return: the dictionary containing the stopID as the key and the rest of infos as values.
    """
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
    """
    Function that computes the distance between a train and the station it left,
    based on their longitude and latitude
    :param stations: the object containing the position of the train and the station
    :return: the distance between the train and the station
    it returns 0 if the train is in the station (which means it's stopped)
    """
    if len(stations) > 1:
        stationDistance = distance([float(stations[0][1]), float(stations[0][2])],
                                   [float(stations[1][1]), float(stations[1][2])]).m
        return stationDistance
    else:
        return 0


def calculateAverageSpeed(stations, stationDistance):
    """
    Calculates the speed of the train based on the time that it has been traveling and the distance
    it has traveled from the previous station
    :param stationDistance: distance between the train and the station
    :param stations: object containing the current time and the time the train left the station
    :return: the average speed of the train between 2 stations
    """
    if len(stations) < 2:
        return 0
    travelTime = int(stations[3]) - int(stations[2])
    averageSpeed = stationDistance / travelTime
    return averageSpeed


def locateTrain(speed, stations, distanceStations, currentTime):
    """
    Function that allows retrieving the longitude and latitude of the train based on its speed and
    the last station it departed from, and the distance between itself and the station it departed
    from
    :param speed: the average speed of the train
    :param stations: the distance between the station it has to arrive to, and it departed from
    :param distanceStations: the distance between the 2 stations that the train is between
    :param currentTime: the time at which the train is at this longitude, latitude
    :return: the longitude and the latitude of the current position of the train
    """
    time = currentTime - int(stations[2])
    trainDistance = speed * time
    ratio = trainDistance / distanceStations

    longitude = float(stations[0][1]) + (float(stations[1][1]) - float(stations[0][1])) * ratio
    latitude = float(stations[0][2]) + (float(stations[1][2]) - float(stations[0][2])) * ratio
    return [longitude, latitude]


def visualizeTrains():
    """
    Function that allows visualizing moving trains on a map. First we create a map and center it
    on a set of coordinates. Then, we create a geoJSOn object, define its parameters, save it into
    and html file and open the html
    :return:
    """
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


def writeMovingTrainsCoordinates(i, previousPosition, stations):
    """
    Function that writes in a file the positions of the train and the moments of the positions,
    when it is moving between stations
    :param i: instant at which the train is located on such coordinates
    :param previousPosition: the previous position of the train (will be needed later)
    :param stations: object containing details needed for the called functions, that will
    retrieve the position of the train
    :return: the position written in the file
    """
    distanceStations = calculateDistance(stations)
    speed = calculateAverageSpeed(stations, distanceStations)
    position = [locateTrain(speed, stations, distanceStations, i)]
    with open('unsortedTravels.txt', 'a+') as travels:
        travels.write(f"{position[0][0]},{position[0][1]},{i}\n")
        travels.close()
    return position


def writeStaticTrainsCoordinates(i, previousPosition, stations):
    """
    Function writing coordinates of trains when they're stopped in stations.
    :param i: The current moment
    :param previousPosition: The previous position of the train (will be needed later)
    :param stations: The current position of the train
    :return: the actual position of the train
    """
    with open('unsortedTravels.txt', 'a+') as travels:
        travels.write(f"{stations[0][1]},{stations[0][2]},{i}\n")
        travels.close()
    position = [stations[0][1], stations[0][2]]
    return position


class gtfsData:
    def __init__(self):
        """
        IMPORTANT: replace the url by the location of your gtfsrt file (UNDER URL FORMAT!!)
        This method extracts gtfsValues and stores them into a dictionary. Then it locates
        the train coordinates and shows them on a map
        """
        url = "file:///C:/Users/maeva/Desktop/geo/1680127355.gtfsrt"
        # url = "file:////home/maedekey/Bureau/geo/1680202355.gtfsrt"

        gtfsDict = preprocessing(url)
        self.gtfsValues = list(gtfsDict.values())[1]
        self.positionsDict = findStationPositions()

        self.findTrainLocation()
        visualizeTrains()

    def findTrainLocation(self):
        """
        Function that:
        First, we define an interval of time on which we will establish the positions of the train.
        To do this, we look at the start time of the trip, and the end time, which is the moment the
        train reaches its final destination.
        Then, we iterate over this interval of time, every 60 seconds to visualize the train at
        every minute. Then we check if the train is moving or stopped, and write accordingly in the file.
        Finally, we sort all of these coordinates, in function of the time.
        :return:
        """
        startTime = self.findStartTime()
        endTime = self.gtfsValues[5]['tripUpdate']['stopTimeUpdate'][-1]['arrival']['time']
        previousPosition = None
        previousTripId = None
        for i in range(startTime, int(endTime), 60):
            stations, previousTripId = self.findStations(i, previousTripId)

            if len(stations) == 1 and [stations[0][1], stations[0][2]] != previousPosition:
                previousPosition = writeStaticTrainsCoordinates(i, previousPosition, stations)

            elif len(stations) > 1:
                previousPosition = writeMovingTrainsCoordinates(i, previousPosition, stations)

        writeSortedTravels()

    def findStations(self, currentTime, previousTripId):
        """
        Function that retrieves all the stops of the train during the trip. Then, for each of these
        stops, we check if the current time is before or after the departure/arrival time.
        If the current time is before the arrival time but after the departure train, it means the
        train is moving between 2 stations, so we return the time and the position of the 2 stations
        it is between. otherwise, it means it's stopped and we return the position of the station
        it's waiting at.
        :param currentTime: self-explanatory
        :param previousTripId: not used yet, but important later
        :return:
        """
        stops = self.gtfsValues[5]['tripUpdate']['stopTimeUpdate']
        for i in range(len(stops) - 1):

            if self.gtfsValues[5]['tripUpdate']['trip']['tripId'] != previousTripId:
                # not used yet but important later
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
        """
        Function that finds the starting time of a trip.
        :return: the starting time under epoch format
        """
        startTime = self.gtfsValues[5]['tripUpdate']['trip']['startTime']
        startDate = self.gtfsValues[5]['tripUpdate']['trip']['startDate']
        startDateTime = datetime.strptime(startDate + startTime, '%Y%m%d%H:%M:%S')
        epochTime = int(startDateTime.timestamp())
        return epochTime

    def visualizeStations(self):
        """
        Not used
        :return:
        """
        belgium_coords = [50.5039, 4.4699]
        m = folium.Map(location=belgium_coords, zoom_start=8)
        for position in self.positionsDict:
            folium.Marker([self.positionsDict[position][1], self.positionsDict[position][2]],
                          popup=self.positionsDict[position][0]).add_to(m)
        m.save('map.html')


gtfs = gtfsData()

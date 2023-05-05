import json
import os
import webbrowser
from datetime import datetime
from urllib.request import urlopen
from folium.plugins import TimestampedGeoJson
from google.transit import gtfs_realtime_pb2
import folium
from google.protobuf.json_format import MessageToDict
import osm



def preprocessing(url):
    print("processing: ", url)
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
    Function that allows retrieving coordinates from the travels.txt file and add it into a
    coordinate object, used to create a json object
    :return: the coordinate object
    """
    previousTripId = '0\n'
    coordinatesSet = []
    coordinates = []
    index = 0
    with open('travels.txt', 'r') as travels:
        for i, line in enumerate(travels):
            tripId = line.split(',')[3]
            if previousTripId != tripId:
                coordinatesSet.append(coordinates.copy())
                coordinates = []
                previousTripId = tripId
                index = 0
            longitude = float(line.split(',')[1])
            latitude = float(line.split(',')[0])
            epochTime = float(line.split(',')[2])
            coordinates.append({"coordinates": [latitude, longitude],
                                "time": datetime.fromtimestamp(float(epochTime)).isoformat() + "Z"})
            index += 1
        coordinatesSet.append(coordinates.copy())
        return coordinatesSet


def testGeoJson():
    feature_collection = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[3.6859148, 50.4101452], [3.6918031, 50.4115532]]
            },
            "properties": {
                "times": ['2023-03-27T21:02:00Z', '2023-03-27T21:04:00Z']
            }
        }]
    }
    return [feature_collection]


def createGeoJSON():
    """
    Function that creates a geoJSON object. We pass it coordinates so the pin on the map can move
    according to a determined time
    :return:
    """
    coordinatesSet = retrieveCoordinates()

    # for coordinates in coordinatesSet:
    #    coordinates[0]['coordinates'] = coordinates[1]['coordinates']
    geoJSONSet = []
    for i in range(len(coordinatesSet)):
        print(coordinatesSet[i])
        feature_collection = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [coord["coordinates"] for coord in coordinatesSet[i]]
                },
                "properties": {
                    "times": [coord["time"] for coord in coordinatesSet[i]]
                }
            }]
        }
        geoJSONSet.append(feature_collection.copy())
    return geoJSONSet


def findStationPositions():
    """
    Opens the gtfs/stops.txt and retrieves each line. In each line, we retrieve the information of
    the station, based on the stopID.
    IMPORTANT: please change the path to the location of your gtfs/stops.txt file
    :return: the dictionary containing the stopID as the key and the rest of infos as values.
    """
    # path = "C:/Users/maeva/Desktop/geo/gtfs/stops.txt"
    path = "data/gtfs/stops.txt"

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


def visualizeTrains():
    """
    Function that allows visualizing moving trains on a map. First we create a map and center it
    on a set of coordinates. Then, we create a geoJSOn object, define its parameters, save it into
    and html file and open the html
    :return:
    """
    belgium_coords = [51.17147, 4.142963]
    m = folium.Map(location=belgium_coords, zoom_start=8)

    geoJSONSet = createGeoJSON()

    # Add the GeoJSON data to the map
    for feature_collection in geoJSONSet:
        # create TimestampedGeoJson object for the current feature collection
        geojson = TimestampedGeoJson(
            json.dumps(feature_collection),
            period="PT1S",  # update frequency in seconds
            add_last_point=True,  # add a marker at the last point of the trajectory
            auto_play=True,  # autoplay the animation
            loop=True,  # loop the animation
        )

        # add the TimestampedGeoJson object to the map

        geojson.add_to(m)

    # Show the map in PyCharm
    m.save("map.html")
    webbrowser.open('map.html')


class gtfsData:
    def __init__(self):
        """
        IMPORTANT: replace the url by the location of your gtfsrt file (UNDER URL FORMAT!!)
        This method extracts gtfsValues and stores them into a dictionary. Then it locates
        the train coordinates and shows them on a map
        """
        file = "data/1679954735.gtfsrt"
        # url = "file:///C:/Users/maeva/Desktop/geo/1680127355.gtfsrt"
        cwd = os.getcwd()
        full_path = os.path.join(cwd, file)
        url = 'file://' + full_path

        gtfsDict = preprocessing(url)
        self.gtfsValues = list(gtfsDict.values())[1]
        self.positionsDict = findStationPositions()
        for i in range(187,189):
            self.findTrainLocation(i)
        visualizeTrains()

    def findTrainLocation(self, trip):
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

        # on retrieve toutes les stations du trip
        startTime = float(self.findStartTime(trip))
        endTime = float(self.gtfsValues[trip]['tripUpdate']['stopTimeUpdate'][-1]['arrival']['time'])
        stations = self.findStations(trip)
        osm.retrieveTripCoordinates(stations, startTime, trip)

    def findStations(self, trip):
        """
        Function that retrieves all the stops of the train during the trip. Then, for each of these
        stops, we check if the current time is before or after the departure/arrival time.
        If the current time is before the arrival time but after the departure train, it means the
        train is moving between 2 stations, so we return the time and the position of the 2 stations
        it is between. otherwise, it means it's stopped and we return the position of the station
        it's waiting at.
        :param trip:
        :return:
        """
        res = []
        stops = self.gtfsValues[trip]['tripUpdate']['stopTimeUpdate']
        for i in range(len(stops) - 1):

            if 'arrival' not in stops[i + 1]:
                stops[i + 1]['arrival'] = {'delay': stops[i + 2]['departure']['delay'],
                                           'time': stops[i + 2]['departure']['time']}
            res.append([self.positionsDict[stops[i]['stopId']], self.positionsDict[stops[i + 1]['stopId']],
                        stops[i]['departure']['time'], stops[i + 1]['arrival']['time']])
        return res

    def findStartTime(self, trip):
        """
        Function that finds the starting time of a trip.
        :return: the starting time under epoch format
        """
        startTime = "21:00:00"
        startDate = self.gtfsValues[trip]['tripUpdate']['trip']['startDate']
        startDateTime = datetime.strptime(startDate + startTime, '%Y%m%d%H:%M:%S')
        epochTime = int(startDateTime.timestamp())
        return epochTime

#gtfs = gtfsData()

import time

from shapely.geometry import LineString, Point
import csv
import json

"""
General idea: when a train has to go from one station to another, retrieve station positions. Then, find segments in the
csv file between these 2 stations, and calculate their length. Return list of segments + length of the segments.
This will allow to find average speed of the train. 
d = v*t. We will obtain the distance at which the train is from the path. 
then, extrapolate and blablabla like chatgpt said
"""


def retrieveStationIds(stations):
    # liste = [['Quievrain', '50.4101100', '3.68608000'], ['Thulin', '50.4233300', '3.74470800'], '1680117240', '1680117480']
    departureStationCoords = [stations[0][1], stations[0][2]]
    arrivalStationCoords = [stations[1][1], stations[1][2]]


def findPath(departureCoordinates, arrivalCoordinates):
    file = "C:/Users/maeva/Desktop/geo/trajectories.csv"
    csv.field_size_limit(10485760)
    with open(file, mode='r', newline='') as csv_file:
        # Create a CSV reader object
        paths = []
        paths = addSegments(paths, csv_file, departureCoordinates, departureCoordinates, arrivalCoordinates)
        print(paths)


def addSegments(path, csv_file, currentCoordinates, departureCoordinates, arrivalCoordinates):
    csv_reader = csv.reader(csv_file, delimiter=';', quotechar='"')
    csv_file.seek(0)
    next(csv_reader)
    print("looking for :", currentCoordinates)
    for row in csv_reader:

        data = json.loads(row[1])
        for coordinate in data['coordinates']:
            if findCoordinates(coordinate, currentCoordinates, departureCoordinates, arrivalCoordinates):

                path.append([coordinate[0], coordinate[1]])
                path = addSegments(path, csv_file, coordinate, departureCoordinates, arrivalCoordinates)

    return path


def findCoordinates(coordinates1, coordinates2, departure, arrival):
    latRounded, longRounded = roundCoordinates(coordinates1, coordinates2)
    precision = 0.0029
    if departure[0] > arrival[0] and departure[1] > arrival[1]:
        # 50.___ . on doit se déplacer vers le - pour les 2
        if coordinates2[0] > longRounded > coordinates2[0] - precision and coordinates2[1] > latRounded > coordinates2[1] - precision:
            return True
    elif departure[0] > arrival[0] and departure[1] < arrival[1]:
        # on doit se déplacer vers le - pour 50 et vers le + pour 4
        if coordinates2[0] > longRounded > coordinates2[0] - precision and coordinates2[1] < latRounded < coordinates2[1] + precision:
            return True
    elif departure[0] < arrival[0] and departure[1] > arrival[1]:
        # on doit se déplacer vers le + pour 50 et vers le - pour 4
        if coordinates2[0] < longRounded < coordinates2[0] + precision and coordinates2[1] > latRounded > coordinates2[1] - precision:
            return True
    elif departure[0] < arrival[0] and departure[1] < arrival[1]:
        if coordinates2[0] < longRounded < coordinates2[0] + precision and coordinates2[1] < latRounded < coordinates2[1]+ precision:
            return True

    return False


def roundCoordinates(coordinates1, coordinates2):
    latRoundNumber, longRoundNumber = 7, 7
    latStr, longStr = str(coordinates2[0]), str(coordinates2[1])
    i = len(latStr) - 1
    while latStr == '0' and i >= 0:
        latRoundNumber -= 1
        i -= 1
    latRounded = round(coordinates1[0], latRoundNumber)
    j = len(longStr) - 1
    while longStr == '0' and j >= 0:
        longRoundNumber -= 1
        j -= 1
    longRounded = round(coordinates1[1], longRoundNumber + 1)
    return latRounded, longRounded


stations = [['Waremme', '50.6945500', '5.24948000'], ['Bleret', '50.6850700', '5.28639800'], '1680126240', '1680126360']
findPath([float(stations[0][1]), float(stations[0][2])], [float(stations[1][1]), float(stations[1][2])])
# findCoordinates([50.41011199005315, 3.685692209790285], ['50.4101100', '3.68608000'])

"""# define the coordinates of the starting and ending stations
start_station = Point(4.585837405556894, 51.14354071364106)
end_station = Point(4.58742606503013, 51.143618759998155)

# define a threshold for proximity to a station
proximity_threshold = 0.0001

# define a list to store candidate segments
candidate_segments = []
path = "C:/Users/maeva/Desktop/geo/trajectories.csv"
# iterate through each line in the CSV file
with open('path_segments.csv', 'r') as f:
    for line in f:
        # extract the start and end coordinates from the line
        start_coords, linestring, segment_id = line.strip().split(';')
        start_lon, start_lat = map(float, start_coords.split(','))
        end_lon, end_lat = map(float, linestring.split('[')[1].split(']')[0].split(',')[3:5])

        # create Point objects for the start and end coordinates
        start_point = Point(start_lon, start_lat)
        end_point = Point(end_lon, end_lat)

        # check if either the start or end point is close enough to one of the two stations
        if start_point.distance(start_station) < proximity_threshold or end_point.distance(
                start_station) < proximity_threshold:
            candidate_segments.append(LineString([[start_lon, start_lat], [end_lon, end_lat]]))
        elif start_point.distance(end_station) < proximity_threshold or end_point.distance(
                end_station) < proximity_threshold:
            candidate_segments.append(LineString([[start_lon, start_lat], [end_lon, end_lat]]))

# define a list to store the final path
final_path = []

# create a straight line connecting the starting and ending stations
straight_line = LineString([start_station.coords[0], end_station.coords[0]])

# iterate through the candidate segments and identify which intersect or are close to the straight line
for segment in candidate_segments:
    if segment.distance(straight_line) < proximity_threshold or segment.intersects(straight_line):
        final_path.append(segment)

# concatenate the final path
full_path = LineString([p.coords[0] for segment in final_path for p in segment.coords])

print(full_path)"""

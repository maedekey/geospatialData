import itertools
import osmnx as ox
from geopy.distance import distance

"""
General idea: when a train has to go from one station to another, retrieve station positions. Then, find segments in the
csv file between these 2 stations, and calculate their length. Return list of segments + length of the segments.
This will allow to find average speed of the train. 
d = v*t. We will obtain the distance at which the train is from the path. 
then, extrapolate and blablabla like chatgpt said
"""


def retrieveTripCoordinates(stations, startTime, trip):
    """[float(station[0][1]), float(station[0][2])],
                                                                 [float(station[1][1]), float(station[1][2])]"""
    place_name = "Belgium"
    #changer: for stations in list: calculer le shortest path

    # G = ox.graph_from_place(place_name, custom_filter='["railway"]')
    G = ox.load_graphml('/home/maedekey/PycharmProjects/pythonProject/railwayGraph.graphml')
    for station in stations:

        routeNodes = extractCoordinates(G, station)

        startTime = writeInFile(routeNodes, startTime, station, trip)


def extractCoordinates(G, station):
    station1 = ox.nearest_nodes(G, float(station[0][2]), float(station[0][1]))
    station2 = ox.nearest_nodes(G, float(station[1][2]), float(station[1][1]))
    route = ox.shortest_path(G, station1, station2)
    routeNodes = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route]
    routeNodes = [key for key, group in itertools.groupby(routeNodes)]
    distances = 0
    if len(routeNodes)> 1:
        for i in range(len(routeNodes) - 1):
            distances += distance([routeNodes[i][0], routeNodes[i][1]],
                                  [routeNodes[i+1][0], routeNodes[i+1][1]]).m

    return routeNodes


def writeInFile(routeNodes, startTime, station, trip):

    tripTime = float(station[3]) - float(station[2])
    for i in range(len(routeNodes)):
        totalTime = tripTime / len(routeNodes)
        startTime += totalTime
        with open('travels.txt', 'a+') as travels:
            travels.write(f"{routeNodes[i][1]},{routeNodes[i][0]},{int(startTime)},{trip}\n")
            travels.close()

    return startTime


import itertools
import osmnx as ox
from geopy.distance import distance
import os


def retrieveTripCoordinates(stations, startTime, trip):
    graphPath = '/home/maedekey/PycharmProjects/pythonProject/railwayGraph.graphml'
    if os.path.exists(graphPath):
        G = ox.load_graphml('/home/maedekey/PycharmProjects/pythonProject/railwayGraph.graphml')
    else:
        place_name = "Belgium"
        G = ox.graph_from_place(place_name, custom_filter='["railway"]')

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
    if len(routeNodes) > 1:
        for i in range(len(routeNodes) - 1):
            distances += distance([routeNodes[i][0], routeNodes[i][1]],
                                  [routeNodes[i + 1][0], routeNodes[i + 1][1]]).m

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

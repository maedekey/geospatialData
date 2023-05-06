import itertools
import osmnx as ox
from geopy.distance import distance
import os


def retrieveTripCoordinates(startTime, trip):
    graphPath = 'railwayGraph.graphml'
    if os.path.exists(graphPath):
        G = ox.load_graphml(graphPath)
    else:
        place_name = "Belgium"
        G = ox.graph_from_place(place_name, custom_filter='["railway"]')
        ox.save_graphml(G, graphPath)

    for i in range(len(trip)-1):
        routeNodes = extractCoordinates(G, trip[i], trip[i+1])
        startTime = writeInFile(routeNodes, startTime, trip[i], trip[i+1])


def extractCoordinates(G, station1, station2):
    station1 = ox.nearest_nodes(G, float(station1[3]), float(station1[2]))
    station2 = ox.nearest_nodes(G, float(station2[3]), float(station2[2]))
    route = ox.shortest_path(G, station1, station2)
    routeNodes = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route]
    routeNodes = [key for key, group in itertools.groupby(routeNodes)]
    distances = 0
    if len(routeNodes) > 1:
        for i in range(len(routeNodes) - 1):
            distances += distance([routeNodes[i][0], routeNodes[i][1]],
                                  [routeNodes[i + 1][0], routeNodes[i + 1][1]]).m

    return routeNodes


def writeInFile(routeNodes, startTime, station1, station2):
    tripTime = station2[4] - station1[4]
    for i in range(len(routeNodes)):
        totalTime = tripTime / len(routeNodes)
        startTime += totalTime
        with open('travels.txt', 'a+') as travels:
            travels.write(f"{routeNodes[i][1]},{routeNodes[i][0]},{int(startTime)}\n")
            travels.close()

    return startTime

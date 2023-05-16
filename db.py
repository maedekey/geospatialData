import psycopg2
import os
import common

"""
Run this program to initialize a table loaded with GTFSRT data. To use this code, you need to create a database called
traindb, and set the user 'postgres' password to 'password'
"""


def main():
    """
    Function to run to initialize the db, import gtfsrt data in it, and print the content of the table
    :return:
    """
    con, cur = connectToDB()
    createTable(cur)
    importGTFSRTData(cur)
    printTable(con, cur)
    cur.close()
    con.close()


def connectToDB():
    """
    Function that connects to the traindb database
    :return: the connection and the cursor, used to make queries to the database
    """
    conn = psycopg2.connect(database="traindb", user="postgres", password="password", host="localhost", port="5432")
    cur = conn.cursor()
    return conn, cur


def createTable(cur):
    """
    Method that reinitializes and creates a table called 'station'
    :param cur: the cursor needed to make the query
    :return:
    """
    cur.execute("DROP TABLE IF EXISTS station;")
    cur.execute('''CREATE TABLE station
               (id SERIAL PRIMARY KEY,
                nameStation TEXT,
                latStation FLOAT,
                longStation FLOAT,
                arrivalTime INT,
                trip INT);''')


def insertInTable(cur, data):
    """
    Function that allows to insert a set of GTFSRT data into the table
    :param cur: cursor needed to make the query
    :param data: data to insert in the table
    :return:
    """
    cur.execute("INSERT INTO station (nameStation, latStation, longStation, arrivalTime, trip) VALUES (%s, %s, %s, "
                "%s, %s)",
                (data[0][0], float(data[0][1]), float(data[0][2]), int(data[1]), data[2]))


def printTable(conn, cur):
    """
    Method that prints the content of the database
    :param conn: connection to the database
    :param cur: cursor needed to make queries to the database
    :return:
    """
    cur.execute("SELECT * FROM station")
    conn.commit()
    rows = cur.fetchall()
    for row in rows:
        print(row)


def loadGtfsData(cur, url, counter):
    """
    Function that loads the GTFSRT data into a database. We iterate through the GTFSRT dictionary, retrieve the
    tripupdate field, iterate through it, find the station positions of each trip, then insert in a postgresql table
    the station names, their location, the time at which the train arrived at this station, and the tripID, which allows
    us to identify the stops belonging to a same trip (i.e. stops with the same tripId belong to the same trip).
    :param cur: cursor used to make db queries
    :param url: gtfsrt data location under the url format
    :param counter: number of the trip being processed, which allows us to identify trips
    :return: counter
    """
    positionsDict = common.findStationPositions()
    gtfsDict = common.preprocessing(url)
    if gtfsDict:
        if len(gtfsDict) == 2:
            gtfsValues = list(gtfsDict.values())[1]
            if gtfsValues:
                for i in range(len(gtfsValues)):
                    res = findStations(gtfsValues, positionsDict, i, counter)
                    if res:
                        print(counter)
                        counter += 1
                        for station in res:
                            insertInTable(cur, station)
    return counter


def importGTFSRTData(cur):
    """
    Method that retrieves all the .GTFSRT files in the data directory and loads the gtfsrt data
    :param cur: cursor used to make db queries
    :return:
    """
    dataPath = "data/"
    files = os.listdir(dataPath)
    # files = [files[0], files[1]]
    counter = 0
    for file in files:
        cwd = os.getcwd()
        full_path = os.path.join(cwd, dataPath + file)
        url = 'file://' + full_path
        if url.endswith(".gtfsrt"):
            try:
                counter = loadGtfsData(cur, url, counter)
            except:
                print("Couldn't open file " + url)


def findStations(gtfsrtValues, positionsDict, trip, counter):
    """
    Function that finds the corresponding coordinates and names of a stopID element in the gtsfrt data. Also fills the
    gaps, if 'departure' and 'arrival' are non-existent for a stopID.
    :param gtfsrtValues:
    :param positionsDict: a dictionary containing stopID as a key, and a name and coordinates as a value
    :param trip:
    :param counter:
    :return:
    """
    res = []
    stops = gtfsrtValues[trip]['tripUpdate']['stopTimeUpdate']
    if len(stops) > 1:
        for i in range(len(stops)):
            if i == len(stops) - 1:
                res.append([positionsDict[stops[i]['stopId']],
                            stops[i]['arrival']['time'], counter])

            else:
                if 'departure' not in stops[i] and i > 0:
                    stops[i]['departure'] = {'delay': stops[i - 1]['departure']['delay'],
                                             'time': stops[i - 1]['departure']['time']}
                if 'departure' in stops[i]:
                    res.append([positionsDict[stops[i]['stopId']],
                                stops[i]['departure']['time'], counter])

        return res


# main()


def retrievePath(conn, trip):
    """
    Function that finds all the stops for a given tripID
    :param conn: connection to the db
    :param trip: tripID to identify the trip and its corresponding stations
    :return: found stations having the asked tripID
    """
    cur = conn.cursor()
    cur.execute("select * from station where trip = %s", (trip,))
    conn.commit()
    rows = cur.fetchall()
    cur.close()
    return rows


def retrieveStations(arrivalStation, departureStation):
    """
    Function that finds a common tripID for an arrival station and a destination station
    :param arrivalStation: list of tuples of (arrivalStations, tripID) (only the tripID changes)
    :param departureStation: list of tuples of (departureStations, tripID) (only the tripID changes)
    :return: tuples with tripID in common
    """
    stationDico = {}
    for station in departureStation:
        keyTrip = station[-1]
        if keyTrip in stationDico:
            stationDico[keyTrip].append(station)
        else:
            stationDico[keyTrip] = [station]
    validDepartureStation = []
    validArrivalStation = []
    for station in arrivalStation:
        keyTrip = station[-1]
        if keyTrip in stationDico:
            validDepartureStation.append(stationDico[keyTrip])
            validArrivalStation.append(station)
    return validArrivalStation, validDepartureStation


def retrieveArrivalStation(conn, station, epoch):
    """
    Function that retrieves a list of stations according to a name and a time
    :param conn: the connection to the db
    :param station: the name of the station asked
    :param epoch: the epoch time
    :return: the matching stations
    """
    cur = conn.cursor()
    cur.execute("select * from station where nameStation = %s and arrivalTime > %s", (station, epoch,))
    conn.commit()
    rows = cur.fetchall()
    cur.close()
    return rows


def retrieveDepartureStation(conn, station, epoch):
    """
    Function that retrieves a list of stations according to a name and a time
    :param conn: the connection to the db
    :param station: the name of the station asked
    :param epoch: the epoch time
    :return: the matching stations
    """
    cur = conn.cursor()
    cur.execute("select * from station where nameStation = %s and arrivalTime < %s", (station, epoch,))
    conn.commit()
    rows = cur.fetchall()
    cur.close()
    return rows


if __name__ == '__main__':
    main()

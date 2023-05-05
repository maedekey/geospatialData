import psycopg2
import visualization
import os

"""
sudo -u postgres psql
CREATE USER geoProject WITH PASSWORD 'geoProject';
CREATE USER geoDataProject WITH PASSWORD 'password';

CREATE DATABASE traindb;
GRANT ALL PRIVILEGES ON DATABASE traindb TO geoProject;
"""


def main():
    con, cur = connectToDB()
    createTable(cur)
    importGtfsData(cur)
    printTable(con, cur)
    cur.close()
    con.close()


def connectToDB():
    conn = psycopg2.connect(database="traindb", user="postgres", password="password", host="localhost", port="5432")
    cur = conn.cursor()
    return conn, cur


def createTable(cur):
    cur.execute("DROP TABLE IF EXISTS station;")
    cur.execute('''CREATE TABLE station
               (id SERIAL PRIMARY KEY,
                nameStation TEXT,
                latStation FLOAT,
                longStation FLOAT,
                arrivalTime INT,
                trip INT);''')


def insertInTable(cur, data):
    cur.execute("INSERT INTO station (nameStation, latStation, longStation, arrivalTime, trip) VALUES (%s, %s, %s, "
                "%s, %s)",
                (data[0][0], float(data[0][1]), float(data[0][2]), int(data[1]), data[2]))


def printTable(conn, cur):
    cur.execute("SELECT * FROM station")
    conn.commit()
    rows = cur.fetchall()
    for row in rows:
        print(row)


def loadGtfsData(cur, url):
    positionsDict = visualization.findStationPositions()
    gtfsDict = visualization.preprocessing(url)
    if gtfsDict:
        if len(gtfsDict) == 2:
            gtfsValues = list(gtfsDict.values())[1]
            if gtfsValues:
                for i in range(len(gtfsValues)):
                    res = findStations(gtfsValues, positionsDict, i)
                    if res:
                        for station in res:
                            insertInTable(cur, station)


def importGtfsData(cur):
    dataPath = "data/"
    files = os.listdir(dataPath)

    for file in files:
        cwd = os.getcwd()
        full_path = os.path.join(cwd, dataPath+file)
        url = 'file://' + full_path
        if url.endswith(".gtfsrt"):
            loadGtfsData(cur, url)


def findStations(gtfsValues, positionsDict, trip):
    res = []
    stops = gtfsValues[trip]['tripUpdate']['stopTimeUpdate']
    if len(stops) > 1:
        for i in range(len(stops)):
            if i == len(stops)-1:
                res.append([positionsDict[stops[i]['stopId']],
                            stops[i]['arrival']['time'], trip])
            else:
                if 'departure' not in stops[i] and i > 0:
                    stops[i]['departure'] = {'delay': stops[i - 1]['departure']['delay'],
                                             'time': stops[i - 1]['departure']['time']}
                if 'departure' in stops[i]:
                    res.append([positionsDict[stops[i]['stopId']],
                                stops[i]['departure']['time'], trip])

        return res


main()

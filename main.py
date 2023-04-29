from urllib.request import urlopen
from google.transit import gtfs_realtime_pb2
from google import protobuf
from google.protobuf.json_format import MessageToDict


def preprocessing(url):
    gtfs_realtime = gtfs_realtime_pb2.FeedMessage()
    gtfs_realtime.ParseFromString(urlopen(url).read())
    dict_obj = MessageToDict(gtfs_realtime)
    return dict_obj


class gtfsData:
    def __init__(self):
        url = "file:////home/maedekey/Bureau/geo/1680127202.gtfsrt"
        gtfsDict = preprocessing(url)
        print(gtfsDict)


gtfs = gtfsData()

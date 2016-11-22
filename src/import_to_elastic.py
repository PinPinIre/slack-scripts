import sys
import os
import json
from datetime import datetime
from elasticsearch import Elasticsearch, ElasticsearchException


def get_file_names(dir_path):
    """
    Get a list of json files in the dir_path directory
    """
    # TODO: Surely this could be written better?
    files = []
    for filename in os.listdir(dir_path):
        path = os.path.join(dir_path, filename)
        if os.path.isfile(path) and path.endswith('.json'):
            files.append(path)
    return files


def normalise_json_ts(json):
    """
        Normalise the slack json data
    """
    if 'ts' in json:
        json['ts'] = convert_ts_to_date(float(json['ts']))
    if 'attachments' in json:
        json['attachments'] = list(map(normalise_json_ts, json['attachments']))
    return json


def import_json(dir_path):
    """
        Import all the json files from the dir_path directory
    """
    file_names = get_file_names(dir_path)
    json_files = {}
    for file_name in file_names:
        with open(file_name) as json_data:
            temp_json = json.load(json_data)
            # TODO: Try to remember if this is the pythonic way
            list(map(normalise_json, temp_json))
            json_files[file_name] = temp_json
    return json_files


def convert_ts_to_date(ts):
    """
        Converts a timestamp to a date object
    """
    # TODO: is this function necessary?
    return datetime.fromtimestamp(ts)


def export_to_elastic(json_files, index):
    """
        Export a dict of JSON files to elastic search
    """
    es = Elasticsearch()
    es.indices.create(index=index)
    for key, json_array in json_files.items():
        for idx, json in enumerate(json_array):
            try:
                res = es.index(index=index, doc_type='slack-message',
                               id=key+str(idx), body=json)
            except ElasticsearchException as elasticEx:
                print(json)
                print(elasticEx)
                sys.exit()
    es.indices.refresh(index=index)
    return "Success!"


def main():
    if len(sys.argv) > 2 and os.path.isdir(sys.argv[1]):
        # TODO: Better error handling and parsing of this
        json_files = import_json(sys.argv[1])
        success = export_to_elastic(json_files, sys.argv[2])
        print success
    else:
        print "Wrong Params!"

if __name__ == "__main__":
    main()

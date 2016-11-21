import sys
import os


def get_file_names(dir_path):
    return None


def transform_data(data):
    return data


def import_json(dir_path):
    file_names = get_file_names(dir_path)
    for file in file_names:
        # TODO: Read json files and do manipulations
        # Maybe have a passed in function to do this? transform_data(?)
        continue
    return None


def export_to_elastic(json):
    # TODO: Read elastic config from somewhere
    # TODO: Push the data to elastic
    return None


def main():
    if len(sys.argv) > 1 and os.path.isDir(sys.argv[1]):
        json = import_json(sys.argv[1])
        success = export_to_elastic(json)
    else:
        print "None"

if __name__ == "__main__":
    main()

#!/bin/env python3 
import sys
import yaml
import pkg_resources

CONFIG_FILE_PATH = pkg_resources.resource_filename(__name__, "tag.yaml")

class MyTag():
    tag_map = {}

    def __init__(self):
        try:
            with open(CONFIG_FILE_PATH) as fp:
                config = yaml.load(fp, Loader=yaml.FullLoader)
        except:
            print("Fail to load %s" %CONFIG_FILE_PATH)
            sys.exit()

        for tag in config['tags'][0].keys():
            self.tag_map[tag] = config['tags'][0][tag]

if __name__ == "__main__":
    tag = MyTag()

    for item in tag.tag_map.keys():
        print("%-10s : %s" %(item, tag.tag_map[item]))
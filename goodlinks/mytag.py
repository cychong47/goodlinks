#!/bin/env python3
"""Tagging"""

import os
import sys
from pathlib import Path

import yaml
#import pkg_resources
import newspaper
import nltk

nltk.download("punkt", quiet=True)

#CONFIG_FILE_PATH = pkg_resources.resource_filename(__name__, "tag.yaml")
CONFIG_FILE_PATH = os.environ.get("TAG_FILE", "tag.yaml")


class Tagging:
    """MyTag class"""

    tag_map = {}

    def __init__(self):
        try:
            with open(CONFIG_FILE_PATH) as fp:
                config = yaml.load(fp, Loader=yaml.FullLoader)
        except:
            print(f"Fail to load {CONFIG_FILE_PATH}")
            sys.exit()

        for tag in config["tags"][0].keys():
            self.tag_map[tag] = config["tags"][0][tag]

    @staticmethod
    def get_keyword_and_title(url: str):
        """Get keywords and title from the given URL"""

        article = newspaper.Article(url)

        try:
            article.download()
        except KeyboardInterrupt:
            print("User interruption")
            sys.exit(0)

        if article.html != "":
            article.parse()

        try:
            article.nlp()
        except Exception as err:
            print(f"fail to NLP {err}")
            return [], ""

        return article.keywords, article.title

    @staticmethod
    def get_keyword_from_text(text: str) -> list:
        """Get keywords from the given text"""

        tokens = set(nltk.word_tokenize(text))
        tokens = [token.lower() for token in tokens]
        return tokens


if __name__ == "__main__":
    tagger = Tagging()

    for k, v in tagger.tag_map.items():
        print(f"{k:-10s} : {v}")

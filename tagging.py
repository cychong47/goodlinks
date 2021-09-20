#!/usr/bin/env python3

import newspaper
import sys
import nltk

nltk.download('punkt', quiet=True)

def get_keyword_and_title(url):
    a = newspaper.Article(url)

    try:
        a.download()
    except KeyboardInterrupt:
        print("User interruption")
        sys.exit(0)

    if a.html != '': 
        a.parse()

    try:
        a.nlp()
    except Exception as err:
        #print(f"fail to NLP {err}")
        return [], ""

    return a.keywords, a.title

if __name__ == "__main__":
    get_keyword("")

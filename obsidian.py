#!/usr/bin/env python

import argparse
import datetime
import pathlib
import os
import sys
import goodlinks

example_text = """
example:
    %(prog)s --date 2021-09-04
    %(prog)s --today
"""
class Obsidian():
    def __init__(self, req_date):
        self.dn_file = f"""{os.environ["HOME"]}/Library/Mobile Documents/iCloud~md~obsidian/Documents/Notes/01. Daily Notes/{req_date}.md"""

    def check_if_dn_is_exist(self):
        if pathlib.Path(self.dn_file).is_file():
            self.dn_note_is_exist = True
        else: 
            self.dn_note_is_exist = False

        return self.dn_note_is_exist

    def check_if_note_has_goodlinks(self):
        """Return True if Daily Notes has a Goodlinks section"""

        # if note is not eixst, just say note has links already
        if not self.dn_note_is_exist:
            return True

        with open(self.dn_file, 'r') as fp:
            for line in fp.readlines():
                if "## Goodlinks" in line:
                    print("Daily notes has already Goodlinks section.")
                    return True
        
        return False

    def append_to_note(self, links):
        """Append links to Daily Notes"""
        if not self.dn_note_is_exist:
            return

        # Find out what LF is needed
        first_line = ''
        with open(self.dn_file, 'r') as fp:
            buf = fp.readlines()

            if buf[-1] != '\n':
                first_line = "\n\n"

        with open(self.dn_file, 'a') as fp:
            fp.write(first_line)
            fp.write("## Goodlinks\n")

            count = 0
            for link in links:
                fp.write(f"""- [{link['title']}]({link['url']}) """)
                tags = link.get('tags', "")
                if tags:
                    for tag in tags.split():
                        fp.write(f"#{tag} ")
                fp.write("\n")
                count += 1
            print(f"Append {count} links to Daily Notes")
#!/usr/bin/env python3

import argparse
import datetime
import os
import sys
import sqlite3
import pathlib
import tagging

class Goodlinks():

    def __init__(self, verbose=None, db_file=""):
        self.verbose = 0
        if verbose == 1:
            self.verbose = 1

        self.db_file = db_file
        if db_file == "":
            self.db_file = os.environ["HOME"]+"""/Library/Group Containers/group.com.ngocluu.goodlinks/Data/data.sqlite"""
        
        if self.verbose == 1:
            print(f"DB : {self.db_file}")

        self.table_name = "link"
        self.connect_to_db()
            
    def connect_to_db(self):
        try:
            self.db = sqlite3.connect(self.db_file)
        except:
            print(f"Fail to connect DB file {self.db_file}")
            sys.exit(0)

        self.cursor = self.db.cursor()

        # move to the last record
        #self.cursor.lastrowid
        #self.db.commit()
    
    def get_tables(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return self.cursor.fetchall()

    def print_tables(self):
        print("== Table in this database")
        for index, item in enumerate(self.get_tables()):
            print(f"{index:4} {item[0]}")
    
    def get_fields(self, table):
        """Get fields of record"""

        cmd = f"PRAGMA table_info('{table}')"
        result = self.cursor.execute(f"PRAGMA table_info('{table}')").fetchall()
        return list(zip(*result))[1]
    
    def print_fields(self, table):
        print(f"== Fields of table {table} ==")
        for index, item in enumerate(self.get_fields(table)):
            print(f"{index:4} {item}")

    def _get_date_filter(self, date=None):
        if date != None:
            ts_per_day = 24*60*60 
            target_ts = datetime.datetime.strptime(date, "%Y-%m-%d").timestamp()
            return f"WHERE addedAt >= {target_ts} and addedAt < {target_ts + ts_per_day}"
        else:
            return ""

    def get_records(self, table, date=""):
        date_filter = self._get_date_filter(date)

        buf = f"SELECT * FROM {table} {date_filter} ORDER BY addedAt DESC"
        self.cursor.execute(buf)

        return self.cursor.fetchall()

    def _print_record(self, data):
        buf = ""
        if self.verbose == 1:
            print("-"*120)
            print(f"{data['title']:<20}")
            print(f"{'':<2} : {data['url']:<20}")
#            print(f"{'':<2} : {time.ctime(data['addedAt'])}")
            if data['tags'] != None:
                print(f"{'':<2} : ")
                for tag in data['tags'].split():
                    print(f"#{tag}", end=" ")
                print()
        else:
            print(f"""- [{data['title']}]({data['url']})""", end=" ")
            tags = data.get('tags') or ""
            for tag in tags.split():
                print(f"#{tag}", end=" ")
            print()

    def print_records(self, table, req_tag=None, req_date=None, limit=10):
        fields = self.get_fields(table)
        values = self.get_records(table, req_date)

        count = 0
        for index, value in enumerate(values, start=1):
            data = dict(zip(fields, value))

            if req_tag != None:
                if data['tags'] == None:
                    continue
                elif req_tag not in data['tags']:
                    continue
            count += 1
            self._print_record(data)

            if limit > 0 and index >= limit:
                return count

        return count
    
    def get_links(self, table, req_date=None):
        """Return links of the given date"""
        fields = self.get_fields(table)
        values = self.get_records(table, req_date)

        data = []
        for index, value in enumerate(values, start=1):
            data.append(dict(zip(fields, value)))

        return data

    def _update_tag(self, data):
        """ return 1 if tag is udpated otherwise return 0"""

        id = data['id']
        url = data['url']
        title = data['title']
        old_tags = data.get('tags', "") or "" # to avoid error in "x not in old_tags"

        my_tag = (
            'kubernetes', 'rust', 'cargo', 'go', 'ebpf',
            'python', 'fastapi', 'generator', 'iterator', 'jupyter', 'numpy', 'pandas', 'seaborn',
            'obsidian', 'note-taking', 'journaling',
            'helm', 'container', 'observability',
            'aws'
        )

        if False:
            ## temporal code to replace " twitter youtube" to "youtube"
            tag_map = {"youtubekubernetes": "youtube kubernetes",
                        "youtubeobservability": "youtube observability",
                        "youtubeobsidian": "youtube obsidian",
                        "youtubepython": "youtube python"}

            for x in tag_map.keys():
                if old_tags == None:
                    return None

                if x in old_tags:
                    new_tags = old_tags.replace(x, tag_map[x])
                    self.cursor.execute(f"""UPDATE link SET tags = "{new_tags}" WHERE id='{id}'""")
                    self.db.commit()
                    return new_tags

            return old_tags


        extracted_keyword, a_title = tagging.get_keyword_and_title(url)
        if extracted_keyword != []:
            if self.verbose:
                print(extracted_keyword)

            b = [x for x in extracted_keyword if x in my_tag and x not in old_tags]
            if b != []:
                new_tags = old_tags + ' ' + ' '.join(b)
                self.cursor.execute(f"""UPDATE link SET tags = "{new_tags}" WHERE id='{id}'""")
                self.db.commit()

        # simple tag for twitter and youtube
        target_tags = ( 
                ["on Twitter", "twitter"], 
                ["- YouTube", "youtube"]
                )

        new_tags = old_tags
        for keyword, tag in target_tags:
            if title == None:
                title = a_title 
            if keyword in title:
                if old_tags is None:
                    new_tags = tag
                elif tag not in old_tags:
                    new_tags = f"{old_tags} {tag}"

                if new_tags != old_tags:
                    print(f"Update tag : {old_tags} -> {new_tags}")
                    self.cursor.execute(f"""UPDATE link SET tags = "{new_tags}" WHERE id='{id}'""")
                    self.db.commit()

                return 0 if new_tags == old_tags else 1

        return 0 if new_tags == old_tags else 1
    
    def update_tag(self, table, req_date=None):
        """Update tag of records"""
        fields = self.get_fields(table)
        values = self.get_records(table, req_date)

        count = 0
        if self.verbose:
            print(f"Process {len(values)} items on {req_date}")
        for index, item in enumerate(values, start=1):
            data = dict(zip(fields, item))
            count += self._update_tag(data)
        
        if count:
            print(f"Updated record : {count}")

    def append_to_obsidian(self, update, req_date):
        dn_file = f"""{os.environ["HOME"]}/Library/Mobile Documents/iCloud~md~obsidian/Documents/Notes/01. Daily Notes/{args.date}.md"""
        if pathlib.Path(dn_file).is_file():
            # check if already Goodlinks sections are present
            with open(dn_file, 'r') as fp:
                for line in fp.readlines():
                    if "## Goodlinks" in line:
                        print("Daily notes has already Goodlinks section.")
                        return

        # need to update tag first if not 
        if not update:
            self.update_tag(self.table_name, args.date)

        links = self.get_links(self.table_name, req_date)
        if pathlib.Path(dn_file).is_file():
            first_line = ''
            with open(dn_file, 'r') as fp:
                buf = fp.readlines()

                if buf[-1] != '\n':
                    first_line = "\n\n"

            with open(dn_file, 'a') as fp:
                fp.write(first_line)
                fp.write("## Goodlinks\n")

                for link in links:
                    fp.write(f"""- [{link['title']}]({link['url']}) """)
                    tags = link.get('tags') or ""
                    for tag in tags.split():
                        fp.write(f"#{tag}")
                    fp.write("\n")
            print("Append to Daily Notes")
        else:
            print(f"File is not exist {dn_file}")

    # output to json
    # http://stackoverflow.com/questions/3286525/return-sql-table-as-json-in-python
    #cursor.execute('SELECT * FROM vm_list WHERE state == 1')
    #r = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in cursor.fetchall()]
    #json_output = json.dumps(r)
    #print json_output

if __name__ == "__main__":
    # update/list/obsidian
    parser = argparse.ArgumentParser() #epilog=example_text)
    parser.add_argument("-c", "--count", type=int, default=10)
    parser.add_argument("--date", "-d", action="store")
    parser.add_argument("--today", action="store_const", const=1, help=f"same to --date with today")
    parser.add_argument("--verbose", action="store_const", const=1, help="print details of each item")

    parser.add_argument("--tables", action="store_const", const=1, help="print tables")
    parser.add_argument("--tag", "-t", action="store")
    parser.add_argument("--fields", action="store_const", const=1, help="print fields of tables")

    parser.add_argument("--update", action="store_const", const=1, help="update tag")
    parser.add_argument("--obsidian", action="store_const", const=1, help="Update obsidian Daily Notes tag")
    args = parser.parse_args()

    goodlinks = Goodlinks(args.verbose)

    if args.tables == 1:
        goodlinks.print_tables()

    if args.fields == 1:
        goodlinks.print_fields('link')
        goodlinks.print_fields('state')

    if args.today == 1:
        args.date = datetime.datetime.now().strftime("%Y-%m-%d")

    if args.update == 1:
        goodlinks.update_tag('link', args.date)
    
    if args.obsidian == 1:
        goodlinks.append_to_obsidian(args.update, args.date)
    else:
        count = goodlinks.print_records('link', args.tag, args.date, -1)
        print(f"{count} on {args.date}")
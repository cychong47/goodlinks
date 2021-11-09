#!/usr/bin/env python3

import argparse
import datetime
import os
import sys
import sqlite3
import pathlib
import tagging
import obsidian

class Goodlinks():

    def __init__(self, verbose=0, db_file=""):
        self.verbose = verbose

        self.db_file = db_file
        if db_file == "":
            self.db_file = os.environ["HOME"]+"""/Library/Group Containers/group.com.ngocluu.goodlinks/Data/data.sqlite"""
        
        if self.verbose:
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
        """Get table field names"""
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
        """Get table data"""
        date_filter = self._get_date_filter(date)

        buf = f"SELECT * FROM {table} {date_filter} ORDER BY addedAt DESC"
        self.cursor.execute(buf)

        return self.cursor.fetchall()

    def _print_record(self, data):
        buf = ""
        if self.verbose:
            print("-"*120)
            try:
                print(f"{data['title']:<20}")
            except:
                print("No title")
            print(f"  url {'':<2} : {data['url']:<20}")
#            print(f"{'':<2} : {time.ctime(data['addedAt'])}")
            if data['tags'] != None:
                print(f"  tag {'':<2} : ", end="")
                for tag in data['tags'].split():
                    print(f"#{tag}", end=" ")
                print()
        else:
            print(f"""- [{data['title']}]({data['url']})""", end=" ")
            tags = data.get('tags') or ""
            for tag in tags.split():
                print(f"#{tag}", end=" ")
            print()
            
    def _print_record_simple(self, data):
        """rint title only without link """
        print(f"""- {data['title']}""", end=" ")
        tags = data.get('tags') or ""
        for tag in tags.split():
            print(f"#{tag}", end=" ")
        print()

    def print_records(self, table, reqs, args):
        fields = self.get_fields(table)
        values = self.get_records(table, reqs.date)

        count = 0
        for index, value in enumerate(values, start=1):
            data = dict(zip(fields, value))

            count += 1
            if reqs.tag != None:
                if not data['tags'] or reqs.tag not in data['tags']:
                    continue

            if args.verbose:
                self._print_record(data)
            else:
                self._print_record_simple(data)

            if reqs.count != -1 and index >= reqs.count:
                return count

        return count
    
    def get_links(self, req_date=None):
        """Return links of the given date"""

        fields = self.get_fields(self.table_name)
        values = self.get_records(self.table_name, req_date)

        data = []
        for _, value in enumerate(values, start=1):
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
                if not old_tags:
                    return None

                if x in old_tags:
                    new_tags = old_tags.replace(x, tag_map[x])
                    self.cursor.execute(f"""UPDATE link SET tags = "{new_tags}" WHERE id='{id}'""")
                    self.db.commit()
                    return new_tags

            return old_tags

        extracted_keyword, a_title = tagging.get_keyword_and_title(url)
        if extracted_keyword != []:
            if self.verbose > 1:
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
            title = a_title if not title else title
            if keyword in title:
                if not old_tags:
                    new_tags = tag
                elif tag not in old_tags:
                    new_tags = f"{old_tags} {tag}"

                if new_tags != old_tags:
                    print(f"Update tag) {old_tags} -> {new_tags}")
                    self.cursor.execute(f"""UPDATE link SET tags = "{new_tags}" WHERE id='{id}'""")
                    self.db.commit()

                return 0 if new_tags == old_tags else 1

        return 0 if new_tags == old_tags else 1
    
    def update_tag(self, req_date=None):
        """ Update tag of records"""

        fields = self.get_fields(self.table_name)
        values = self.get_records(self.table_name, req_date)

        count = 0
        if self.verbose:
            print(f"Process {len(values)} items on {req_date}")
        for index, item in enumerate(values, start=1):
            data = dict(zip(fields, item))
            count += self._update_tag(data)
        
        if count:
            print(f"Updated record : {count}")

    def append_to_obsidian(self, update, req_date):
        """append to Obsidian Today Notes"""
        if not update:
            self.update_tag(req_date)

        ob_note = obsidian.Obsidian(req_date)
        if not ob_note.check_if_dn_is_exist():
            print(f"{req_date} : No MD file")

        if not ob_note.check_if_note_has_goodlinks():
            links = self.get_links(req_date)
            if links:
                ob_note.append_to_note(links)
            else:
                print(f"No links to append")


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
#    parser.add_argument("--today", action="store_const", const=1, help=f"same to --date with today")
    parser.add_argument("--week", action="store_const", const=1, help=f"process for last one week")

    parser.add_argument("--verbose", action="count", default=0, help="print details of each item")

    parser.add_argument("--tables", action="store_const", const=1, help="print tables")
    parser.add_argument("--tag", "-t", action="store")
    parser.add_argument("--fields", action="store_const", const=1, help="print fields of tables")

    parser.add_argument("--update", action="store_const", const=1, help="update tag")
    parser.add_argument("--obsidian", action="store_const", const=1, help="Update obsidian Daily Notes tag")
    args = parser.parse_args()

    goodlinks = Goodlinks(args.verbose)

    if args.tables:
        goodlinks.print_tables()

    if args.fields:
        goodlinks.print_fields('link')
        goodlinks.print_fields('state')

    if args.date:
        d = args.date.split('-')
        base_date = datetime.datetime(int(d[0]), int(d[1]), int(d[2]))
    else:
        base_date = datetime.datetime.now() #.strftime("%Y-%m-%d")

    if args.week:
        base_date = datetime.datetime.now() - datetime.timedelta(days=6)
        day_offset_list = [x for x in range(0,7)]
    else:
        day_offset_list = [0]

    print("-"*os.get_terminal_size().columns)
    for day_offset in day_offset_list:
        t = base_date + datetime.timedelta(days=day_offset)
        t_date = t.strftime("%Y-%m-%d")

        if args.update:
            goodlinks.update_tag(t_date)

        if args.obsidian:
            goodlinks.append_to_obsidian(args.update, t_date)
        else:
            reqs = argparse.Namespace()
            reqs.tag = args.tag
            reqs.date = t_date
            reqs.count = -1

            count = goodlinks.print_records(table='link', reqs=reqs, args=args)
            print(f"\n{count} on {t_date}")
            
            print("-"*os.get_terminal_size().columns)

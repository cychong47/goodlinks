#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import sys
import time
import sqlite3

class Goodlinks():

    def __init__(self, verbose=None, debug=False, db_file=""):
        if db_file != "":
            self.db_file = db_file
        else:
            self.db_file = os.environ["HOME"]+"""/Library/Group Containers/group.com.ngocluu.goodlinks/Data/data.sqlite"""
        
        if debug == True:
            print(f"DB filename : {self.db_file}")

        self.connect_to_db()

        self.verbose = 0
        if verbose == 1:
            self.verbose = 1
            
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
        result = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()

        return tables

    def print_tables(self):
        tables = self.get_tables()

        print("== Tables in the DB ==")
        for index, item in enumerate(tables):
            print(f"{index:4} {item[0]}")
    
    def get_fields(self, table):
        """Get fields of record"""

        cmd = f"PRAGMA table_info('{table}')"
        result = self.cursor.execute(f"PRAGMA table_info('{table}')").fetchall()
        return list(zip(*result))[1]
    
    def print_fields(self, table):
        result = self.get_fields(table)

        print(f"== Fields of table {table} ==")
        for index, item in enumerate(result):
            print(f"{index:4} {item}")

    def get_records(self, table, order_by=""):
        if order_by != "":
            self.cursor.execute(f"SELECT * FROM {table} ORDER BY addedAt DESC")
        else:
            self.cursor.execute(f"SELECT * FROM {table}")

        return self.cursor.fetchall()

    def _print_record(self, data):
        if self.verbose == 1:
            for key in ['addedAt', 'url', 'title', 'tags']:
                if data[key] is None:
                    return
                if key in ['addedAt', 'modifiedAt'] :
                    print(f"{key:<12} : {time.ctime(data[key])} {data[key]}")
                else:  
                    try:
                        print(f"{key:<12} : {data[key]:<20}")
                    except TypeError:
                        print(f"Error {key}")
        else:
            print(f"""- [{data['title']}]({data['url']})""", end=" ")
            tags = data.get('tags') or ""
            for tag in tags.split():
                print(f"#{tag}", end=" ")
            print()

    def print_records(self, table, tag=None, date=None, limit=10):
        fields = self.get_fields(table)
        values = self.get_records(table)


        count = 0
        for index, value in enumerate(values, start=1):
            data = dict(zip(fields, value))

            if tag != None:
                if data['tags'] == None:
                    continue
                elif tag not in data['tags']:
                    continue

            if date != None:
                if date != datetime.datetime.fromtimestamp(data['addedAt']).strftime("%Y-%m-%d"):
                    continue

            count += 1
            self._print_record(data)

            if limit > 0 and index >= limit:
                return count

        return count
    

    def _update_tag(self, id, title, old_tags):

        if False:
            ## temporal code to replace " twitter youtube" to "youtube"
            try:
                if " twitter youtube" in old_tags:
                    new_tags = old_tags.replace(" twitter youtube", "youtube")
                    print(f"{id} tags is updated from ({old_tags}) to ({new_tags})")
                    self.cursor.execute(f"""UPDATE link SET tags = "{new_tags}" WHERE id='{id}'""")
                    self.db.commit()
                    return new_tags
            except:
                return old_tags

        target_tags = ( 
                ["on Twitter", "twitter"], 
                ["- YouTube", "youtube"]
                )

        new_tags = old_tags
        for keyword, tag in target_tags:
            if keyword in title:
                if old_tags is None:
                    new_tags = tag
                elif tag not in old_tags:
                    new_tags = f"{old_tags} {tag}"

                if new_tags != old_tags:
                    print(f"{id} tags is updated {old_tags} -> {new_tags}")
                    self.cursor.execute(f"""UPDATE link SET tags = "{new_tags}" WHERE id='{id}'""")
                    self.db.commit()

                return new_tags

        return new_tags
    
    def update_tag(self, table):
        """Update tag of records"""
        fields = self.get_fields(table)
        values = self.get_records(table)

        count = 0
        for index, item in enumerate(values, start=1):
            data = dict(zip(fields, item))

            tags = data['tags']
            title = data['title']
            id = data['id']

            if title != None:
                new_tags = self._update_tag(id, title, tags)

                if tags != new_tags:
                    count += 1
        
        print(f"{count} is updated")

    def get_db(self):
        return self.db
    
    def get_cursor(self):
        return self.cursor


def main(args):

    with sqlite3.connect(args.db) as connection:
        cursor = connection.cursor()

        cursor.lastrowid
        connection.commit()

        # Get Table list
        result = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
    #    print(tables)
    #    print(list(zip(tables)))
    #    print(list(zip(*tables))[0])

        # Get fields of table 'link'
        result = cursor.execute("PRAGMA table_info('link')").fetchall()
        column_names = list(zip(*result))[1]
    #    print(list(zip(*result)))
    #    print(list(zip(result)))

        print("\ncolumn names for links:")
        print(column_names)

        # Get all records from table 'link'
        cursor.execute("SELECT * FROM link ORDER BY addedAt DESC")
        ret =  cursor.fetchall()

        print(f"Total {len(ret)} links")
        for index, item in enumerate(ret, start=1):
            data = dict(zip(column_names, item))

            tags = data['tags']
            title = data['title']
            id = data['id']

            if title != None:
                tags = update_tag(cursor, id, title, tags)

    #        for field, value in zip(column_names, item):

            continue
            for field, value in zip(column_names, item):
                if value == None:
                    continue
    #            if field in ['preview', 'fetchStatus', 'id', 'summary', 'modifiedAt', 'starred']:
    #                continue
                if field not in ['url', 'title', 'addedAt', 'tags']:
                #if field not in ['addedAt']:
                    continue
                if field in ['addedAt', 'modifiedAt'] :
                    print(f"{field:<12} : {time.ctime(value)}")
                else:  
                    print(f"{field:<12} : {value:<20}")
            if index > 3:
                break

        #for row in cursor:
        #    print "%16s   %7s %16s %16s %10u %10u" %(row[0], "active" if row[1] == 1 else "disable", row[2], row[3], row[4], row[5])


        # output to json
        # http://stackoverflow.com/questions/3286525/return-sql-table-as-json-in-python
        #cursor.execute('SELECT * FROM vm_list WHERE state == 1')
        #r = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in cursor.fetchall()]
        #json_output = json.dumps(r)
        #print json_output

if __name__ == "__main__":
    parser = argparse.ArgumentParser() #epilog=example_text)
    parser.add_argument("-c", "--count", type=int, default=10)
    parser.add_argument("--tag", "-t", action="store")
    parser.add_argument("--date", "-d", action="store")
    parser.add_argument("--today", action="store_const", const=1, help=f"same to --date with today")
    parser.add_argument("--verbose", action="store_const", const=1, help="print details of each item")
    parser.add_argument("--tables", action="store_const", const=1, help="print tables")
    parser.add_argument("--fields", action="store_const", const=1, help="print fields of tables")
    parser.add_argument("--update", action="store_const", const=1, help="update tag")
    args = parser.parse_args()

    goodlinks = Goodlinks(args.verbose)

    if args.tables == 1:
        goodlinks.print_tables()

    if args.fields == 1:
        goodlinks.print_fields('link')
        goodlinks.print_fields('state')

    if args.update:
        goodlinks.update_tag('link')
    else:
        if args.today == 1 or args.date != None:
            if args.today == 1:
                args.date = datetime.datetime.now().strftime("%Y-%m-%d")
            count = goodlinks.print_records('link', args.tag, args.date, -1)
            print(f"{count} on {args.date}")
        else:
            print("TBD WHAT TO DO?? DAILY LINK COUNT?")
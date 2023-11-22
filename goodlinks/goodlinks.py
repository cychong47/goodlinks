#!/usr/bin/env python3

import argparse
import datetime
import os
import sys
import sqlite3
import pathlib
import time
from mytag import Tagging
import obsidian
import pandas as pd
import pprint
import urllib.request
from bs4 import BeautifulSoup as bf


class Goodlinks:
    def __init__(self, verbose=0, tag_update=True, db_file=""):
        self.verbose = verbose

        self.db_file = db_file
        if db_file == "":
            self.db_file = (
                os.environ["HOME"]
                + """/Library/Group Containers/group.com.ngocluu.goodlinks/Data/data.sqlite"""
            )

        if self.verbose:
            print(f"DB : {self.db_file}")

        if not pathlib.Path(self.db_file).is_file():
            raise Exception("Goodlinks data file is not found")

        self.table_name = "link"

        self.connect_to_db()

        self.fields = self.get_fields(self.table_name)

        if tag_update:
            mytag = Tagging()
            self.my_tag_map = mytag.tag_map

    def connect_to_db(self):
        try:
            self.db = sqlite3.connect(self.db_file)
        except sqlite3.Error:
            print(f"Fail to connect DB file {self.db_file}")
            sys.exit(0)

        print("Connect to database file")

        self.cursor = self.db.cursor()

    def get_tables(self):
        """Get Tables"""

        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return self.cursor.fetchall()

    def print_tables(self):
        """Print tables"""

        print("== Table in this database")
        for index, item in enumerate(self.get_tables()):
            print(f"{index:4} {item[0]}")

    def get_fields(self, table):
        """Get fields of record"""

        result = self.cursor.execute(f"PRAGMA table_info('{table}')").fetchall()
        return list(zip(*result))[1]

    def print_fields(self, table):
        """Get table field names"""

        print(f"== Fields of table {table} ==")
        for index, item in enumerate(self.get_fields(table)):
            print(f"{index:4} {item}")

    def _get_date_filter(self, date=None):
        if date:
            ts_per_day = 24 * 60 * 60
            target_ts = datetime.datetime.strptime(date, "%Y-%m-%d").timestamp()
            return (
                f"WHERE addedAt >= {target_ts} and addedAt < {target_ts + ts_per_day}"
            )
        else:
            return ""

    def get_records(self, table, date=""):
        """Get table data"""
        date_filter = self._get_date_filter(date)

        buf = f"SELECT * FROM {table} {date_filter} ORDER BY addedAt DESC"
        self.cursor.execute(buf)

        return self.cursor.fetchall()

    def _print_record(self, index, data):
        if self.verbose:
            try:
                print(f"""[{index:2}] {data['title']:<20}""")
            except KeyError:
                print(f"""[{index:2}] No title""")
            if self.verbose > 1:
                print(f"     url {'':<2} : {data['url']:<20}")
            #            print(f"{'':<2} : {time.ctime(data['addedAt'])}")
            if data["tags"]:
                print(f"     tag {'':<2} : ", end="")
                for tag in data["tags"].split():
                    print(f"#{tag}", end=" ")
                print()
        else:
            print(f"""- [{data['title']}]({data['url']})""", end=" ")
            tags = data.get("tags") or ""
            for tag in tags.split():
                print(f"#{tag}", end=" ")
            print()

    def _print_tag(self, tags):
        if tags:
            print(f"     tag {'':<2} : ", end="")
            for tag in tags.split():
                print(f"#{tag}", end=" ")
            print()

    def _print_record_simple(self, index, data):
        """rint title only without link"""

        read_flag = "R" if data["readAt"] else " "
        print(f"""{read_flag}[{index:2}] {data['title']}""", end="   ")

        tags = data.get("tags") or ""
        for tag in tags.split():
            print(f"#{tag}", end=" ")
        print()

    def _print_title(self, index, data):
        read_flag = "R" if data["readAt"] else " "

        if data.get("title", "No title"):
            print(f"""[{read_flag}{index:2}] {data['title']:<20}""")
        else:
            print(f"""[{read_flag}{index:2}] No title""")

        if self.verbose > 1:
            print(f"     url {'':<2} : {data['url']:<20}")

    def print_records(self, table, reqs, args):
        values = self.get_records(table, reqs.date)

        read_count = 0
        total_count = 0
        for index, value in enumerate(values, start=1):
            data = dict(zip(self.fields, value))

            tags = data.get("tags", [])
            if args.update:
                _, tags = self._update_tag(data)

            if reqs.tag:
                if not data["tags"] or reqs.tag not in data["tags"]:
                    continue

            # only count all conditions are met such as tag is matched
            total_count += 1
            read_count += 1 if data["readAt"] else 0

            if args.verbose:
                self._print_title(index, data)
            else:
                self._print_record_simple(index, data)

            if args.verbose:
                self._print_tag(tags)

            if reqs.count != -1 and index >= reqs.count:
                return total_count, read_count

        return total_count, read_count

    def get_links(self, req_date=None):
        """Return links of the given date"""

        fields = self.get_fields(self.table_name)
        values = self.get_records(self.table_name, req_date)

        data = []
        for _, value in enumerate(values, start=1):
            data.append(dict(zip(fields, value)))

        return data

    def _get_youtube_keyworld(self, url):
        # extract keywords from title or....
        request = urllib.request.Request(url)
        response = urllib.request.urlopen(request)
        extracted_keyword = ["youtube"]
        if response:
            soup = bf(response, "lxml")

            try:
                raw = soup.find("meta", {"name": "keywords"})["content"]
            except TypeError:
                raise Exception("Fail to get content")

            extracted_keyword.extend(raw.split(", "))

        return extracted_keyword

    def _update_tag(self, data):
        """return 1 if tag is updated otherwise return 0

        Returns
            True/False. True if tag is updated
            new tag
        """

        id = data["id"]
        url = data["url"]
        title = data["title"]
        old_tags = data.get("tags", "")
        new_tags = old_tags

        extracted_keyword, a_title = Tagging.get_keyword_and_title(url)
        if "youtube.com" in url:
            try:
                extracted_keyword = self._get_youtube_keyworld(url)
            except:
                return 0, old_tags

            extracted_keyword.extend(Tagging.get_keyword_from_text(title))
        elif "twitter.com" in url or "x.com" in url:
            extracted_keyword = ["twitter"]
            extracted_keyword.extend(Tagging.get_keyword_from_text(title))

        if extracted_keyword:
            if self.verbose > 1:
                print("     keyword : ", end="")
                if len(extracted_keyword) > 5:
                    print()
                    pp = pprint.PrettyPrinter(width=80, compact=True, indent=15)
                    pp.pprint(extracted_keyword)
                    # pprint.pprint(extracted_keyword)
                else:
                    print(extracted_keyword)

            # list comprehension might not suitable to handle list and single entry? They need to be flattened
            # b = [self.my_tag_map[x] for x in extracted_keyword if x in self.my_tag_map.keys() and x not in old_tags]
            b = []
            old_tag_list = old_tags.split() if old_tags else []

            for x in extracted_keyword:
                if x in self.my_tag_map.keys() and x not in old_tag_list:
                    if isinstance(self.my_tag_map[x], list):
                        b.extend(self.my_tag_map[x])
                        b = list(set(b))  # remove duplicate
                    else:
                        b.append(self.my_tag_map[x])

            if b:
                if self.verbose > 2:
                    print(f"b: {b}")

                new_tag_list = old_tag_list
                new_tag_list.extend(list(set(b)))
                # to remove duplicated from old_tags and new tags(added as a list)
                new_tag_list = list(set(new_tag_list))

                new_tag_list.sort()
                new_tags = " ".join(new_tag_list)
                new_tags = new_tags.strip()

                if self.verbose > 1 and old_tag_list != new_tag_list:
                    print(f"({old_tags}) -> ({new_tags})")

                self.cursor.execute(
                    f"""UPDATE link SET tags = "{new_tags}" WHERE id='{id}'"""
                )
                self.db.commit()

        return 0 if new_tags == old_tags else 1, new_tags

    def update_tag(self, req_date=None):
        """Update tag of records"""

        values = self.get_records(self.table_name, req_date)

        count = 0
        if self.verbose:
            print(f"Process {len(values)} items on {req_date}")
            time.sleep(1)

        for index, item in enumerate(values, start=1):
            data = dict(zip(self.fields, item))
            t, _ = self._update_tag(data)
            if t:
                count += 1

        if count:
            print(f"Updated record : {count}")

    def append_to_obsidian(self, update, req_date):
        """append to Obsidian Today Notes"""
        if update:
            self.update_tag(req_date)

        note = obsidian.Obsidian(req_date)

        if not note.check_if_dn_is_exist():
            print(f"{req_date} : No MD file")

        if not note.check_if_note_has_goodlinks():
            links = self.get_links(req_date)
            if links:
                note.append_to_note(links)
            else:
                print("No links to append")

    # output to json
    # http://stackoverflow.com/questions/3286525/return-sql-table-as-json-in-python
    # cursor.execute('SELECT * FROM vm_list WHERE state == 1')
    # r = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in cursor.fetchall()]
    # json_output = json.dumps(r)
    # print json_output


def main(args):
    print(args)

    goodlinks = Goodlinks(args.verbose, args.update)

    try:
        screen_width = os.get_terminal_size().columns
    except OSError:
        screen_width = 120

    if args.tables:
        goodlinks.print_tables()

    if args.fields:
        goodlinks.print_fields("link")
        goodlinks.print_fields("state")

    if args.date:
        d = args.date.split("-")
        base_date = datetime.datetime(int(d[0]), int(d[1]), int(d[2]))
    else:
        base_date = datetime.datetime.now()  # .strftime("%Y-%m-%d")

    if args.days:
        base_date = datetime.datetime.now() - datetime.timedelta(days=args.days)
        day_offset_list = [x for x in range(0, args.days)]
    else:
        day_offset_list = [0]

    print(day_offset_list)

    print("-" * screen_width)

    day_count = {}
    for day_offset in day_offset_list:
        t = base_date + datetime.timedelta(days=day_offset)
        t_date = t.strftime("%Y-%m-%d")

        #        if args.update:
        #            goodlinks.update_tag(t_date)

        print(t_date)

        if args.obsidian:
            if day_offset != day_offset_list[-1:][0]:
                goodlinks.append_to_obsidian(args.update, t_date)

        if args.list:
            reqs = argparse.Namespace()
            reqs.tag = args.tag
            reqs.date = t_date
            reqs.count = -1

            total_count, read_count = goodlinks.print_records(
                table="link", reqs=reqs, args=args
            )
            day_count[t_date] = (total_count, read_count)

            print("-" * screen_width)

    if day_count:
        df = pd.DataFrame.from_dict(
            day_count, orient="index", columns=["total count", "read count"]
        )
        print(df)


if __name__ == "__main__":
    # update/list/obsidian
    parser = argparse.ArgumentParser()  # epilog=example_text)
    parser.add_argument("-c", "--count", type=int, default=10)
    parser.add_argument("--date", "-d", action="store")
    parser.add_argument(
        "--days", action="store", type=int, help="how many days from today"
    )

    parser.add_argument(
        "--verbose", "-v", action="count", default=0, help="print details of each item"
    )

    parser.add_argument("--tables", action="store_const", const=1, help="print tables")
    parser.add_argument("--tag", "-t", action="store")
    parser.add_argument(
        "--fields", action="store_const", const=1, help="print fields of tables"
    )

    parser.add_argument("--update", action="store_const", const=1, help="update tag")
    parser.add_argument(
        "--obsidian",
        action="store_const",
        const=1,
        help="Update obsidian Daily Notes tag",
    )
    parser.add_argument("--list", action="store_const", const=1, help="List")
    args = parser.parse_args()

    main(args)

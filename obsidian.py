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
if __name__ == "__main__":
    parser = argparse.ArgumentParser()  # epilog=example_text)
    parser.add_argument("--date", "-d", action="store")
    parser.add_argument("--today", action="store_const", const=1, help=f"same to --date with today")
    parser.add_argument("--no-update", action="store_const", const=1, help=f"do not update tag")
    parser.add_argument("--dry-run", action="store_const", const=1, help=f"not udpate Obsidian Daily Notes")

    args = parser.parse_args()

    if args.today == 1:
        args.date = datetime.datetime.now().strftime("%Y-%m-%d")

    # get today's list
    goodlinks = goodlinks.Goodlinks()

    # update first
    if args.no_update == None:
        print("Update tags")
        goodlinks.update_tag('link', args.date)

    links = goodlinks.get_links('link', args.date)

    if args.dry_run == 1:
        print(f"{len(links)} new links on {args.date}")
        sys.exit(0)

    dn_file = f"""{os.environ["HOME"]}/Library/Mobile Documents/iCloud~md~obsidian/Documents/Notes/01. Daily Notes/{args.date}.md"""
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
    else:
        print(f"File is not exist {dn_file}")
    # find note
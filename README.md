# goodlinks

Get daily list from goodlinks.app

== Fields of table link ==
```
   0 id
   1 url
   2 originalURL
   3 title
   4 summary
   5 author
   6 preview
   7 tags
   8 starred
   9 readAt
  10 addedAt
  11 modifiedAt
  12 fetchStatus
  13 status
```

## How to use
```
TAG_FILE=$PWD/tag.yaml python3 goodlinks/goodlinks.py --days 7 --update --list
```

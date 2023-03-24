#!/bin/sh 
scrapeghost https://www.ncleg.gov/Members/Biography/S/436  \
        --schema "{'first_name': 'str', 'last_name': 'str',
        'photo_url': 'url', 'offices': [] }'" \
        --css div.card | python -m json.tool
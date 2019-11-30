#!/bin/bash
python3 c3voc_calendar.py -u https://c3voc.de/eventkalender/events.json -o calendar_year.svg
python3 c3voc_calendar.py -u https://c3voc.de/eventkalender/events.json -m -p calendar_ -s .svg

this_month=$(date +%m)
# yes, this will break in december... but also the whole concepts breaks there, as the next year does not get rendered...
# update: script can now render month 13 aka January of next year
next_month=$(($(date +%m) +1))

ln -s calendar_$this_month.svg calendar_current.svg
ln -s calendar_$next_month.svg calendar_next.svg
ln -s resources-calendar_$this_month.svg resources-calendar_current.svg
ln -s resources-calendar_$next_month.svg resources-calendar_next.svg
mv *.svg /srv/www/001-c3voc.de/htdocs/case-calendar/

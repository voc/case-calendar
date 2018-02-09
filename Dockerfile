# Based on https://github.com/docker-library/docs/tree/master/python

FROM python:3-alpine

WORKDIR /code
COPY requirements.txt ./

RUN apk add --update build-base bash
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# app.py does *nothing, but run in a never ending loop
# CMD [ "python", "c3voc_calendar.py", "-f calendar.yaml", "-o calendar_yaml.svg"]
CMD [ "python", "c3voc_calendar.py", "-u https://c3voc.de/eventkalender/events.json", "-o calendar_json.svg", "-y 2017"]
# Based on https://github.com/docker-library/docs/tree/master/python

FROM python:3-alpine

WORKDIR /code
COPY requirements.txt ./

RUN apk add --update build-base bash
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# app.py does *nothing, but run in a never ending loop
CMD [ "python", "c3voc_calendar.py", "calendar.yaml", "calendar.svg"]

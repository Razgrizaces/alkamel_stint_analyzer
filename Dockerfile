# Use the official lightweight Python image.
# https://hub.docker.com/_/python

FROM python:3.9-slim-buster

RUN apt-get update
RUN apt-get install nano
RUN mkdir wd
WORKDIR wd
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . ./

CMD [ "gunicorn", "-b 0.0.0.0:8070", "app:server"]


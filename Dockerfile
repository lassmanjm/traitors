# syntax=docker/dockerfile:1

# base python image for custom image
FROM python:3.12.8-slim

# create working directory and install pip dependencies
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

# run the flask server
CMD [ "python3", "claudia_bot.py"]

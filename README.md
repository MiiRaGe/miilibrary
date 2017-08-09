# MiiNASLibrary 2.0 #

### Status ###
[![Build Status](https://travis-ci.org/MiiRaGe/miilibrary.svg?branch=master)](https://travis-ci.org/MiiRaGe/miilibrary)
[![Coverage Status](https://coveralls.io/repos/MiiRaGe/miilibrary/badge.svg?branch=master&service=github)](https://coveralls.io/github/MiiRaGe/miilibrary?branch=master)
[![Requirements Status](https://requires.io/github/MiiRaGe/miilibrary/requirements.svg?branch=master)](https://requires.io/github/MiiRaGe/miilibrary/requirements/?branch=master)

### Concept ###

This project is a media handling library, it's meant to be use on a tinker board connecté with access to a storage (NAS, Hard Drive).

It acts as an rpc server, with 3 different actions:
* Unpack: looks for files in a local folder and extract archive or hard link video medias to a data folder.
* Sort: looks for video medias in the data folder, fetches info on internet via metadata or name, clean name, add them to db and sort them approprietly (Serie/Movie).
* Index: looks a the video files in db and index them with info from the internet (ratings, years, actors, genre etc)


### Technical Stack ###

This project includes the dockerfile needed to use resin.io.
It uses a local django, local mysql db, a local celery instance and a local rabbitmq broker.

### Dependencies ###

* Python 3.4-3.5
* Django 1.11
* See requirements.txt for full module dependencies
* The requirements are meant to be "bleeding edge" (contact for a list of working dependencies if latest not working)

### Setting up ###

* Install dependencies : pip install -r requirements.txt
* Run tests : py.test
* Deployement : Carefully set the parameters in settings/local.py (local copy of base.py) or environment variables

### Running ###

* python ./manage.py runserver

### Contributors ###

* Alexis Durand (Owner)

### Contact ###

* alexis.durand28@gmail.com

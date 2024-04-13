# Training Diary App #

Web application for tracking and analyzing trainings.

## Features ##

### Keep track of your trainings

Input your trainings or load them through [Polar API](https://www.polar.com/en/accesslink):

![trainings](./img/trainings.png)

### Analyze your trainings

Analyze your trainings with various graphical reports:

![report_amount](./img/report_amount.png)

![report_sport](./img/report_sport.png)

### View routes on map

View training routes on map:

![map](./img/map.png)

### Follow your recovery

Load sleep data from [Polar](https://www.polar.com/en/accesslink) or [Oura](https://cloud.ouraring.com/docs/) and analyze it with recovery dashboard:

![recovery](./img/recovery.png)

### Personalize settings

Customize sports, training zones and seasons:

![settings](./img/settings.png)

## Setting up the development environment ##

* Install Python >= 3.10

* Clone repository

* Install required python libraries

````
pip install -r requirements.txt
````

* Run database migrations

````
python .\treenit\manage.py migrate
````

* Import static data

````
python .\treenit\manage.py loaddata treenit\treenipaivakirja\fixtures\aika.json
````

* Set following environment variables 
````
DEBUG = True
SECRET_KEY = your_secret_key
````

* If you wish to interact with Polar and Oura APIs set also following environment variables
````
ACCESSLINK_CLIENT_KEY
ACCESSLINK_CLIENT_SECRET
OURA_CLIENT_KEY
OURA_CLIENT_SECRET
````

* Start app by running following command
````
python .\treenit\manage.py runserver
````

* Open web-browser (*preferred Chrome*) and go to
````
http://127.0.0.1:8000/treenipaivakirja/
````
# Training App #

Web application for recording and analyzing trainings. 

App has interfaces to [Polar](https://www.polar.com/en/accesslink) and [Oura](https://cloud.ouraring.com/docs/) data.

## Features ##

### Keep track of your trainings

* Input your trainings 
    * either manually or load them through Polar API
* Investigate training calendar
* Download training data into excel or csv

![trainings](./img/trainings.png)

### Analyse your trainings

* Analyse your trainings with various graphical reports

![report_amount](./img/report_amount.png)

![report_sport](./img/report_sport.png)

### Follow your recovery

* Fetch sleep data from Polar or Oura
* Analyse it with recovery dashboard

![recovery](./img/recovery.png)

### Personalise settings

* Sports, training zones and seasons can be customized for each user

![settings](./img/settings.png)

## Setting up the development environment ##

* Install Python >= 3.6

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
### Installation

install the following packages or their equivalents:

````
$ sudo apt-get install libmysqlclient-dev python-dev redis-server
````

install the package:
````
$ cd wikimetrics
$ sudo pip install -e .
````

run the tests (inside top-level wikimetrics directory)
````
$ sudo pip install nose
$ nosetests
````

run celery and the flask webserver in seperate terminals
````
$ wikimetrics --mode web
````
````
$ wikimetrics --mode celery
````

go to `localhost:5000`

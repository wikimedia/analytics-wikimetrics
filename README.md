Contents:

* [Setting up your Development Environment](#development-environment)
* [Understanding the Architecture of the code](#architecture)
* [Quick Tutorial: Write a new Metric](#write-a-new-metric)
* [Submitting Code](#submit-code)

### Development Environment

Wikimetrics consists of a website that runs on Flask and an asynchronous queue implemented
with Celery.  The Celery queue stores its results in Redis and the Flask website stores
metadata in MySQL.  To set up your dev environment the old fashioned way, see old versions
of this README.

To set it up using our new Docker setup, follow directions below. Please note that this setup is optimized for a dev environment only. To see how we deploy wikimetrics on WikimediaLabs, look at our [deploy repo](https://github.com/wikimedia/analytics-wikimetrics-deploy)

#### Setup docker engine, docker-machine, and docker-compose

* [Docker engine](https://docs.docker.com/engine/installation/)
* [Docker-machine](https://www.docker.com/products/docker-toolbox) - For MacOS/Windows - docker-machine is supported through docker-toolbox now
* [Docker-compose](https://docs.docker.com/compose/install/)

By now you should have docker running, and if you are using docker-machine, use `docker-machine ip machine-name` to find its ip. If you don't know the machine-name, `docker-machine ls` should find it for you.

Please note that this setup is tested with docker 18.06.1-ce and docker-compose 1.22.0 - it may throw some errors with older versions.

#### Setup wikimetrics

Let's go ahead and setup wikimetrics now

* Get the code [here](https://gerrit.wikimedia.org/r/#/admin/projects/analytics/wikimetrics)
* `cd` into the source directory
* Build it all - `docker-compose build` (if this doesn't work, you may need to run `$ eval "$(docker-machine env default)"`)
    - This uses the instructions in the docker-compose.yml file to build all the containers and link them.
* Run it all - `docker-compose up`
    - You should see all the services start up now - if there are no errors you should be good to go
    - Don't want to see all these logs at once or keep this running in the foreground? `docker-compose up -d` runs it in detached mode.
    - Navigate to localhost:5000 and make sure it's running.
    - If you are using docker-machine - it will be some thing like 192.168.99.100:5000
      - The one tricky thing here is that oauth redirection on login will take you to localhost, at the moment we don't have a better solution than replacing localhost with the docker machine ip on redirect - but this works.
* What is running? - `docker-compose ps`
    - For the application to be running healthy - you should see db, queue, redis, scheduler, and web up. The other services run at startup and exit or are there for other purposes (will explain)
* See logs - `docker-compose logs service`
    - The service can be web, db, queue etc. You can find available services defined as keys in the `docker-compose.yml` file.
* Run migrations
    - The upgrade_db service does precisely that. `docker-compose run upgrade_db` should run migrations
    - If you're making a change and need to generate an Alembic version, then after
      you update the models in ````wikimetrics.models````,
      `docker-compose run --entrypoint bash upgrade_db`. This should drop you into a bash shell. Then run,
      `alembic revision --autogenerate`. Type `exit` to leave the session.
* Run tests
    - The test service helps with this. `docker-compose run test scripts/test` runs all the tests.
    - You can also run specific tests like `docker-compose run test scripts/test tests/test_utils`, etc.
    - Make sure that the queue service is not running when tests run, you can ensure this by doing `docker-compose stop` before running the `docker-compose run test` commands.
* Test changes in source code
    - The uwsgi web server is configured to autoreload on changes, so hopefully you don't have to restart the web server. If you need to - you can run `docker-compose restart web`.
    - If you change code that affects the celery workers - you probably need to restart the queue. `docker-compose restart queue` does it.
* Stop wikimetrics - `docker-compose stop`

Other FAQ:

* How do I access the database?
    - `docker ps` to see the list of docker containers. You should find the container name for the database service, somehing like `wikimetrics_db_1`. Run `docker exec -i -t wikimetrics_db_1 mysql` to access the mysql host as root user, or pass appropriate user options to access as wikimetrics user.
* Where is the config coming from?
    - ./wikimetrics/config/docker_config. This is mounted as a volume at /srv/wikimetrics/config in the container. Look at the definition for the `data` service to see the volumes defined. This defines how the source code from the current directory gets mounted too.
* Do I have to do `docker-compose build` everytime?
    - Mostly not. Do rebuild if you change any of the requirements.txt files, or change the setup.py installation. Otherwise `docker-compose restart` should be enough.

(Note: This setup is brand new - Please ping @madhuvishy on freenode #wikimedia-analytics or file a bug at https://phabricator.wikimedia.org/tag/analytics if you run into issues.)

### Architecture

The project is [Python](http://www.python.org/) on the back-end, and a little
[KnockoutJS](http://knockoutjs.com/) on the front-end.  You can read the code but this
section aims to make it easy to understand.  If you'd just like to write a new metric,
follow the [quick tutorial](#write-a-new-metric) below.

### Write a new Metric

This tutorial is about speed not depth, so here we go.

* Make `wikimetrics/metrics/your_new_metric.py`
* In `wikimetrics/metrics/__init__.py`, add `from your_new_metric import *`
* In your new metric file, start by importing:

````
# the base class
from metric import Metric
# the sqlalchemy models you need to run querries on
from wikimetrics.models import Page, Revision
# any WTForms fields, custom fields, or validators you'll need
from wtforms import DateField
from form_fields import CommaSeparatedIntegerListField
from wtforms.validators import Required
# some date helpers that are useful but should probably be factored out
from ..utils import thirty_days_ago, today, mediawiki_date
# and finally any sqlalchemy constructs you need
from sqlalchemy import func
````

* Then create your class and document it.  The docstring will show up on the website in
  monospace font so by convention we include an explanation of the metric and the SQL used
  to compute it.

````
class YourNewMetric(Metric):
    """
    Explanation of Your New Metric (in this case I'm just duplicating namespace edits)
    
    SQL query:
    
     select r.rev_user, r.count(*)
       from revision r
                inner join
            page p      on p.page_id = r.rev_page
      where r.rev_timestamp between [start] and [end]
        and r.rev_user in ([parameterized])
        and p.page_namespace in ([parameterized])
      group by rev_user
    """
````

* Inside the class there are two sections of properties.  The first is used to control how
  the metric shows up throughout the interface:

````
# controls whether this metric is available to run reports
show_in_ui  = True
# a unique id that we use internally
id          = 'edits'
# the name that this metric has in the UI
label       = 'Edits'
# the headline on the /metrics page and tooltip in the UI
description = 'Compute the number of edits'
````

* The second section is used to define the WTForm input fields for this metric in the UI.
  These are the parameters of the metric and their value will be used in the sqlalchemy
  logic.

````
start_date          = DateField(default=thirty_days_ago)
end_date            = DateField(default=today)
namespaces = CommaSeparatedIntegerListField(
    None,
    [Required()],
    default='0',
    description='0, 2, 4, etc.',
)
````

* Finally, you have to write the logic of the metric itself.  Subclasses of `Metric` are
  callable, so we have to implement the following signature
  `__call__(self, user_ids, session)`.  Basically, you get the mediawiki user ids to run
  the metric on and a sqlalchemy session to run the query.

````
# the WTForm date fields don't work as-is in Mediawiki,
# this should be factored out but is necessary for now
start_date = self.start_date.data
end_date = self.end_date.data
if session.bind.name == 'mysql':
    start_date = mediawiki_date(self.start_date)
    end_date = mediawiki_date(self.end_date)

# For details on SQLAlchemy, study the incredibly well written documentation
revisions_by_user = dict(
    session
    .query(Revision.rev_user, func.count(Revision.rev_id))
    .join(Page)
    .filter(Page.page_namespace.in_(self.namespaces.data))
    .filter(Revision.rev_user.in_(user_ids))
    .filter(Revision.rev_timestamp >= start_date)
    .filter(Revision.rev_timestamp <= end_date)
    .group_by(Revision.rev_user)
    .all()
)
````

* The return value of `__call__` has to be a dictionary of user ids to a dictionary of
  different values that the metric might be returning per user.  In this case, the only
  value would be 'edits' but in the case of bytes added, there are a few different ways to
  compute the bytes added aggregates, you can see `wikimetrics/metrics/bytes_added.py` for
  that example.

````
return {
    user_id: {'edits': revisions_by_user.get(user_id, 0)}
    for user_id in user_ids
}
````


### Submit Code

As long as all the tests pass, your code style is clean, and you have code coverage on all
or most of your new code, go ahead and submit:

* a gerrit patchset (link to instructions on this coming soon, go to #wikimedia-analytics
  on irc.freenode.net if you'd like to get started right away)
* a github pull request (this is a bit harder to merge because we use gerrit and mirror to
  github, but we love all flavors of git so it's ok)

As a style guide, we rely mostly on flake8.  We've set up the rules in setup.cfg, so run
flake8 before submiting any code.

````
$ sudo pip install flake8
$ flake8
````

The only things not covered by flake8 that we care about are commenting classes and
functions and indenting blank lines.  We don't comment obvious functions, but if there's
anything interesting to say, we say it.  Here's an example (I used periods to show spaces
on blank lines):

````
class StyleGuide(object):
    """
    Used to show the style we prefer in Wikimetrics code
    """
....
    def __init__(self, age, debug=False):
        """
        The constructor shows our parameter documentation style, aligned on tab stops
........
        Parameters
            age     : An integer age in years.  Oh by the way, we changed flake8's default
                      line length to 90 instead of 80 as you can see here, and we try to
                      make line wrappings somewhat pretty
            debug   : A boolean to put the instance in debug mode, optional, defaults
                      to False
        """
        self.age = age
        self.debug = debug
........
        self.start()
....
    def start(self):
        """
        Starts this instance and lets it receive requests
        """
        # code omitted because the metaphor ran dry
....
    def obvious_method(self):
        # no doc string comment on this function because it's obvious
````

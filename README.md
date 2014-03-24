Contents:

* [Setting up your Development Environment](#development-environment)
* [Understanding the Architecture of the code](#architecture)
* [Quick Tutorial: Write a new Metric](#write-a-new-metric)
* [Submitting Code](#submit-code)

### Development Environment

Wikimetrics consists of a website that runs on Flask and an asynchronous
queue implemented with Celery.  The Celery queue stores its results in
Redis and the Flask website stores metadata in MySQL.
To set up your dev environment the old fashioned way, see old versions of this README.
To set it up the easy way with mediawiki-vagrant, follow the directions below:

* Install [Mediawiki Vagrant](https://www.mediawiki.org/wiki/MediaWiki-Vagrant)
* From your Mediawiki Vagrant directory, do this:

````
$ vagrant enable-role wikimetrics
$ git submodule update --init
$ vim Vagrantfile
````

* Add this under the other config.vm.network section(s):

````
config.vm.network :forwarded_port,
    guest: 5000, host: 5000, id: 'wikimetrics'
````

* Reload vagrant: `$ vagrant reload --provision`
* Browse to [localhost:5000](http://localhost:5000)

And you now have a fully working Wikimetrics environment.
You can verify both the web interface and queue are working
by ssh-ing into vagrant (https://www.mediawiki.org/wiki/MediaWiki-Vagrant#Basic_usage)
and running the following command:

````
 $  ps ax | grep -e '[-]c wikimetrics'
````
You should see the processes associated to wikimetrics instance.

The queue and web are managed with upstart, doing:

````
sudo [start|stop] wikimetrics-queue
````

should start/stop the queue. Doing:

````
sudo [start|stop] wikimetrics-web
````

will start/stop the web ui.

The code it's running from is sym-linked locally in your Mediawiki Vagrant
repository under `wikimetrics/` so you can do any development there.

Remember that when you ssh into vagrant you are the vagrant user, you can set up git
access in vagrant but you can also run git commands outside vagrant.
 
 /some-path/vagrant/wikimetrics

#### Running Tests
Vagrant sets up a wikimetrics environment but it does not set up your testing
dependencies.

In order to setup those please execute the following
in wikimetrics root directory.
````
$ sudo pip install .

````
and

````
$ sudo pip install nose
$ sudo pip install coverage
````
To run all tests:

1. Stop the queue
````
$ sudo stop wikimetrics-queue
````

2. Run tests
````
$ ./scripts/test
````

Contact us on freenode, channel #wikimedia-analytics if you have any questions.

#### Ongoing Development

Once you're up and running, there are a few things you need to know if you do
ongoing development.  When you `git pull` new code, you'll need to potentially
update the database and potentially update any dependencies.  To update the database,
we use [Alembic](https://pypi.python.org/pypi/alembic/0.6.3).  So to upgrade to
the latest version as defined by Alembic, first ssh into your vagrant box and
go to the wikimetrics directory:

````
$ vagrant ssh
$ cd /vagrant/wikimetrics
````

Then tell Alembic to bring you up to speed: `$ alembic upgrade head`.

Similarly, if you're making a change and need to generate an Alembic version, then
after you update the models in ````wikimetrics.models````,
issue: `$ alembic revision --autogenerate`

To install new dependencies, ssh into your vagrant box as above,
and issue: `$ scripts/install`

### Architecture

The project is [Python](http://www.python.org/) on the back-end, and a
little [KnockoutJS](http://knockoutjs.com/) on the front-end. You can read
the code but this section aims to make it easy to understand. If you'd just like
to write a new metric, follow the [quick tutorial](#write-a-new-metric) below.

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

* Then create your class and document it.  The docstring will show up on the website
in monospace font so by convention we include an explanation of the metric and
the SQL used to compute it.

````
class YourNewMetric(Metric):
    """
    Explanation of Your New Metric (in this case I'm just duplicating namespace edits)

    SQL query:

    select r.rev_user, r.count(*)
        from revision r
                inner join
            page p on p.page_id = r.rev_page
    where r.rev_timestamp between [start] and [end]
        and r.rev_user in ([parameterized])
        and p.page_namespace in ([parameterized])
    group by rev_user
    """
````

* Inside the class there are two sections of properties.  The first is used to control
how the metric shows up throughout the interface:

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
 These are the parameters of the metric and their value will be used in the
 sqlalchemy logic.

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

* Finally, you have to write the logic of the metric itself.  Subclasses of `Metric`
are callable, so we have to implement the
following signature `__call__(self, user_ids, session)`.
Basically, you get the mediawiki user ids to run the metric
on and a sqlalchemy session to run the query.

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

* The return value of `__call__` has to be a dictionary of user ids to a dictionary
of different values that the metric might be returning per user.  In this case,
the only value would be 'edits' but in the case of bytes added, there are a
few different ways to compute the bytes added aggregates,
you can see `wikimetrics/metrics/bytes_added.py` for that example.

````
return {
    user_id: {'edits': revisions_by_user.get(user_id, 0)}
    for user_id in user_ids
}
````

### Submit Code

If all the tests pass, your code style is clean, and you have code coverage on all
or most of your new code, go ahead and submit:

* a gerrit patchset (link to instructions on this coming soon, go to #wikimedia-analytics
on irc.freenode.net if you'd like to get started right away)
* a github pull request (this is a bit harder to merge because we use gerrit and mirror
to github, but we love all flavors of git so it's ok)

#### Coding Guidelines

* Controllers should not access storage or IO. Storage or IO operations need to
happen from models or API layer.

* Controllers validate user input such when requests get to storage layer we know
parameters are "sane" (except when there are non-controller access paths to the code
that needs valid input).

* Storage methods should be stateless. That is, you should not require to call method
A before calling method B. A and B should be grouped in to a C method
that wraps both actions and thus can roll both actions back if needed.

* No circular dependencies on javascript. If reports.js uses site.js site.js should
not use code in reports.js.

* Checks on ownership (can this user access report X?) should happen in one place.
That way admin overrides can also happen in just one place.

* Please do not add functionality that creates files in the wikimetrics checkout.
Since we deploy the code from source, creating files under ./wikimetrics
is likely to run into permits problems on production.

* Any transaction that changes state should have a CSRF token associated with it.

* Avoid singleton access in methods. Methods should specify what data are they using
via parameter passing.

Good:

```python
  def method(param_1, param_2, param_3)
```

Bad:

```python
  def method(param_1)
    #access to method2 which is a global here
```

#### Style Guidelines

As a style guide, we rely mostly on flake8.  We've set up the rules in setup.cfg,
so run flake8 before submitting any code.

````
$ sudo pip install flake8
$ flake8
````

The only things not covered by flake8 that we care about are commenting classes and
functions and indenting blank lines.  We don't comment obvious functions, but if
there's anything interesting to say, we say it.  Here's an example (I used periods
to show spaces on blank lines):

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
            debug   : A boolean to put the instance in debug mode, optional,
                      defaults to False
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

import time
from sqlalchemy import func

from wikimetrics.configurables import app, db
from wikimetrics.models import (
    MediawikiUser, CentralAuthLocalUser, ReportStore
)
from wikimetrics.controllers.authentication import is_public


if app.config['DEBUG']:

    @app.route('/demo/get-session-and-leave-open')
    @is_public
    def get_session_and_leave_open():
        session = db.get_session()
        session.query(ReportStore).all()
        session2 = db.get_session()
        session2.query(ReportStore).all()
        return ''

    @app.route('/demo/create/fake-<string:project>-users/<int:n>')
    def add_fake_wiki_users(project, n):
        def name_formatter(x):
            return 'FakeUser{0}'.format(x)
        generate_mediawiki_users(project, n, name_formatter)
        generate_centralauth_users(project, n, name_formatter)
        return 'Up to {0} records created in {1} and centralauth'.format(n, project)


def generate_mediawiki_users(project, n, name_formatter):
    session = db.get_mw_session(project)
    try:
        user_count = (
            session.query(func.count()).
            filter(MediawikiUser.user_name.like(name_formatter('%'))).
            one()[0]
        )
        users_to_generate = n - user_count
        if users_to_generate > 0:
            start_index = user_count + 1
            session.bind.engine.execute(
                MediawikiUser.__table__.insert(),
                [
                    {
                        'user_name'         : name_formatter(start_index + i),
                        'user_registration' : '20130101000000'
                    }
                    for i in range(users_to_generate)
                ]
            )
            session.commit()
    finally:
        session.close()


def generate_centralauth_users(project, n, name_formatter):
    session = db.get_ca_session()
    try:
        user_count = (
            session.query(func.count()).
            filter(CentralAuthLocalUser.lu_wiki == project).
            filter(CentralAuthLocalUser.lu_name.like(name_formatter('%'))).
            one()[0]
        )
        users_to_generate = n - user_count
        if users_to_generate > 0:
            start_index = user_count + 1
            session.bind.engine.execute(
                CentralAuthLocalUser.__table__.insert(),
                [
                    {
                        'lu_wiki' : project,
                        'lu_name' : name_formatter(start_index + i)
                    }
                    for i in range(users_to_generate)
                ]
            )
            session.commit()
    finally:
        session.close()

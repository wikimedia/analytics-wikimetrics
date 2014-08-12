import time
from sqlalchemy import func

from wikimetrics.configurables import app, db
from wikimetrics.models import MediawikiUser, ReportStore
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
        session = db.get_mw_session(project)
        max_id = session.query(func.max(MediawikiUser.user_id)).one()[0] or 0
        start = max_id + 1
        session.bind.engine.execute(
            MediawikiUser.__table__.insert(),
            [
                {
                    'user_name'         : 'User-{0}'.format(r),
                    'user_id'           : r,
                    'user_registration' : '20130101000000'
                }
                for r in range(start, start + n)
            ]
        )
        session.commit()
        return '{0} user records created in {1}'.format(n, project)

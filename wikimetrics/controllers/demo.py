from sqlalchemy import func

from wikimetrics.configurables import app, db
from wikimetrics.models import MediawikiUser


if app.config['DEBUG']:
    
    @app.route('/demo/create/fake-<string:project>-users/<int:n>')
    def add_fake_wiki_users(project, n):
        session = db.get_mw_session(project)
        try:
            max_id = session.query(func.max(MediawikiUser.user_id)).one()[0] or 0
            start = max_id + 1
            session.bind.engine.execute(
                MediawikiUser.__table__.insert(),
                [
                    {
                        'user_name'         : 'user-{0}'.format(r),
                        'user_id'           : r,
                        'user_registration' : '20130101000000'
                    }
                    for r in range(start, start + n)
                ]
            )
            session.commit()
        finally:
            session.close()
        return '{0} user records created in {1}'.format(n, project)

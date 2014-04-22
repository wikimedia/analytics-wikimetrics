from flask import render_template, redirect, request, jsonify
from flask.ext.login import current_user
from sqlalchemy import func

from ..configurables import app, db
from ..models import (
    WikiUser,
    User,
    MediawikiUser,
    Cohort,
    CohortUser,
    CohortUserRole,
    CohortWikiUser,
    MetricReport,
)
from ..models.mediawiki import Revision, Page
from datetime import datetime
from ..metrics import RandomMetric


if app.config['DEBUG']:
    def delete_my_cohorts(db_sess):
        user = db_sess.query(User).filter_by(email=current_user.email).one()
        
        # delete all of this user's data
        cohort_users = db_sess.query(CohortUser).filter_by(user_id=user.id)
        cohort_users.delete()
        cwu = db_sess.query(CohortWikiUser)\
            .join(Cohort)\
            .join(CohortUser)\
            .filter(CohortUser.user_id == user.id)\
            .all()
        wu = db_sess.query(WikiUser)\
            .join(CohortWikiUser)\
            .join(Cohort)\
            .join(CohortUser)\
            .filter(CohortUser.user_id == user.id)\
            .all()
        c = db_sess.query(Cohort)\
            .join(CohortUser)\
            .filter(CohortUser.user_id == user.id)\
            .filter(CohortUser.role == CohortUserRole.OWNER)\
            .all()
        
        db_sess.commit()
        
        for r in cwu:
            db_sess.delete(r)
        for r in wu:
            db_sess.delete(r)
        for r in c:
            db_sess.delete(r)
        
        db_sess.commit()
        return user
    
    @app.route('/demo/delete/cohorts/')
    def demo_delete_cohorts():
        db_sess = db.get_session()
        delete_my_cohorts(db_sess)
        db_sess.close()
        return 'OK, wiped out the database only for ' + current_user.email
    
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

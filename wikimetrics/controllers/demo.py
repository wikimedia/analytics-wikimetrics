from flask import render_template, redirect, request, jsonify
from flask.ext.login import current_user
from ..configurables import app, db
from ..models import (
    WikiUser,
    User,
    MediawikiUser,
    Cohort,
    CohortUser,
    CohortUserRole,
    CohortWikiUser,
    MetricJob,
)
from ..metrics import RandomMetric
import logging
logger = logging.getLogger(__name__)


if app.config['DEBUG']:
    @app.route('/demo/metric/random/<int:cohort_id>')
    def run_task_in_celery(cohort_id):
        db_session = db.get_session()
        user_ids = db_session.query(WikiUser.mediawiki_userid)\
            .join(CohortWikiUser)\
            .filter(CohortWikiUser.cohort_id == cohort_id)\
            .all()
        if len(user_ids) == 0:
            user_ids = db_session.query(WikiUser.mediawiki_userid).all()
        
        job = MetricJob(RandomMetric(), user_ids, 'enwiki')
        #from nose.tools import set_trace; set_trace()
        res = job.task.delay().get()
        print user_ids
        return str(res)
    
    @app.route('/demo/create/cohorts/')
    def add_demo_cohorts():
        db_sess = db.get_session()
        user = db_sess.query(User).filter_by(email=current_user.email).one()
        
        # delete all of this user's data
        db_sess.query(CohortUser).filter_by(user_id=user.id).delete()
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
            .all()
        for r in cwu:
            db_sess.delete(r)
        for r in wu:
            db_sess.delete(r)
        for r in c:
            db_sess.delete(r)
        
        db_sess.commit()
        
        # add cohorts and assign ownership to the passed-in user
        cohort1 = Cohort(name='Algeria Summer Teahouse', description='', enabled=True)
        cohort2 = Cohort(name='Berlin Beekeeping Society', description='', enabled=True)
        cohort3 = Cohort(name='A/B April', description='', enabled=True)
        cohort4 = Cohort(name='A/B March', description='', enabled=True)
        cohort5 = Cohort(name='A/B February', description='', enabled=True)
        cohort6 = Cohort(name='A/B January', description='', enabled=True)
        cohort7 = Cohort(name='A/B December', description='', enabled=True)
        cohort8 = Cohort(name='A/B October', description='', enabled=True)
        cohort9 = Cohort(name='A/B September', description='', enabled=True)
        cohort10 = Cohort(name='A/B August', description='', enabled=True)
        cohort11 = Cohort(name='A/B July', description='', enabled=True)
        db_sess.add_all([
            cohort1, cohort2, cohort3, cohort4, cohort5, cohort6,
            cohort7, cohort8, cohort9, cohort10, cohort11
        ])
        db_sess.commit()
        
        db_sess.add(CohortUser(user_id=user.id, cohort_id=cohort1.id, role=CohortUserRole.OWNER))
        db_sess.add(CohortUser(user_id=user.id, cohort_id=cohort2.id, role=CohortUserRole.OWNER))
        db_sess.add(CohortUser(user_id=user.id, cohort_id=cohort3.id, role=CohortUserRole.OWNER))
        db_sess.add(CohortUser(user_id=user.id, cohort_id=cohort4.id, role=CohortUserRole.OWNER))
        db_sess.add(CohortUser(user_id=user.id, cohort_id=cohort5.id, role=CohortUserRole.OWNER))
        db_sess.add(CohortUser(user_id=user.id, cohort_id=cohort6.id, role=CohortUserRole.OWNER))
        db_sess.add(CohortUser(user_id=user.id, cohort_id=cohort7.id, role=CohortUserRole.OWNER))
        db_sess.add(CohortUser(user_id=user.id, cohort_id=cohort8.id, role=CohortUserRole.OWNER))
        db_sess.add(CohortUser(user_id=user.id, cohort_id=cohort9.id, role=CohortUserRole.OWNER))
        db_sess.add(CohortUser(user_id=user.id, cohort_id=cohort10.id, role=CohortUserRole.OWNER))
        db_sess.add(CohortUser(user_id=user.id, cohort_id=cohort11.id, role=CohortUserRole.OWNER))
        
        # TODO: these users don't actually exist in the mediawiki databases, add them
        #db_enwiki_session = db.get_mw_session('enwiki')
        #db_dewiki_session = db.get_mw_session('dewiki')
        wu1 = WikiUser(mediawiki_username='Dan', mediawiki_userid=1, project='enwiki')
        wu2 = WikiUser(mediawiki_username='Evan', mediawiki_userid=2, project='enwiki')
        wu3 = WikiUser(mediawiki_username='Andrew', mediawiki_userid=3, project='enwiki')
        wu4 = WikiUser(mediawiki_username='Diederik', mediawiki_userid=4, project='enwiki')
        
        wu5 = WikiUser(mediawiki_username='Andrea', mediawiki_userid=5, project='dewiki')
        wu6 = WikiUser(mediawiki_username='Dennis', mediawiki_userid=6, project='dewiki')
        wu7 = WikiUser(mediawiki_username='Florian', mediawiki_userid=7, project='dewiki')
        wu8 = WikiUser(mediawiki_username='Gabriele', mediawiki_userid=8, project='dewiki')
        
        wu9 = WikiUser(mediawiki_username='n/a', mediawiki_userid=9, project='enwiki')
        wu10 = WikiUser(mediawiki_username='n/a', mediawiki_userid=10, project='enwiki')
        wu11 = WikiUser(mediawiki_username='n/a', mediawiki_userid=11, project='enwiki')
        
        wu12 = WikiUser(mediawiki_username='n/a', mediawiki_userid=12, project='enwiki')
        wu13 = WikiUser(mediawiki_username='n/a', mediawiki_userid=13, project='enwiki')
        wu14 = WikiUser(mediawiki_username='n/a', mediawiki_userid=14, project='enwiki')
        
        wu15 = WikiUser(mediawiki_username='n/a', mediawiki_userid=15, project='enwiki')
        wu16 = WikiUser(mediawiki_username='n/a', mediawiki_userid=16, project='enwiki')
        wu17 = WikiUser(mediawiki_username='n/a', mediawiki_userid=17, project='enwiki')
        
        wu18 = WikiUser(mediawiki_username='n/a', mediawiki_userid=18, project='enwiki')
        wu19 = WikiUser(mediawiki_username='n/a', mediawiki_userid=19, project='enwiki')
        wu20 = WikiUser(mediawiki_username='n/a', mediawiki_userid=20, project='enwiki')
        
        wu21 = WikiUser(mediawiki_username='n/a', mediawiki_userid=21, project='enwiki')
        wu22 = WikiUser(mediawiki_username='n/a', mediawiki_userid=22, project='enwiki')
        wu23 = WikiUser(mediawiki_username='n/a', mediawiki_userid=23, project='enwiki')
        
        wu24 = WikiUser(mediawiki_username='n/a', mediawiki_userid=24, project='enwiki')
        wu25 = WikiUser(mediawiki_username='n/a', mediawiki_userid=25, project='enwiki')
        wu26 = WikiUser(mediawiki_username='n/a', mediawiki_userid=26, project='enwiki')
        
        wu27 = WikiUser(mediawiki_username='n/a', mediawiki_userid=27, project='enwiki')
        wu28 = WikiUser(mediawiki_username='n/a', mediawiki_userid=28, project='enwiki')
        wu29 = WikiUser(mediawiki_username='n/a', mediawiki_userid=29, project='enwiki')
        
        wu30 = WikiUser(mediawiki_username='n/a', mediawiki_userid=30, project='enwiki')
        wu31 = WikiUser(mediawiki_username='n/a', mediawiki_userid=31, project='enwiki')
        wu32 = WikiUser(mediawiki_username='n/a', mediawiki_userid=32, project='enwiki')
        
        wu33 = WikiUser(mediawiki_username='n/a', mediawiki_userid=33, project='enwiki')
        wu34 = WikiUser(mediawiki_username='n/a', mediawiki_userid=34, project='enwiki')
        wu35 = WikiUser(mediawiki_username='n/a', mediawiki_userid=35, project='enwiki')
        
        db_sess.add_all([
            wu1, wu2, wu3, wu4, wu5, wu6, wu7, wu8, wu9, wu10, wu11, wu12,
            wu13, wu14, wu15, wu16, wu17, wu18, wu19, wu20, wu21, wu22, wu23,
            wu24, wu25, wu26, wu27, wu28, wu29, wu30, wu31, wu32, wu33, wu34,
            wu35,
        ])
        db_sess.commit()
        
        db_sess.add(CohortWikiUser(wiki_user_id=wu1.id, cohort_id=cohort1.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu2.id, cohort_id=cohort1.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu3.id, cohort_id=cohort1.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu4.id, cohort_id=cohort1.id))
        
        db_sess.add(CohortWikiUser(wiki_user_id=wu5.id, cohort_id=cohort2.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu6.id, cohort_id=cohort2.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu7.id, cohort_id=cohort2.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu8.id, cohort_id=cohort2.id))
        
        db_sess.add(CohortWikiUser(wiki_user_id=wu9.id, cohort_id=cohort3.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu10.id, cohort_id=cohort3.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu11.id, cohort_id=cohort3.id))
        
        db_sess.add(CohortWikiUser(wiki_user_id=wu12.id, cohort_id=cohort4.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu13.id, cohort_id=cohort4.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu14.id, cohort_id=cohort4.id))
        
        db_sess.add(CohortWikiUser(wiki_user_id=wu15.id, cohort_id=cohort5.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu16.id, cohort_id=cohort5.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu17.id, cohort_id=cohort5.id))
        
        db_sess.add(CohortWikiUser(wiki_user_id=wu18.id, cohort_id=cohort6.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu19.id, cohort_id=cohort6.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu20.id, cohort_id=cohort6.id))
        
        db_sess.add(CohortWikiUser(wiki_user_id=wu21.id, cohort_id=cohort7.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu22.id, cohort_id=cohort7.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu23.id, cohort_id=cohort7.id))
        
        db_sess.add(CohortWikiUser(wiki_user_id=wu24.id, cohort_id=cohort8.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu25.id, cohort_id=cohort8.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu26.id, cohort_id=cohort8.id))
        
        db_sess.add(CohortWikiUser(wiki_user_id=wu27.id, cohort_id=cohort9.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu28.id, cohort_id=cohort9.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu29.id, cohort_id=cohort9.id))
        
        db_sess.add(CohortWikiUser(wiki_user_id=wu30.id, cohort_id=cohort10.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu31.id, cohort_id=cohort10.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu32.id, cohort_id=cohort10.id))
        
        db_sess.add(CohortWikiUser(wiki_user_id=wu33.id, cohort_id=cohort11.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu34.id, cohort_id=cohort11.id))
        db_sess.add(CohortWikiUser(wiki_user_id=wu35.id, cohort_id=cohort11.id))
        
        db_sess.commit()
        return 'OK, wiped out the database and added cohorts only for ' + current_user.email

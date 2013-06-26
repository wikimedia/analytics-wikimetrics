from flask import render_template, redirect, request, jsonify
from flask.ext.login import current_user
from ..configurables import app, db
from ..models import *
import logging

logger = logging.getLogger(__name__)



# TODO: this is an obvious serious security flaw.  Either come up with a way to
# isolate it or remove the functionality
@app.route('/demo/create/cohorts/')
def add_demo_cohorts():
    db_session = db.get_session()
    user = db_session.query(User).filter_by(email=current_user.email).one()
    
    
    db_session.query(CohortUser).delete()
    db_session.query(CohortWikiUser).delete()
    db_session.query(WikiUser).delete()
    db_session.query(Cohort).delete()
    
    # add cohorts and assign ownership to the passed-in user
    db_session.add(Cohort(id=1, name='Algeria Summer Teahouse', description='', enabled=True))
    db_session.add(Cohort(id=2, name='Berlin Beekeeping Society', description='', enabled=True))
    db_session.add(Cohort(id=3, name='A/B April', description='', enabled=True))
    db_session.add(Cohort(id=4, name='A/B March', description='', enabled=True))
    db_session.add(Cohort(id=5, name='A/B February', description='', enabled=True))
    db_session.add(Cohort(id=6, name='A/B January', description='', enabled=True))
    db_session.add(Cohort(id=7, name='A/B December', description='', enabled=True))
    db_session.add(Cohort(id=8, name='A/B October', description='', enabled=True))
    db_session.add(Cohort(id=9, name='A/B September', description='', enabled=True))
    db_session.add(Cohort(id=10, name='A/B August', description='', enabled=True))
    db_session.add(Cohort(id=11, name='A/B July', description='', enabled=True))
    
    db_session.add(CohortUser(user_id=user.id, cohort_id=1, role=CohortUserRole.OWNER))
    db_session.add(CohortUser(user_id=user.id, cohort_id=2, role=CohortUserRole.OWNER))
    db_session.add(CohortUser(user_id=user.id, cohort_id=3, role=CohortUserRole.OWNER))
    db_session.add(CohortUser(user_id=user.id, cohort_id=4, role=CohortUserRole.OWNER))
    db_session.add(CohortUser(user_id=user.id, cohort_id=5, role=CohortUserRole.OWNER))
    db_session.add(CohortUser(user_id=user.id, cohort_id=6, role=CohortUserRole.OWNER))
    db_session.add(CohortUser(user_id=user.id, cohort_id=7, role=CohortUserRole.OWNER))
    db_session.add(CohortUser(user_id=user.id, cohort_id=8, role=CohortUserRole.OWNER))
    db_session.add(CohortUser(user_id=user.id, cohort_id=9, role=CohortUserRole.OWNER))
    db_session.add(CohortUser(user_id=user.id, cohort_id=10, role=CohortUserRole.OWNER))
    db_session.add(CohortUser(user_id=user.id, cohort_id=11, role=CohortUserRole.OWNER))
    
    # TODO: these users don't actually exist in the mediawiki databases, add them
    #db_enwiki_session = db.get_mw_session('enwiki')
    #db_dewiki_session = db.get_mw_session('dewiki')
    db_session.add(WikiUser(mediawiki_username='Dan', mediawiki_userid=1, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='Evan', mediawiki_userid=2, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='Andrew', mediawiki_userid=3, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='Diederik', mediawiki_userid=4, project='enwiki'))
    
    db_session.add(WikiUser(mediawiki_username='Andrea', mediawiki_userid=5, project='dewiki'))
    db_session.add(WikiUser(mediawiki_username='Dennis', mediawiki_userid=6, project='dewiki'))
    db_session.add(WikiUser(mediawiki_username='Florian', mediawiki_userid=7, project='dewiki'))
    db_session.add(WikiUser(mediawiki_username='Gabriele', mediawiki_userid=8, project='dewiki'))
    
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=9, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=10, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=11, project='enwiki'))
    
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=12, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=13, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=14, project='enwiki'))
    
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=15, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=16, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=17, project='enwiki'))
    
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=18, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=19, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=20, project='enwiki'))
    
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=21, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=22, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=23, project='enwiki'))
    
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=24, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=25, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=26, project='enwiki'))
    
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=27, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=28, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=29, project='enwiki'))
    
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=30, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=31, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=32, project='enwiki'))
    
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=33, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=34, project='enwiki'))
    db_session.add(WikiUser(mediawiki_username='n/a', mediawiki_userid=35, project='enwiki'))
    
    db_session.add(CohortWikiUser(wiki_user_id=1, cohort_id=1))
    db_session.add(CohortWikiUser(wiki_user_id=2, cohort_id=1))
    db_session.add(CohortWikiUser(wiki_user_id=3, cohort_id=1))
    db_session.add(CohortWikiUser(wiki_user_id=4, cohort_id=1))
    
    db_session.add(CohortWikiUser(wiki_user_id=5, cohort_id=2))
    db_session.add(CohortWikiUser(wiki_user_id=6, cohort_id=2))
    db_session.add(CohortWikiUser(wiki_user_id=7, cohort_id=2))
    db_session.add(CohortWikiUser(wiki_user_id=8, cohort_id=2))
    
    db_session.add(CohortWikiUser(wiki_user_id=9, cohort_id=3))
    db_session.add(CohortWikiUser(wiki_user_id=10, cohort_id=3))
    db_session.add(CohortWikiUser(wiki_user_id=11, cohort_id=3))
    
    db_session.add(CohortWikiUser(wiki_user_id=12, cohort_id=4))
    db_session.add(CohortWikiUser(wiki_user_id=13, cohort_id=4))
    db_session.add(CohortWikiUser(wiki_user_id=14, cohort_id=4))
    
    db_session.add(CohortWikiUser(wiki_user_id=15, cohort_id=5))
    db_session.add(CohortWikiUser(wiki_user_id=16, cohort_id=5))
    db_session.add(CohortWikiUser(wiki_user_id=17, cohort_id=5))
    
    db_session.add(CohortWikiUser(wiki_user_id=18, cohort_id=6))
    db_session.add(CohortWikiUser(wiki_user_id=19, cohort_id=6))
    db_session.add(CohortWikiUser(wiki_user_id=20, cohort_id=6))
    
    db_session.add(CohortWikiUser(wiki_user_id=21, cohort_id=7))
    db_session.add(CohortWikiUser(wiki_user_id=22, cohort_id=7))
    db_session.add(CohortWikiUser(wiki_user_id=23, cohort_id=7))
    
    db_session.add(CohortWikiUser(wiki_user_id=24, cohort_id=8))
    db_session.add(CohortWikiUser(wiki_user_id=25, cohort_id=8))
    db_session.add(CohortWikiUser(wiki_user_id=26, cohort_id=8))
    
    db_session.add(CohortWikiUser(wiki_user_id=27, cohort_id=9))
    db_session.add(CohortWikiUser(wiki_user_id=28, cohort_id=9))
    db_session.add(CohortWikiUser(wiki_user_id=29, cohort_id=9))
    
    db_session.add(CohortWikiUser(wiki_user_id=30, cohort_id=10))
    db_session.add(CohortWikiUser(wiki_user_id=31, cohort_id=10))
    db_session.add(CohortWikiUser(wiki_user_id=32, cohort_id=10))
    
    db_session.add(CohortWikiUser(wiki_user_id=33, cohort_id=11))
    db_session.add(CohortWikiUser(wiki_user_id=34, cohort_id=11))
    db_session.add(CohortWikiUser(wiki_user_id=35, cohort_id=11))
    
    
    db_session.commit()
    return 'OK, wiped out the database and added cohorts only for ' + current_user.email

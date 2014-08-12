from wikimetrics.configurables import app, db


@app.teardown_request
def remove_database_sessions(self):
    if db.wikimetrics_session:
        db.wikimetrics_session.remove()
    for project, session in db.mediawiki_sessions.items():
        session.remove()

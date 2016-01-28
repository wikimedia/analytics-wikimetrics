from wikimetrics.configurables import db, get_project_host_names_local
import MySQLdb

mediawiki_projects = get_project_host_names_local()
dbs = ["wikimetrics", "centralauth", "wikimetrics_testing", "wiki_testing",
       "wiki2_testing", "centralauth_testing"] + mediawiki_projects

con = MySQLdb.connect(user='root', passwd='', host='db')
cur = con.cursor()
for database in dbs:
    cur.execute("CREATE DATABASE IF NOT EXISTS {0};".format(database))
    cur.execute("GRANT ALL ON * . * TO wikimetrics;")

for project in mediawiki_projects:
    engine = db.get_mw_engine(project)
    db.MediawikiBase.metadata.create_all(engine, checkfirst=True)

ca_engine = db.get_ca_engine()
db.CentralAuthBase.metadata.create_all(ca_engine, checkfirst=True)

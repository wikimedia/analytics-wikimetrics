from wikimetrics.configurables import db

db.get_session().close()
db.get_session().close()
db.get_session().close()

# pool size is now three.

print("Restart the server")
raw_input()

for i in xrange(10):
    c = db.get_session()
    print(c.execute("select 1").fetchall())
    c.close()

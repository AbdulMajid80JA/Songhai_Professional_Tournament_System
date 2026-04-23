from flask import *
import sqlite3,csv
app=Flask(__name__)
DB='database.db'
def db():
 c=getattr(g,'d',None)
 if c is None:
  c=g.d=sqlite3.connect(DB); c.row_factory=sqlite3.Row
 return c
@app.before_request
def init(): db().execute("CREATE TABLE IF NOT EXISTS teams(id INTEGER PRIMARY KEY,team_name TEXT,manager TEXT,coach TEXT,captain TEXT,players INTEGER,year TEXT,payment TEXT)"); db().commit()
@app.route('/')
def h(): return render_template('index.html')
@app.route('/register',methods=['GET','POST'])
def r():
 import sqlite3
 if request.method=='POST':
  d=request.form; db().execute('INSERT INTO teams(team_name,manager,coach,captain,players,year,payment) VALUES(?,?,?,?,?,?,?)',(d['team_name'],d['manager'],d['coach'],d['captain'],d['players'],d['year'],d['payment'])); db().commit(); return redirect('/teams')
 return render_template('register.html')
@app.route('/teams')
def t():
 q=request.args.get('q',''); rows=db().execute('SELECT * FROM teams').fetchall(); return render_template('teams.html',teams=rows,q=q)
@app.route('/admin')
def a():
 total=db().execute('select count(*) c from teams').fetchone()['c']; return render_template('admin.html',total=total)
@app.route('/export')
def e():
 p='teams_export.csv'; rows=db().execute('select * from teams').fetchall(); import csv
 f=open(p,'w',newline='');w=csv.writer(f);[w.writerow(list(r)) for r in rows];f.close(); return send_file(p,as_attachment=True)
@app.route('/gallery')
def g1(): return render_template('gallery.html')
if __name__=='__main__': app.run()
from flask import (
    Flask, render_template, request,
    redirect, send_file, g, session
)

import sqlite3
import csv
import os
from werkzeug.utils import secure_filename

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "songhai_secret_key_2026"

DB = "database.db"
UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----------------------------
# DATABASE CONNECTION
# ----------------------------
def db():
    conn = getattr(g, "conn", None)
    if conn is None:
        conn = g.conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
    return conn


# ----------------------------
# INIT DATABASE (FIXED)
# ----------------------------
@app.before_request
def init_db():

    db().execute("""
    CREATE TABLE IF NOT EXISTS teams(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_name TEXT,
        manager TEXT,
        coach TEXT,
        captain TEXT,
        players INTEGER,
        year TEXT,
        payment TEXT,
        logo TEXT,
        roster TEXT,
        payment_proof TEXT
    )
    """)

    db().execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    db().execute("""
    CREATE TABLE IF NOT EXISTS matches(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_a TEXT,
        team_b TEXT,
        score_a INTEGER,
        score_b INTEGER,
        group_name TEXT
    )
    """)

 # ADD THIS PART (seed default admin if missing)
    existing = db().execute(
        "SELECT * FROM users WHERE username=?",
        ("admin",)
    ).fetchone()

    if not existing:
        db().execute(
            "INSERT INTO users(username,password) VALUES(?,?)",
            ("admin","1234")
        )

    db().commit()


@app.teardown_appcontext
def close_db(error):
    conn = getattr(g, "conn", None)
    if conn:
        conn.close()


# ----------------------------
# HOME
# ----------------------------
@app.route('/')
def home():
    return render_template("index.html")


# ----------------------------
# REGISTRATION
# ----------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == "POST":

        d = request.form

        # logo
        logo = request.files.get("team_logo")
        logo_name = ""
        if logo and logo.filename:
            logo_name = secure_filename(logo.filename)
            logo.save(os.path.join(UPLOAD_FOLDER, logo_name))

        # proof
        proof = request.files.get("payment_proof")
        proof_name = ""
        if proof and proof.filename:
            proof_name = secure_filename(proof.filename)
            proof.save(os.path.join(UPLOAD_FOLDER, proof_name))

        # roster
        roster = []
        for i in range(1, 26):
            p = d.get(f"player{i}")
            if p:
                roster.append(p)

        roster_text = ",".join(roster)

        db().execute("""
        INSERT INTO teams(
            team_name, manager, coach, captain,
            players, year, payment,
            logo, roster, payment_proof
        )
        VALUES(?,?,?,?,?,?,?,?,?,?)
        """, (
            d["team_name"],
            d["manager"],
            d["coach"],
            d["captain"],
            d["players"],
            d["year"],
            d["payment"],
            logo_name,
            roster_text,
            proof_name
        ))

        db().commit()

        new_id = db().execute("SELECT last_insert_rowid()").fetchone()[0]

        return redirect(f"/slip/{new_id}")

    return render_template("register.html")


# ----------------------------
# PDF SLIP
# ----------------------------
@app.route('/slip/<int:id>')
def slip(id):

    row = db().execute(
        "SELECT * FROM teams WHERE id=?",
        (id,)
    ).fetchone()

    filename = "registration_slip.pdf"
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()

    story = [
        Paragraph("🏆 SONGHAI SALLAH FOOTBALL GALA", styles["Title"]),
        Paragraph("OFFICIAL REGISTRATION SLIP", styles["Heading2"]),
        Paragraph("----------------------", styles["Normal"]),
        Paragraph(f"TEAM: {row['team_name']}", styles["BodyText"]),
        Paragraph(f"MANAGER: {row['manager']}", styles["BodyText"]),
        Paragraph(f"COACH: {row['coach']}", styles["BodyText"]),
        Paragraph(f"CAPTAIN: {row['captain']}", styles["BodyText"]),
        Paragraph(f"PLAYERS: {row['players']}", styles["BodyText"]),
        Paragraph("----------------------", styles["Normal"]),
        Paragraph("✔ Registered Successfully", styles["BodyText"]),
    ]

    doc.build(story)

    return send_file(filename, as_attachment=True)


# ----------------------------
# LOGIN (SAFE FIX)
# ----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = db().execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        if user:
            session["admin"] = True
            return redirect("/admin")

        return "Wrong Login"

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop("admin", None)
    return redirect('/')

# ----------------------------
# TEAMS
# ----------------------------
@app.route('/teams')
def teams():

    q = request.args.get('q', '')

    if q:
        rows = db().execute(
            "SELECT * FROM teams WHERE team_name LIKE ? ORDER BY id DESC",
            ('%' + q + '%',)
        ).fetchall()
    else:
        rows = db().execute(
            "SELECT * FROM teams ORDER BY id DESC"
        ).fetchall()

    return render_template("teams.html", teams=rows, q=q)


@app.route('/delete/<int:id>')
def delete_team(id):

    if not session.get("admin"):
        return redirect("/login")

    db().execute("DELETE FROM teams WHERE id=?", (id,))
    db().commit()

    return redirect('/teams')

@app.route('/approve/<int:id>')
def approve_team(id):

    if not session.get("admin"):
        return redirect("/login")

    db().execute(
        "UPDATE teams SET approved=1 WHERE id=?",
        (id,)
    )

    db().commit()

    return redirect('/teams')

# ----------------------------
# STATIC PAGES ROUTES (FIX 404 ISSUE)
# ----------------------------

@app.route('/gallery')
def gallery():
    return render_template("gallery.html")


@app.route('/news')
def news():
    return render_template("news.html")


@app.route('/rules')
def rules():
    return render_template("rules.html")

@app.route('/location')
def location():
    return render_template("location.html")

@app.route('/payment')
def payment():
    return render_template("payment.html")

# ----------------------------
# ADMIN
# ----------------------------
@app.route('/admin')
def admin():

    if not session.get('admin'):
        return redirect('/login')

    total = db().execute(
        "SELECT count(*) c FROM teams"
    ).fetchone()["c"]

    return render_template("admin.html", total=total)

# ----------------------------
# EXPORT PDF
# ----------------------------

@app.route('/export_pdf')
def export_pdf():

    if not session.get('admin'):
        return redirect('/login')

    rows=db().execute(
    'SELECT * FROM teams'
    ).fetchall()

    filename='team_registrations.pdf'

    doc=SimpleDocTemplate(
        filename
    )

    data=[[
    "ID",
    "Team",
    "Manager",
    "Coach",
    "Captain",
    "Players",
    "Year",
    "Payment"
    ]]

    for r in rows:
        data.append([
            r["id"],
            r["team_name"],
            r["manager"],
            r["coach"],
            r["captain"],
            r["players"],
            r["year"],
            r["payment"]
        ])


    table=Table(
        data,
        repeatRows=1
    )


    table.setStyle(TableStyle([

    # Header
    ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#4B0082")),
    ('TEXTCOLOR',(0,0),(-1,0),colors.white),
    ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
    ('FONTSIZE',(0,0),(-1,0),12),
    ('ALIGN',(0,0),(-1,-1),'CENTER'),

    # Body
    ('FONTNAME',(0,1),(-1,-1),'Helvetica'),
    ('FONTSIZE',(0,1),(-1,-1),10),

    # Zebra stripes
    ('ROWBACKGROUNDS',
     (0,1),
     (-1,-1),
     [colors.whitesmoke, colors.HexColor("#efe8ff")]
    ),

    # Borders
    ('GRID',(0,0),(-1,-1),1,colors.grey),

    # Padding
    ('TOPPADDING',(0,0),(-1,-1),8),
    ('BOTTOMPADDING',(0,0),(-1,-1),8),

    # Outer border emphasis
    ('BOX',(0,0),(-1,-1),2,colors.HexColor("#4B0082"))

    ]))


    title_style=getSampleStyleSheet()['Title']

    title=Paragraph(
    "Songhai Sallah Football Gala Tournament<br/>Team Registration Report",
    title_style
    )


    doc.build([
        title,
        table
    ])


    return send_file(
    filename,
    as_attachment=True
    )

# ----------------------------
# MATCH SAVE
# ----------------------------
@app.route('/add_match', methods=['POST'])
def add_match():

    if not session.get("admin"):
        return redirect("/login")

    d = request.form

    db().execute("""
    INSERT INTO matches(team_a, team_b, score_a, score_b, group_name)
    VALUES(?,?,?,?,?)
    """, (
        d["teamA"],
        d["teamB"],
        d["scoreA"],
        d["scoreB"],
        d.get("group", "A")
    ))

    db().commit()

    return redirect("/fixtures")


# ----------------------------
# FIXTURES
# ----------------------------
@app.route('/fixtures')
def fixtures():

    if not session.get("admin"):
        return redirect("/login")

    rows = db().execute(
        "SELECT team_name FROM teams LIMIT 16"
    ).fetchall()

    team_list = [t["team_name"] for t in rows]

    while len(team_list) < 16:
        team_list.append("Empty Slot")

    groups = {
        "A": team_list[0:4],
        "B": team_list[4:8],
        "C": team_list[8:12],
        "D": team_list[12:16]
    }

    return render_template("fixtures.html",
                           groups=groups,
                           teams=team_list)


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
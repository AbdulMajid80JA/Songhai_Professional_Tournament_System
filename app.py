from flask import (
    Flask, render_template, request,
    redirect, send_file, g, session,
    send_from_directory
)

import sqlite3
import os
import json
import base64
import qrcode

from io import BytesIO
from werkzeug.utils import secure_filename

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle,
    Image,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm


app = Flask(__name__)
app.secret_key = "songhai_secret_key_2026"

DB = "database.db"
UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# DATABASE CONNECTION
# =========================================================
def db():

    conn = getattr(g, "conn", None)

    if conn is None:
        conn = g.conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# INIT DATABASE
# =========================================================
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

    try:
        db().execute(
            "ALTER TABLE teams ADD COLUMN approved INTEGER DEFAULT 0"
        )
    except:
        pass

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

    existing = db().execute(
        "SELECT * FROM users WHERE username=?",
        ("admin",)
    ).fetchone()

    if not existing:

        db().execute(
            "INSERT INTO users(username,password) VALUES(?,?)",
            ("admin", "1234")
        )

    db().commit()


# =========================================================
# CLOSE DATABASE
# =========================================================
@app.teardown_appcontext
def close_db(error):

    conn = getattr(g, "conn", None)

    if conn:
        conn.close()


# =========================================================
# HOME
# =========================================================
@app.route('/')
def home():
    return render_template("index.html")


# =========================================================
# REGISTER TEAM
# =========================================================
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == "POST":

        d = request.form

        # TEAM LOGO
        logo = request.files.get("team_logo")
        logo_name = ""

        if logo and logo.filename:

            logo_name = secure_filename(logo.filename)

            logo.save(
                os.path.join(UPLOAD_FOLDER, logo_name)
            )

        # PAYMENT PROOF
        proof = request.files.get("payment_proof")
        proof_name = ""

        if proof and proof.filename:

            proof_name = secure_filename(proof.filename)

            proof.save(
                os.path.join(UPLOAD_FOLDER, proof_name)
            )

        # ROSTER
        roster = []

        for i in range(1, 26):

            p = d.get(f"player{i}")

            if p:
                roster.append(p)

        roster_text = ",".join(roster)

        db().execute("""

        INSERT INTO teams(

            team_name,
            manager,
            coach,
            captain,
            players,
            year,
            payment,
            logo,
            roster,
            payment_proof

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

        new_id = db().execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        return redirect(f"/slip/{new_id}")

    return render_template("register.html")


# =========================================================
# REGISTRATION SLIP PDF
# =========================================================
@app.route('/slip/<int:id>')
def slip(id):

    row = db().execute(
        "SELECT * FROM teams WHERE id=?",
        (id,)
    ).fetchone()

    filename = "registration_slip.pdf"

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "🏆 SONGHAI SALLAH FOOTBALL GALA TOURNAMENT",
            styles["Title"]
        )
    )

    story.append(
        Paragraph(
            "OFFICIAL REGISTRATION SLIP",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph("--------------------", styles["Normal"])
    )

    story.append(
        Paragraph(
            f"<b>TEAM:</b> {row['team_name']}",
            styles["BodyText"]
        )
    )

    story.append(
        Paragraph(
            f"<b>MANAGER:</b> {row['manager']}",
            styles["BodyText"]
        )
    )

    story.append(
        Paragraph(
            f"<b>COACH:</b> {row['coach']}",
            styles["BodyText"]
        )
    )

    story.append(
        Paragraph(
            f"<b>CAPTAIN:</b> {row['captain']}",
            styles["BodyText"]
        )
    )

    story.append(
        Paragraph(
            f"<b>PLAYERS:</b> {row['players']}",
            styles["BodyText"]
        )
    )

    # TEAM LOGO
    if row["logo"]:

        path = os.path.join(
            UPLOAD_FOLDER,
            row["logo"]
        )

        if os.path.exists(path):

            story.append(
                Paragraph(
                    "<b>TEAM LOGO</b>",
                    styles["Heading3"]
                )
            )

            story.append(
                Image(path, width=120, height=120)
            )

    # PAYMENT PROOF
    if row["payment_proof"]:

        path = os.path.join(
            UPLOAD_FOLDER,
            row["payment_proof"]
        )

        if os.path.exists(path):

            story.append(
                Paragraph(
                    "<b>PAYMENT PROOF</b>",
                    styles["Heading3"]
                )
            )

            story.append(
                Image(path, width=150, height=150)
            )

    # PLAYER ROSTER
    if row["roster"]:

        story.append(
            Paragraph(
                "<b>PLAYER ROSTER</b>",
                styles["Heading3"]
            )
        )

        for p in row["roster"].split(","):

            story.append(
                Paragraph(
                    f"- {p}",
                    styles["BodyText"]
                )
            )

    doc.build(story)

    return send_file(
        filename,
        as_attachment=True
    )


# =========================================================
# LOGIN
# =========================================================
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


# =========================================================
# LOGOUT
# =========================================================
@app.route('/logout')
def logout():

    session.pop("admin", None)

    return redirect('/')


# =========================================================
# TEAMS
# =========================================================
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

    return render_template(
        "teams.html",
        teams=rows,
        q=q
    )


# =========================================================
# DELETE TEAM
# =========================================================
@app.route('/delete/<int:id>')
def delete_team(id):

    if not session.get("admin"):
        return redirect("/login")

    db().execute(
        "DELETE FROM teams WHERE id=?",
        (id,)
    )

    db().commit()

    return redirect('/teams')


# =========================================================
# APPROVE TEAM
# =========================================================
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


# =========================================================
# REJECT TEAM
# =========================================================
@app.route('/reject/<int:id>')
def reject_team(id):

    if not session.get("admin"):
        return redirect("/login")

    db().execute(
        "UPDATE teams SET approved=0 WHERE id=?",
        (id,)
    )

    db().commit()

    return redirect('/teams')


# =========================================================
# GALLERY
# =========================================================
@app.route('/gallery')
def gallery():
    return render_template("gallery.html")


# =========================================================
# NEWS
# =========================================================
@app.route('/news')
def news():
    return render_template("news.html")


# =========================================================
# RULES
# =========================================================
@app.route('/rules')
def rules():
    return render_template("rules.html")


# =========================================================
# LOCATION
# =========================================================
@app.route('/location')
def location():
    return render_template("location.html")


# =========================================================
# PAYMENT
# =========================================================
@app.route('/payment')
def payment():
    return render_template("payment.html")


# =========================================================
# PRIVACY
# =========================================================
@app.route('/privacy')
def privacy():
    return render_template("payment.html")


# =========================================================
# PLAYER ID PAGE
# =========================================================
@app.route('/player_id')
def player_id():
    return render_template("player_id.html")


# =========================================================
# UPLOADS
# =========================================================
@app.route('/uploads/<filename>')
def uploaded_file(filename):

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename
    )


# =========================================================
# ADMIN
# =========================================================
@app.route('/admin')
def admin():

    if not session.get('admin'):
        return redirect('/login')

    total = db().execute(
        "SELECT COUNT(*) as c FROM teams"
    ).fetchone()["c"]

    return render_template(
        "admin.html",
        total=total
    )


# =========================================================
# EXPORT TEAM PDF
# =========================================================
@app.route('/export_pdf')
def export_pdf():

    if not session.get('admin'):
        return redirect('/login')

    rows = db().execute(
        'SELECT * FROM teams'
    ).fetchall()

    filename = 'team_registrations.pdf'

    doc = SimpleDocTemplate(filename)

    data = [[
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

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([

        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4B0082")),

        ('TEXTCOLOR', (0,0), (-1,0), colors.white),

        ('GRID', (0,0), (-1,-1), 1, colors.grey)

    ]))

    doc.build([table])

    return send_file(
        filename,
        as_attachment=True
    )


# =========================================================
# PLAYER ID PRO MAX PDF
# =========================================================
@app.route('/generate_cards_pdf', methods=['POST'])
def generate_cards_pdf():

    players = request.get_json()

    filename = "player_cards.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=8,
        leftMargin=8,
        topMargin=10,
        bottomMargin=10
    )

    styles = getSampleStyleSheet()

    elements = []

    cards = []

    for p in players:

        # PLAYER PHOTO
        player_img = ""

        if p.get("photo"):

            try:

                img_data = p["photo"].split(",")[1]

                img_bytes = base64.b64decode(img_data)

                player_img = Image(
                    BytesIO(img_bytes),
                    width=60,
                    height=70
                )

            except:
                pass

        # TEAM LOGO
        logo_img = ""

        if p.get("logo"):

            try:

                logo_data = p["logo"].split(",")[1]

                logo_bytes = base64.b64decode(logo_data)

                logo_img = Image(
                    BytesIO(logo_bytes),
                    width=35,
                    height=35
                )

            except:
                pass

        # QR CODE
        qr_text = f"""
        PLAYER: {p.get('name','')}
        TEAM: {p.get('team','')}
        POSITION: {p.get('position','')}
        """

        qr = qrcode.make(qr_text)

        qr_buffer = BytesIO()

        qr.save(qr_buffer)

        qr_buffer.seek(0)

        qr_img = Image(
            qr_buffer,
            width=40,
            height=40
        )

        # PLAYER INFO
        info = f"""
        <font size=9 color='white'>

        <b>{p.get('name','')}</b><br/>

        Team: {p.get('team','')}<br/>

        Position: {p.get('position','')}<br/>

        Age: {p.get('age','')}<br/>

        Blood: {p.get('blood','')}<br/>

        Phone: {p.get('phone','')}

        </font>
        """

        info_paragraph = Paragraph(
            info,
            styles["BodyText"]
        )

        card = Table([
            [
                player_img,
                info_paragraph,
                qr_img
            ],
            [
                "",
                logo_img,
                ""
            ]
        ], colWidths=[60, 150, 50])

        card.setStyle(TableStyle([

            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#4B0082")),

            ('TEXTCOLOR', (0,0), (-1,-1), colors.white),

            ('BOX', (0,0), (-1,-1), 2, colors.black),

            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.white),

            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),

            ('ALIGN', (0,0), (-1,-1), 'CENTER'),

            ('BOTTOMPADDING', (0,0), (-1,-1), 8),

        ]))

        cards.append(card)

    rows = []

    temp = []

    for c in cards:

        temp.append(c)

        if len(temp) == 2:

            rows.append(temp)

            temp = []

    if temp:
        rows.append(temp)

    final_table = Table(
        rows,
        colWidths=[95*mm, 95*mm]
    )

    final_table.setStyle(TableStyle([

        ('VALIGN', (0,0), (-1,-1), 'TOP'),

        ('BOTTOMPADDING', (0,0), (-1,-1), 12),

    ]))

    elements.append(final_table)

    doc.build(elements)

    return send_file(
        filename,
        as_attachment=True
    )


# =========================================================
# SAVE MATCH
# =========================================================
@app.route('/add_match', methods=['POST'])
def add_match():

    if not session.get("admin"):
        return redirect("/login")

    d = request.form

    db().execute("""

    INSERT INTO matches(
        team_a,
        team_b,
        score_a,
        score_b,
        group_name
    )

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


# =========================================================
# FIXTURES
# =========================================================
@app.route('/fixtures')
def fixtures():

    rows = db().execute(
        "SELECT * FROM teams ORDER BY id DESC LIMIT 16"
    ).fetchall()

    while len(rows) < 16:

        rows = list(rows)

        rows.append({
            "team_name":"Empty Slot",
            "logo":""
        })

    groups = {
        "A": rows[0:4],
        "B": rows[4:8],
        "C": rows[8:12],
        "D": rows[12:16]
    }

    return render_template(
        "fixtures.html",
        groups=groups,
        teams=rows
    )
# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
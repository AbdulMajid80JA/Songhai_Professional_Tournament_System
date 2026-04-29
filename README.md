Songhai Sallah Football Gala Tournament Management System

Overview

The Songhai Sallah Football Gala Tournament Management System is a Flask + SQLite web application designed to manage community football tournament operations from registration to fixtures administration.

It supports team registration, admin approvals, tournament fixtures, standings, PDF exports, static information pages, and mobile money payment guidance.

⸻

Core Features

1. Team Registration Module

Teams can register through an online form that captures:

* Team name
* Manager
* Coach
* Captain
* Number of players
* Tournament year
* Payment method
* Team logo upload
* Player roster (up to 25 players)
* Payment proof upload

How it works

1. User opens Register Team.
2. Completes form.
3. Uploads logo and payment proof.
4. Registration data is saved in SQLite (teams table).
5. System generates a registration slip in PDF.

⸻

2. Registration Slip Generator

After successful registration the system creates an official PDF slip containing:

* Tournament title
* Team information
* Captain and manager details
* Player count
* Registration confirmation

Generated using:

* ReportLab
* PDF table and paragraph layouts

⸻

3. Team Directory

Registered teams can be viewed through:

* Searchable teams listing
* Team records display
* Registration details review

Admin can:

* Approve teams
* Delete teams
* Export registrations

⸻

4. Team Approval System

Each team may be approved by administrators.

Approval logic:

* Pending teams show Approve button
* Clicking approve updates:

approved = 1

* Approved teams can display approved status.

⸻

5. Admin Dashboard

Protected admin panel provides:

* Admin login
* Total team count
* Export controls
* Fixtures access
* Registration management

⸻

6. Login System

Current system uses database-based login:

Users stored in:

users

Fields:

* username
* password

Successful login creates:

session['admin']=True

⸻

Tournament Engine

7. Fixtures Generator

Automatically:

* Pulls first 16 registered teams
* Creates:

Group A
Group B
Group C
Group D

4 teams per group.

Also supports:

* Round-robin generated fixtures
* Group stage schedule generation
* Quarterfinal bracket creation

⸻

8. Live Standings Logic

Tracks:

* Played
* Wins
* Draws
* Losses
* Goals For
* Goals Against
* Points

Sorting logic:

1. Points
2. Goal Difference
3. Goals Scored

Standings auto-sort first to fourth.

⸻

9. Auto Qualification Logic

System automatically picks:

* Group Winner
* Runner-up

And fills:

* Quarterfinal pairings
* Semi-final bracket structure
* Final championship bracket

Example:

Winner A vs Runner-up B

Winner B vs Runner-up A

⸻

10. Match Result Entry

Admins can:

* Select two teams
* Enter scores
* Update standings
* Save match results

Stored in:

matches

Fields:

* team_a
* team_b
* score_a
* score_b
* group_name

⸻

Payment System

11. Payment Page

Dedicated payment interface includes:

* Registration fee display
* MTN Ghana Mobile Money instructions
* Payment reference instructions
* QR payment placeholder
* Proof upload reminder

⸻

12. Planned MoMo Merchant API Support

Prepared for:

* MTN Merchant integration
* Request-to-Pay API
* Transaction verification
* Automatic paid/unpaid team status

Future fields:

payment_status
transaction_id
payment_reference

⸻

Exports

13. Registration PDF Export

Exports all teams in styled PDF:

Includes:

* Purple branded header
* Zebra-striped rows
* Tournament report title
* Multi-page header repeat

⸻

14. CSV Export

Exports:

teams_export.csv

Containing:

* Team
* Manager
* Coach
* Captain
* Players
* Payment

⸻

Static Information Pages

15. Gallery Page

Contains:

* Tournament editions archive
* Historic photos
* Lightbox image viewer
* Winners archive

⸻

16. Rules Page

Contains:

* Competition regulations
* Eligibility rules
* Protest procedures
* Discipline sanctions
* Prize structure

⸻

17. News Page

Contains:

* Tournament bulletins
* Sponsor section
* Registration announcements
* Alert ticker

⸻

18. Location Page

Venue:

ZIORME Park, Aflao, Ghana

Contains:

* Embedded Google map
* Directions link
* Venue gallery
* Facility details

⸻

Technology Stack

Backend

* Python
* Flask
* SQLite3

Frontend

* HTML
* CSS
* JavaScript
* Jinja2 templates

Libraries

* ReportLab
* Werkzeug

⸻

Project Structure

Songhai_Professional_Tournament_System/
│
├── app.py
├── database.db
├── README.md
│
├── templates/
│   ├── index.html
│   ├── register.html
│   ├── teams.html
│   ├── admin.html
│   ├── fixtures.html
│   ├── gallery.html
│   ├── rules.html
│   ├── news.html
│   ├── location.html
│   └── payment.html
│
├── static/
│   ├── css/style.css
│   └── images/
│
└── uploads/

⸻

Database Tables

teams

id
team_name
manager
coach
captain
players
year
payment
logo
roster
payment_proof
approved

⸻

users

id
username
password

⸻

matches

id
team_a
team_b
score_a
score_b
group_name

⸻

Running the System

Install dependencies:

pip install flask reportlab werkzeug

Run:

python app.py

Open:

http://127.0.0.1:5000

⸻

Admin Features Summary

Admin can:

* Login
* Approve teams
* Delete teams
* Export PDF
* Export CSV
* Manage fixtures
* Enter results
* Update standings
* View tournament brackets

⸻

Future Upgrades (Planned)

Potential next upgrades:

* Full MTN MoMo Merchant API
* WhatsApp auto-confirmation after registration
* Automatic fixture scheduling engine
* Live score updates
* Referee management module
* Player cards / suspensions tracking
* Online public standings board
* Trophy honors archive

⸻

Author / Project

Developed for:

Songhai Sallah Football Gala Tournament

Community tournament management platform for registration, fixtures, administration and competition operations.

⸻

License

Private tournament management system.
Customize and extend as needed.


Deploy on Render: pip install -r requirements.txt ; gunicorn app:app

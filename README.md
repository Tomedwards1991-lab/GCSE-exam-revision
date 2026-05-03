# GCSE Computer Science VLE

A Django VLE for practising WJEC GCSE Computer Science Unit 2 past-paper style questions, especially the repeat HTML and Greenfoot practical tasks, with generated variants, auto-marked attempts, worked walkthroughs, and exam technique guides.

## Current Slice

- Django app with Bootstrap templates.
- Unit/paper/question domain model focused on WJEC Unit 2 and expandable later.
- HTML and Greenfoot question patterns based on the supplied paper/mark-scheme structure.
- Practice flow with one-question-at-a-time attempts.
- Step-by-step answer walkthrough after submitting.
- Separate exam guide section.
- English-only learner surface for now.
- Heuristic auto-marking that highlights likely earned and missed mark points.
- Generated-question service hook with a local rules-based fallback.
- Role-based user management for students, teachers, and admins.
- Teacher dashboards for assigned-student attempts, metrics, and generated improvement feedback.
- Admin user tools for creating users, changing roles, resetting passwords, and assigning students to teachers.
- Seed command for a small Unit 2 demo dataset.

## Run Locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

By default the project uses SQLite for local development. Set `DATABASE_URL` to a PostgreSQL URL when deploying or developing against Postgres.

## Useful Commands

```bash
python manage.py createsuperuser
python manage.py seed_demo --reset
python manage.py import_past_papers --replace
python manage.py test
```

## Demo Accounts

After `python manage.py seed_demo`, these local accounts are available:

- Student: `student` / `chinchilla`
- Teacher: `teacher` / `chinchilla`
- Admin: `admin` / `chinchilla`

The demo teacher is assigned to the demo student. Admin users can also use `/admin/` because the scaffold marks them as Django staff users.

## Imported PDFs

The attached papers and mark schemes are listed in `docs/source_papers.md`. The importer validates that every referenced resource exists before loading the structured question bank.

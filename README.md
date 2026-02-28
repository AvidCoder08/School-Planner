<<<<<<< ours
=======
# School-Planner (AcademaSync)

A runnable baseline implementation of **AcademaSync** built with **Python + Flet**.

## Implemented modules

- Email/password sign-up and sign-in (local SQLite storage for baseline).
- First-time onboarding for academic year and semester dates.
- Dashboard with:
  - current date/time
  - today's timetable (or next scheduled day)
  - due-today/tomorrow tasks
- Subject management (add/delete)
- Task management (add/delete/mark complete)
- Grade entry and calculation:
  - 2/4-credit normalized theory score
  - 5-credit theory-lab blend (80/20)
  - letter grade + grade point mapping
  - SGPA computation

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Notes

- Firebase integration entrypoint placeholder exists in `app/services/firebase_service.py`; current app uses SQLite to remain immediately runnable in this repository.
- Product/spec documentation remains in `docs/PROJECT_SPEC.md`.
>>>>>>> theirs

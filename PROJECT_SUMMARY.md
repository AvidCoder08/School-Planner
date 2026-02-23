# SkoolPlannr Project Summary

## Overview
SkoolPlannr is a student planner and grade tracker with a Python backend and a Flutter frontend.

## Backend
- Framework: FastAPI
- Entrypoint: `src/skoolplannr/app.py`
- Services:
  - `src/skoolplannr/services/auth_service.py`
  - `src/skoolplannr/services/appwrite_service.py`
- Domain logic:
  - `src/skoolplannr/core/grades.py`
  - `src/skoolplannr/core/gpa.py`

## API Scope
- Auth: signup/login
- Profile + onboarding
- Subjects CRUD
- Tasks CRUD + completion updates
- Events CRUD
- Grades save/list

## Frontend
- Framework: Flutter
- Location: `frontend/flutter`
- Target: Web now, with shared Flutter code for future multi-platform builds

## Running Locally
- Install: `python -m pip install -r requirements.txt`
- Start server: `run.bat`
- Open API docs: `http://localhost:8555/docs`

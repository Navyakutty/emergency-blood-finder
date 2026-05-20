#!/usr/bin/env bash
pip install -r requirements.txt
python -c "import flask_app; flask_app.get_db()"

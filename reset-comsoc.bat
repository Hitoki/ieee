
cmd /c create_db.bat
manage.py syncdb --noinput
manage.py loaddata data-comsoc.json

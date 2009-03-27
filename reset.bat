
cmd /c create_db.bat
@REM manage.py syncdb
manage.py syncdb --noinput
manage.py loaddata data.json

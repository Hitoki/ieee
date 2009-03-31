
cmd /c create_db.bat
@REM manage.py syncdb
@REM manage.py syncdb --noinput
manage.py dmigrate all
@REM manage.py loaddata data.json
load < fixtures\data-full-no-create.sql

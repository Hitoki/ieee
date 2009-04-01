
cmd /c create_db.bat
@REM manage.py syncdb
manage.py syncdb --noinput
@REM manage.py dmigrate all
manage.py loaddata data.json
@REM load < fixtures\data-full-no-create.sql

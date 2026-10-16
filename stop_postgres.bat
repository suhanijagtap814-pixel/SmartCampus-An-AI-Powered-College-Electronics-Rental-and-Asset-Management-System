@echo off
echo Stopping PostgreSQL 16 server...
"C:\Users\Nayan\pgsql\bin\pg_ctl.exe" -D "C:\Users\Nayan\pgsql\data" stop
echo PostgreSQL stopped.
pause

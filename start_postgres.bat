@echo off
echo Starting PostgreSQL 16 server...
"C:\Users\Nayan\pgsql\bin\pg_ctl.exe" -D "C:\Users\Nayan\pgsql\data" -l "C:\Users\Nayan\pgsql\data\server.log" start
echo PostgreSQL started successfully on port 5432.
pause

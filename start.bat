@ECHO off
TITLE Arc
:input
set debug=
set /p debug=Do you want to run in debug mode? [Y/N] 
if "%debug%"=="" goto input
if "%debug%"=="y" goto debug
if "%debug%"=="Y" goto debug
if "%debug%"=="n" goto nodebug
if "%debug%"=="N" goto nodebug
:debug
C:\Python26\python.exe run.py --debug
goto quit
:nodebug
C:\Python26\python.exe run.py
goto quit
:quit
PAUSE
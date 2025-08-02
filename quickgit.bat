cls
@echo off
git add .
set /p commitMessage="commit message: "
git commit -m "%commitMessage%"
git push --set-upstream origin master
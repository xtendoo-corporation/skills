#!/bin/bash
git init
if git remote | grep -q origin; then
    git remote set-url origin https://github.com/xtendoo-corporation/skills
else
    git remote add origin https://github.com/xtendoo-corporation/skills
fi
git add .
git commit -m "Subida inicial de ficheros"
git branch -M main
git push -u origin main

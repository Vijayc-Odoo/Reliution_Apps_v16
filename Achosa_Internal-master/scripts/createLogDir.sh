#!/bin/bash

PATH_TO_LOG=/home/odoo/src/user/scripts/logs/
mkdir -p $PATH_TO_LOG
if ! [ -e "$PATH_TO_LOG/.gitignore" ]; then # create .gitignore file for logs folder if it does not already exist
    echo "Created './logs/.gitignore'"
    echo '*' > "$PATH_TO_LOG/.gitignore"
    echo '!.gitignore' >> "$PATH_TO_LOG/.gitignore"
fi
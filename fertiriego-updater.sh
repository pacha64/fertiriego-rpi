#!/bin/bash

cd ~/fertiriego-rpi
# if git pull; then

# fi
git remote update

UPSTREAM=${1:-'@{u}'}
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse "$UPSTREAM")
BASE=$(git merge-base @ "$UPSTREAM")

if [ $LOCAL = $REMOTE ]; then
    echo "Up-to-date"
elif [ $LOCAL = $BASE ]; then
    echo "Need to pull"
    git pull
    sudo cp fertiriego.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl restart fertiriego.service
fi

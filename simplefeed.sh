#!/bin/bash

python3 simple_feed.py -i terms.csv

if [ $? -eq 0 ]; then
    echo "SimpleFeed completed successfully"
else
    echo "SimpleFeed encountered an error"
fi

#!/bin/bash

# Set the path to your project directory
PROJECT_DIR="/home/hl2dmserver/discord_bot"

# Activate virtual environment if you're using one
# source $PROJECT_DIR/venv/bin/activate

# Change to the project directory
cd $PROJECT_DIR

# Run the Python script
/usr/bin/python3 $PROJECT_DIR/hl2dm_log_processor.py >> $PROJECT_DIR/cron.log 2>&1

# Deactivate virtual environment if you activated one
# deactivate

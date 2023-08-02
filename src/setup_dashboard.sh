#!/usr/bin/env bash

DASHBOARD_DIR=./dashboard

echo 'Creating user-facing dashboard directory at' $DASHBOARD_DIR

# Remove existing dashboard directory
if test -d "$DASHBOARD_DIR"; then
    rm -r $DASHBOARD_DIR
fi

# Recreate
mkdir $DASHBOARD_DIR

# Copy in config and app
cp ./src/config.yml $DASHBOARD_DIR/
cp ./src/st_dashboard.py $DASHBOARD_DIR/

# Change directory in config file
# The if statement accounts for different bash syntax on different systems.
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's|test_data|data|g' $DASHBOARD_DIR/config.yml
else:
    sed -i 's|test_data|data|g' $DASHBOARD_DIR/config.yml
fi
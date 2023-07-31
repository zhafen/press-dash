#!/usr/bin/env bash

DASHBOARD_DIR=./dashboard

echo 'Creating user-facing dashboard directory at' $DASHBOARD_DIR

# Remove existing dashboard directory
if test -d "$DASHBOARD_DIR"; then
    rm -r $DASHBOARD_DIR
fi

# Recreate
mkdir $DASHBOARD_DIR

# Copy in config
cp ./src/config.yml $DASHBOARD_DIR/

# Change directory in config file
sed -i '' 's|data_dir: ../test_data|data_dir: ../data|g' $DASHBOARD_DIR/config.yml
#!/usr/bin/env bash

DATA_DIR=./data

echo 'Creating user-facing data directory at' $DATA_DIR

# Remove if already present
if test -d "$DATA_DIR"; then
    rm -r $DATA_DIR
fi
# Copy data
cp -r ./test_data $DATA_DIR
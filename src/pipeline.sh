#!/usr/bin/env bash

# Get the current directory
SRC_DIR=$(dirname $(realpath $0))
LOGS_DIR=$(dirname $SRC_DIR)/logs
echo "Source directory: $SRC_DIR"
echo "Logs directory: $LOGS_DIR"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")

# Get the config location from the user
CONFIG_FP=$1
CONFIG_DIR=$(dirname $(realpath $CONFIG_FP))
cd $CONFIG_DIR
echo "Config directory: $CONFIG_DIR"

# Make the working directory the location of the config
echo "Switching to config directory."
cd $CONFIG_DIR

# Run the data transformation
jupyter nbconvert --to notebook --execute $SRC_DIR/transform.ipynb --output=transform.$TIMESTAMP.ipynb --output-dir=$LOGS_DIR


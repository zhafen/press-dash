#!/usr/bin/env bash

# Config filepath is provided on the command line
CONFIG_FP=$1

# User notebooks
# Relative paths, relative to the source directory
USER_NBS=(transform.ipynb)

###############################################################################
# Probably don't touch below unless you know what you're doing
###############################################################################
echo "Starting pipeline..."
echo 

# Get the current directory
SRC_DIR=$(dirname $(realpath $0))
LOGS_DIR=$(dirname $SRC_DIR)/logs
echo "Source directory: $SRC_DIR"
echo "Logs directory: $LOGS_DIR"
mkdir -p $LOGS_DIR
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")
echo "Timestamp for logs: $TIMESTAMP"

# Get the config location from the user
CONFIG_DIR=$(dirname $(realpath $CONFIG_FP))
cd $CONFIG_DIR
echo "Config (working) directory: $CONFIG_DIR"
echo

# Convert and execute the notebooks
echo "Converting and executing notebooks..."
for USER_NB in ${USER_NBS[@]}; do
    echo "    $USER_NB"
    USER_NB_BASENAME=$(basename $USER_NB)
    (
    jupyter nbconvert \
        --to script \
        $(realpath $SRC_DIR/$USER_NB) \
        --output=${USER_NB_BASENAME/.ipynb/.$TIMESTAMP} \
        --output-dir=$LOGS_DIR \
    ) > $LOGS_DIR/$USER_NB_BASENAME.conversion.txt
    echo 
done


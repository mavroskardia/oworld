#!/bin/bash

echo -n "Finding all files that match pattern \"*.py?\"..."
find -iname "*.py?" -exec rm {} \;
echo "done"


#!/bin/bash

# Shell script to deploy a heroku-dash app
# Will exhaustively search over letters provided to enable indexing

unset letters

while getopts "l:" opt; do
   case "$opt" in
      l ) letters="$OPTARG" ;;
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$letters" ]; then
   echo "Some or all of the parameters are empty";
   echo "Usage: bash gen_dash.sh -l [abcd]"
   return
fi

echo "---letters to be used: $letters ---"

# SET UP CONDA ENVIRONMENT!!!
# conda activate bok

# Call python script to generate the words and data
echo "Running gen_data.py"
# python gen_data.py --letters $letters


echo "~~~ End of gen_dash.sh ~~~"
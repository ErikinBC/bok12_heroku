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
   echo "Usage: bash gen_dash.sh -l abcdef"
   return
fi

echo "---letters to be used: $letters ---"

# Source conda to allow for "activate"
path_conda=$(which conda | awk '{split($0,a,"/bin"); print a[1]}')
path_conda=$path_conda/etc/profile.d/conda.sh
source $path_conda
{
   conda activate heroku
} || {
   echo "heroku environment not found in conda, creating"
   conda create --name heroku python=3.10
   conda activate heroku
   conda install pandas numpy plotnine nltk requests dash dash-extensions gunicorn
}

# Export requirement list
conda list -e | awk '{split($0,a,"="); print a[1]"=="a[2]}' | grep -v "_" | grep -v "#" > requirements.txt

# Call python script to generate the words and data
echo "Running gen_data.py"
python gen_data.py --letters $letters

echo "Building heroku app"
sudo heroku login
sudo heroku create cipher-poem
git add .
git commit -m "files for cipher_poem"

sudo git push heroku main


echo "~~~ End of gen_dash.sh ~~~"
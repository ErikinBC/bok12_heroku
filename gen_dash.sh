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
lst_requirements=$(cat requirements.txt)
{
   conda activate heroku
} || {
   echo "heroku environment not found in conda, creating"
   conda create --name heroku python=3.10
   conda activate heroku
   conda install $lst_requirements
}

# Export requirement list in pip format
conda list -e | awk '{split($0,a,"="); print a[1]"=="a[2]}' | grep -v "_" | grep -v "#" | grep -v brotli | grep -v bzip> requirements.txt

# Call python script to generate the words and data
echo "Running gen_data.py"
python gen_data.py --letters $letters

echo "Building heroku app (change cipher-poem!)"
name_heroko="cipher-poem"
sudo heroku login
sudo heroku create $name_heroko
git remote add heroku https://git.heroku.com/$name_heroko.git
git add .
git commit -m "files for $name_heroku"
sudo git push heroku main


echo "~~~ End of gen_dash.sh ~~~"
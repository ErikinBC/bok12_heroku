#!/bin/bash

# Shell script to deploy a heroku-dash app
# Will exhaustively search over letters provided to enable indexing

unset letters
unset name_heroko

usage() { echo -e "At least one argument is empty\nUsage: $0 bash gen_dash.sh -l [letters] -n [your-app-name]\nExample: bash gen_dash.sh -l abcdef -n cipher-poem" 1>&2; exit 1; }

while getopts ":l:n:" o; do
    case "${o}" in
        l) letters=${OPTARG} ;;
        n) name_heroko=${OPTARG} ;;
        *) usage ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${letters}" ] || [ -z "${name_heroko}" ]; then
    usage
fi

echo "letters = ${letters}"
echo "name_heroko = ${name_heroko}"

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

# Call python script to generate the words and data
echo "Running gen_data.py"
python gen_data.py --letters $letters

echo "Building heroku app (change cipher-poem!)"
sudo heroku login
sudo heroku create $name_heroko
git remote add heroku https://git.heroku.com/$name_heroko.git
git add .
git commit -m "files for $name_heroku"
sudo git push heroku main


echo "~~~ End of gen_dash.sh ~~~"
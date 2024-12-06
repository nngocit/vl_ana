# commit to csv_data
#!/usr/bin/env bash

URL=https://github.com/nngocit/vl_ana.git
FOLDER=vietlott-data
DATA_FOLDER=data
USER="nngocit"
EMAIl="xuanngocit@gmail.com"

# generate data file
echo "pwd $(pwd)"

export PYTHONPATH="src"
export LOGURU_LEVEL="INFO"

python src/vietlott/cli/crawl.py keno
python src/vietlott/cli/missing.py keno
python src/vietlott/cli/crawl.py power_655
python src/vietlott/cli/missing.py power_655
python src/vietlott/cli/crawl.py power_645
python src/vietlott/cli/missing.py power_645
python src/vietlott/cli/crawl.py 3d
python src/vietlott/cli/missing.py 3d
python src/vietlott/cli/crawl.py 3d_pro
python src/vietlott/cli/missing.py 3d_pro

python src/render_readme.py

#if [[ ! -d "$FOLDER" ]] ; then
#  git clone $URL $FOLDER
#fi

#cp -r $DATA_FOLDER $FOLDER/

#cd $FOLDER
#git pull

# commit and push
git config user.name "\'$USER\'"
git config user.email "\'$EMAIl\'"
git status
git add $DATA_FOLDER
git add readme.md
git commit -m "update data @ `date +%Y-%m-%d\ %H:%M:%S`"
git push

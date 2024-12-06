#!/usr/bin/env bash

# Repository và thư mục liên quan
URL=https://github.com/nngocit/vl_ana.git
FOLDER=vietlott-data
DATA_FOLDER=data
USER="nngocit"
EMAIL="xuanngocit@gmail.com"

# Log thư mục hiện tại
echo "Current working directory: $(pwd)"

# Cấu hình môi trường
export PYTHONPATH="src"
export LOGURU_LEVEL="INFO"

# Generate data file
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

# Cấu hình Git
git config user.name "$USER"
git config user.email "$EMAIL"

# Kiểm tra trạng thái repository
git status

# Add và commit dữ liệu
git add "$DATA_FOLDER" readme.md

if git diff-index --quiet HEAD --; then
  echo "No changes to commit."
else
  git commit -m "update data @ $(date '+%Y-%m-%d %H:%M:%S')"
  git push
fi

# Röntgen

place the files in the right place

weights/
r2g/annotation.json

update .env with 
```commandline
PORT=5000
ALLOWED_HOST="106.51.172.169"
```

ready system
````commandline
sudo apt update && sudo apt upgrade 
sudo apt install libopencv-dev


ssh-keygen -t ed25519 -C "dhrvmohapatra@gmail.com"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sha256sum Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
rm Miniconda3-latest-Linux-x86_64.sh

conda create -n ro python=3.10.12
conda activate ro

pip install -r requirements.txt

gunicorn -c gc_config.py main:app
````
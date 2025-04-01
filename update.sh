git pull origin main
. ./venv/bin/activate
pip install --upgrade -r requirements.txt
python3 manage.py collectstatic --noinput
python3 manage.py migrate
sudo systemctl restart exchange_hub
sudo systemctl daemon-reload
sudo systemctl restart exchange_hub.socket exchange_hub.service
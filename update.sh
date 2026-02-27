git pull origin main
uv sync
uv run manage.py collectstatic --noinput
uv run manage.py migrate
sudo systemctl restart exchange_hub
sudo systemctl daemon-reload
sudo systemctl restart exchange_hub.socket exchange_hub.service
sudo pip3 install --break-system-packages setuptools
sudo apt install -y libffi-dev
sudo pip3 install --break-system-packages cffi
# Install jupyterlab via pip
sudo pip3 install --break-system-packages jupyterlab

sudo cp jupyter.service /etc/systemd/system

#adjust this so it is not dubplicated when running twice.
sed -i "2i127.0.0.1  web.localhost web.raspberrypi.local" /etc/hosts
sed -i "2i127.0.0.1  jupyter.localhost jupyter.raspberrypi.local" /etc/hosts



sudo pip install --break-system-packages -r common/picamera2-flask/requirements.txt
#sudo pip3 install --break-system-packages pyro5
sudo cp common/picamera2-flask/picamera2-flask.service /etc/systemd/system

sudo systemctl daemon-reload


sudo systemctl stop jupyter.service

sudo systemctl start jupyter.service

sudo systemctl enable jupyter.service



sudo systemctl stop picamera2-flask.service

sudo systemctl start picamera2-flask.service

sudo systemctl enable picamera2-flask.service

# Nginx forwards port 80 to port 8000, which is used by Flask
# Copy ams_nginx_config to the available site folder
sudo cp common/ams_nginx_config /etc/nginx/sites-available/ams_nginx_config
# Set the right permission for the config file
sudo chmod 644 /etc/nginx/sites-available/ams_nginx_config
# Remove the default enabled config
sudo rm -f /etc/nginx/sites-enabled/default
# Create a symbolic link at sites-enabled that points to sites-available/ams_nginx_config
sudo ln -fs /etc/nginx/sites-available/ams_nginx_config /etc/nginx/sites-enabled/ams_nginx_config



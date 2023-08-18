pip install -r common/picamera2-flask/requirements.txt
#pip3 install pyro5
sudo cp common/picamera2-flask/picamera2-flask.service /lib/systemd/system

sudo systemctl daemon-reload

sudo systemctl stop picamera2-flask.service

sudo systemctl start picamera2-flask.service

sudo systemctl enable picamera2-flask.service

#pip3 install pyro5
sudo cp common/ams_web.service /lib/systemd/system

systemctl daemon-reload

sudo systemctl stop ams_web.service

sudo systemctl start ams_web.service
sudo systemctl enable ams_web.service

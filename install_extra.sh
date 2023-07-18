#pip3 install pyro5
sudo cp common/ams_pyro.service /lib/systemd/system
sudo cp common/ams_server.service /lib/systemd/system
sudo cp common/ams_web.service /lib/systemd/system

sudo systemctl daemon-reload

sudo systemctl stop ams_server.service
sudo systemctl stop ams_pyro.service
sudo systemctl stop ams_web.service

sudo systemctl start ams_pyro.service
sudo systemctl start ams_server.service
sudo systemctl start ams_web.service

sudo systemctl enable ams_pyro.service
sudo systemctl enable ams_server.service
sudo systemctl enable ams_web.service

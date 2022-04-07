if lsmod | grep mira220pmic &> /dev/null; then echo "Reload mira220pmic"; sudo sh -c "rmmod mira220pmic && modprobe mira220pmic"; else echo "Load mira220pmic"; sudo sh -c "modprobe mira220pmic"; fi

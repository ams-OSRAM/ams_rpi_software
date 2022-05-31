if lsmod | grep mira050pmic &> /dev/null; then echo "Reload mira050pmic"; sudo sh -c "rmmod mira050pmic && modprobe mira050pmic"; else echo "Load mira050pmic"; sudo sh -c "modprobe mira050pmic"; fi

import asyncio
import os
import glob
from kasa import SmartPlug

LivingRoomLamp = "192.168.2.107"
CarCharger = "192.168.2.203"
GarageHeater = "192.168.2.210"
GreenhouseHeater = "192.168.2.200"

HeaterOnTemp = 13
HeaterOffTemp = 23

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def read_temp_raw():
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

def read_temp():
	lines = read_temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		return temp_c

async def main():
	# Initialize devices
	heater_plug = SmartPlug(LivingRoomLamp)
	os.system('modprobe w1-gpio')
	os.system('modprobe w1-therm')

	# Main loop
	while True:
		# Get temperature
		temperature = read_temp()
		print('Temperature: ' + str(temperature) + ' degC')

		# Get plug status
		await heater_plug.update()
		print('Heater status: ' + str(heater_plug.is_on))

		if (temperature < HeaterOnTemp) and (heater_plug.is_off):
			print('Turning heater on')
			await heater_plug.turn_on()
		elif (temperature > HeaterOffTemp) and (heater_plug.is_on):
			print('Turning heater off')
			await heater_plug.turn_off()
		await asyncio.sleep(1)	

if __name__ == "__main__":
	asyncio.run(main())


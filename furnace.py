import asyncio
import os
import glob
import datetime
import uptime
from kasa import SmartPlug

# Kasa devices
LivingRoomLamp = "192.168.2.107"
CarCharger = "192.168.2.203"
GarageHeater = "192.168.2.210"
GreenhouseHeater = "192.168.2.202"

# Furnace temps
HeaterOnTemp = 16 
HeaterOffTemp = 21 

# Temperature sensor 
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

# Main function
async def main():
	# If we just booted, sleep for a bit to allow pi to finish booting and connect to network
	if uptime.uptime() < 60: 
		print('Sleeping for 60 seconds')
		await asyncio.sleep(60)

	# Initialize devices
	heater_plug = SmartPlug(GreenhouseHeater)
	os.system('modprobe w1-gpio')
	os.system('modprobe w1-therm')

	# Turn heater on to start
	print('Turning heater on')
	await heater_plug.turn_on()
	await asyncio.sleep(5)

	# Main loop
	while True:
		# Get temperature
		temperature = read_temp()
		print('Temperature: ' + str(temperature) + ' degC')
		#os.system('echo Temperature: ' + str(temperature) + ' degC | wall')	

		# Get timestamp
		utc_dt = datetime.datetime.now()
		print("Local time {}".format(utc_dt.astimezone().isoformat()))

		# Get plug status
		await heater_plug.update()
		print('Heater status: ' + str(heater_plug.is_on))
		#os.system('echo Heater status: ' + str(heater_plug.is_on) + ' | wall')

		if (temperature < HeaterOnTemp) and (heater_plug.is_off):
			print('Turning heater on')
			await heater_plug.turn_on()
		elif (temperature > HeaterOffTemp) and (heater_plug.is_on):
			print('Turning heater off')
			await heater_plug.turn_off()
		await asyncio.sleep(10)	

if __name__ == "__main__":
	asyncio.run(main())


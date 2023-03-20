import asyncio
import sys
import os
import RPi.GPIO as GPIO 
import glob
import requests
import json
import datetime
import uptime
import csv
from kasa import SmartPlug

# Task timing
GlobalTimeStep_Sec = 1
FurnaceTimeStep_Sec = 60
WeatherTimeStep_Sec = 3600
LightTimeStep_Sec = 1800
TemperatureTimeStep_Sec = 60
LogTimeStep_Sec = 60

# Kasa smart plug devices
LivingRoomLamp = "192.168.2.107"
CarCharger = "192.168.2.203"
GarageHeater = "192.168.2.210"
GreenhouseHeater = "192.168.2.202"

# Furnace thresholds 
EnableFurnace = 0
HeaterOnTemp = 16 
HeaterOffTemp = 21 

# Weather query
base_url = "https://api.openweathermap.org/data/2.5/weather?"
city = "london,ca"
api_key = "c96d2072fe0338fe2dc734f9d90793c4"
units = "metric"
weather_query = base_url + "q=" + city + "&units=" + units + "&appid=" + api_key

# Light control 
EnableLights = 0
LED_TOP_1 = 12
LED_TOP_2 = 16

# Temperature sensor interface 
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# Log file
log_file = 'greenhouse_log.csv' 

# Tasks
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

# Tasks
async def init_task():
	print('Initializing devices')

	# Initialize temperature sensor
	os.system('modprobe w1-gpio')
	os.system('modprobe w1-therm')

	# Turn lights on to start if enabled
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(LED_TOP_1, GPIO.OUT)
	GPIO.setup(LED_TOP_2, GPIO.OUT)
	if EnableLights:
		GPIO.output(LED_TOP_1, GPIO.LOW)
		GPIO.output(LED_TOP_2, GPIO.HIGH)
	else:
		GPIO.output(LED_TOP_1, GPIO.HIGH)
		GPIO.output(LED_TOP_2, GPIO.HIGH)

	# Turn heater on to start if enabled
	if EnableFurnace:
		heater_plug = SmartPlug(GreenhouseHeater)
		await heater_plug.turn_on()

	# Write header to CSV
	if not os.path.exists(log_file):
		log_data = ['timestamp', 'inside_temp_degC', 'outside_temp_degC', 'outside_humidity_pct']
		with open(log_file, 'a') as f_object:
			writer_object = csv.writer(f_object)
			writer_object.writerow(log_data)
			f_object.close()

async def furnace_task():
	print('Running furnace task')
	heater_plug = SmartPlug(GreenhouseHeater)
	await heater_plug.update()

	if EnableFurnace:
		if (temperature < HeaterOnTemp) and (heater_plug.is_off):
			print('Turning heater on')
			await heater_plug.turn_on()
		elif (temperature > HeaterOffTemp) and (heater_plug.is_on):
			print('Turning heater off')
			await heater_plug.turn_off()

def weather_task():
	print('Running weather task')
	response = requests.get(weather_query)
	if response.status_code == 200:
		data = response.json()
		data_main = data['main']
		outside_temp_degC = data_main['temp']
		outside_humidity_pct = data_main['humidity']
		print(f"Temperature: {outside_temp_degC}")
		print(f"Humidity: {outside_humidity_pct}")
	else:
		print('Error in weather HTTP request') 
	return outside_temp_degC, outside_humidity_pct

def temperature_task():
	print('Running temperature task')
	temperature_degC = read_temp()
	print('Temperature: ' + str(temperature_degC) + ' degC')
	#os.system('echo Temperature: ' + str(temperature_degC) + ' degC | wall')	
	return temperature_degC

def light_task():
	print('Running light task')
	if EnableLights:
		if GPIO.input(LED_TOP_1):
			GPIO.output(LED_TOP_1, GPIO.LOW)
			GPIO.output(LED_TOP_2, GPIO.HIGH)
		else:
			GPIO.output(LED_TOP_1, GPIO.HIGH)
			GPIO.output(LED_TOP_2, GPIO.LOW)
	else:
		GPIO.output(LED_TOP_1, GPIO.HIGH)
		GPIO.output(LED_TOP_2, GPIO.HIGH)

def log_task(inside_temp_degC, weather_data):
	print('Running log task')
	utc_dt = datetime.datetime.now()
	print("Local time {}".format(utc_dt.astimezone().isoformat()))
	
	log_data = [utc_dt.astimezone().isoformat(), inside_temp_degC, weather_data[0], weather_data[1]] 
	with open(log_file, 'a') as f_object:
		writer_object = csv.writer(f_object)
		writer_object.writerow(log_data)
		f_object.close()

# Main function
async def main():
	# If we just booted, sleep for a bit to allow pi to finish booting and connect to network
	if uptime.uptime() < 60: 
		print('Sleeping for 60 seconds')
		await asyncio.sleep(60)
	await init_task()

	# Main loop
	GlobalTimer_Sec = 0
	while True:
		if GlobalTimer_Sec % FurnaceTimeStep_Sec == 0:
			await furnace_task()

		if GlobalTimer_Sec % WeatherTimeStep_Sec == 0:
			weather_data = weather_task()

		if GlobalTimer_Sec % TemperatureTimeStep_Sec == 0:
			inside_temp_degC = temperature_task()

		if GlobalTimer_Sec % LightTimeStep_Sec == 0:
			light_task()

		if GlobalTimer_Sec % LogTimeStep_Sec == 0:
			log_task(inside_temp_degC, weather_data)

		await asyncio.sleep(GlobalTimeStep_Sec)	
		GlobalTimer_Sec += 1

if __name__ == "__main__":
	try:
		asyncio.run(main())
	except KeyboardInterrupt: 
		print('Shutting Down')
		GPIO.output(LED_TOP_1, GPIO.HIGH)
		GPIO.output(LED_TOP_2, GPIO.HIGH)
		GPIO.cleanup()

		try:
			sys.exit(130)
		except SystemExit:
			os._exit(130)


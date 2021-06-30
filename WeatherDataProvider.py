from datetime import datetime, timedelta
#from dateutil import parser
import pickledb
import requests
import json
import configparser
import os.path
import pytz

def loadConfig():
	config = configparser.ConfigParser()
	try:
		config.read('config.ini')
	except:
		print('config file not found.')
		exit()
	return config
	
def loadWeatherData(config):
	data = None
	with open(config['env']['filePathWeatherData']) as json_file:
		data = json.load(json_file)
	
	return data
	
def loadLatestWeatherData(config):
	lat = config['forecast.solar']['lat']
	lon = config['forecast.solar']['lon']
	dec = config['forecast.solar']['dec']
	az = config['forecast.solar']['az']
	kwp = config['forecast.solar']['kwp']
	#apiKey = config['forecast.solar']['api_key']
	
	url = 'https://api.forecast.solar/estimate/{}/{}/{}/{}/{}'.format(lat, lon, dec, az, kwp)
	apiResponse = requests.get(url)
	return dict(json.loads(apiResponse.text))

def storeWeatherData(config, data, now):
	outFilePath = config['env']['filePathWeatherData']
	out_file = open(outFilePath, "w")
	format = "%Y-%m-%d %H:%M:%S"
	data.update({'messageCreated': datetime.strftime(now, format)})
	json.dump(data, out_file, indent = 6)
	out_file.close()
	
def getExeedingHours(config, data, now):
	tzJson = pytz.timezone(data['message']['info']['timezone'])
	
	format = "%Y-%m-%d %H:%M:%S"
	currentDay = now.day
	
	exeededhours = []
	print("Hours exeeded my installed power: ")
	for date,value in data['result']['watts'].items():
		#itemDateTime = datetime.strptime(date, format).replace(tzinfo=tzJson)
		itemDateTime = datetime.strptime(date, format)
		if (itemDateTime.day <= currentDay and itemDateTime >= now and value > int(config['gen24']['rWattPeak'])):
			print(date, value)
			exeededhours.append([itemDateTime,value])
	
	return exeededhours
	
def setDbValue(db, name, value):
	valueOld = db.get(name)
	if (valueOld != value):
		db.set(name, value)
		
if __name__ == '__main__':
	config = loadConfig()
	db = pickledb.load(config['env']['filePathConfigDb'], True)
	
	#tzConfig = pytz.timezone(config['env']['timezone'])	
	dataAgeMaxInMinutes = float(config['forecast.solar']['dataAgeMaxInMinutes'])
	
	#print(f'Timezone: {tzConfig}')
	
	format = "%Y-%m-%d %H:%M:%S"	
	now = datetime.now()	
	
	data = loadWeatherData(config)
	dataIsExpired = True
	if (data):
		dateCreated = None
		if (data['messageCreated']):
			#dateCreated = datetime.strptime(data['messageCreated'], format).replace(tzinfo=tzConfig)
			dateCreated = datetime.strptime(data['messageCreated'], format)
		
		if (dateCreated):
			diff = now - dateCreated
			dataAgeInMinutes = diff.total_seconds() / 60
			print(f'[Now: {now}] [Data created:  {dateCreated}] -> age in min: {dataAgeInMinutes}')
			if (dataAgeInMinutes < dataAgeMaxInMinutes):				
				dataIsExpired = False
		
	if (dataIsExpired):
		data = loadLatestWeatherData(config)
		storeWeatherData(config, data, now)
	
	exeededhours = getExeedingHours(config, data, now)
	if (exeededhours):		
		setDbValue(db, 'ChargeStart', datetime.strftime(exeededhours[0][0], format))
		#setDbValue(db, 'ChargeEnd', datetime.strftime(exeededhours[-1][0] + timedelta(hours=1), format))
	else:
		setDbValue(db, 'ChargeStart', '')
		#setDbValue(db, 'ChargeEnd', '')
	
	print('Current time: ' + datetime.strftime(now, format) + ' chargeStart:  ' + db.get('ChargeStart') + ' for current day.')
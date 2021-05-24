import pickledb
import json
import configparser
from datetime import datetime
import pytz
import SymoGen24Connector

def loadConfig():
	config = configparser.ConfigParser()
	try:
		config.read('config.ini')
	except:
		print('config file not found.')
		exit()
	return config
	
def getWeatherData(config):
	with open(config['env']['filePathWeatherData']) as json_file:
		data = json.load(json_file)
	return data

def storeSettingsToDb(db):
	latestBatteryMaxPower = db.get('latestBatteryMaxPower')
	db.set('latestBatteryMaxPower', 'value')
	db.dump()

def analyseWeather(data):
	timezone = data['timezone']
	# sunrise = datetime.fromtimestamp(data['current'][1]['sunrise'], pytz.timezone(timezone))
    # sunset = datetime.fromtimestamp(data['current'][1]['sunset'], pytz.timezone(timezone))
    # hoursOfSunlight	= divmod(sunset - sunrise, 3600)[0]
	# hoursOfSunlightLeft = 
	
	for hour in data['hourly']:
		#weather = data['daily'][1]['weather'][0]['description']
		clouds = hour['clouds']
		dateTime = datetime.fromtimestamp(hour['dt'], pytz.timezone(timezone))
		print(f'Clouds: {clouds} at {dateTime}')
	
if __name__ == '__main__':
	config = loadConfig()
	db = pickledb.load(config['env']['filePathConfigDb'], False)
	gen24 = SymoGen24Connector.SymoGen24(config['gen24']['hostNameOrIp'], port=config['gen24']['port'])
	data = getWeatherData(config)
	#if (data):
		#analyseWeather(data)
	
	if (gen24):
	    #gen24.print_all()
	    print(gen24.read_uint16(40070))
	    print(gen24.get_mppt_power())
	

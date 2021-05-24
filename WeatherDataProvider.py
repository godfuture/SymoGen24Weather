import requests
import json
import configparser
from datetime import datetime
import pytz

def loadConfig():
	config = configparser.ConfigParser()
	try:
		config.read('config.ini')
	except:
		print('config file not found.')
		exit()
	return config

def storeWeatherData(config, data):
	outFilePath = config['env']['filePathWeatherData']

	out_file = open(outFilePath, "w")
	json.dump(data, out_file, indent = 6)
	out_file.close()
			
def getLatestWeatherData(config):
	lat = config['openweathermap']['lat']
	lon = config['openweathermap']['lon']
	apiKey = config['openweathermap']['api_key']
	
	url = 'https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&exclude=minutely,daily,alerts&units=metric&appid={}'.format(lat, lon, apiKey)
	apiResponse = requests.get(url)
	return dict(json.loads(apiResponse.text))

def getExistingWeatherData(config):
	with open(config['env']['filePathWeatherData']) as json_file:
		data = json.load(json_file)
	return data

if __name__ == '__main__':
	config = loadConfig()
	
	data = getExistingWeatherData(config)
	dataIsExpired = True
	if (data):
		dataAgeMaxInMinutes = float(config['openweathermap']['dataAgeMaxInMinutes'])
		timezone = data['timezone']
		now = datetime.now(pytz.timezone(timezone))
		dataDateTime = datetime.fromtimestamp(data['current']['dt'], pytz.timezone(timezone))
		dataAgeInMinutes = divmod((now - dataDateTime).total_seconds(), 60)[0]
		if (dataAgeInMinutes < dataAgeMaxInMinutes):
			dataIsExpired = False
		
	if (dataIsExpired):
		data = getLatestWeatherData(config)
		storeWeatherData(config, data)
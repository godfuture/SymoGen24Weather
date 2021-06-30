import pickledb
import json
import configparser
from datetime import datetime, timedelta
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

def setDbValue(db, name, value):
	valueOld = db.get(name)
	if (valueOld != value):
		db.set(name, value)
	
def storeSettingsToDb(db):
	latestBatteryMaxPower = db.get('latestBatteryMaxPower')
	db.set('latestBatteryMaxPower', 'value')
	db.dump()

if __name__ == '__main__':
	config = loadConfig()
	db = pickledb.load(config['env']['filePathConfigDb'], True)
	
	#now = datetime.now(pytz.timezone(config['env']['timezone']))
	now = datetime.now()
	format = "%Y-%m-%d %H:%M:%S"
	
	gen24 = None
	auto = False
	try:		
		chargeStart = None
		if (db.get('ChargeStart')):
			chargeStart = datetime.strptime(db.get('ChargeStart'), format)
			print(f'Current chargeStart loaded from db: {chargeStart}')
		
		newPercent = None
		chargeIsPaused = db.get('chargeIsPaused')
		print(f'Is charge currently paused (0=no,1=yes,False=NotSet)? {chargeIsPaused}')
		if (chargeStart):
			if (now < chargeStart):
				if (chargeIsPaused == 0 or not chargeIsPaused):
					newPercent = 0
			else:
				if (chargeIsPaused == 1):
					newPercent = 10000
		elif (chargeIsPaused == 1):
			newPercent = 10000
			
		if (newPercent is not None):
			gen24 = SymoGen24Connector.SymoGen24(config['gen24']['hostNameOrIp'], config['gen24']['port'], auto)
			valueOld = gen24.read_data('BatteryMaxChargePercent')			
			if (newPercent == 0):				
				valueNew = gen24.write_data('BatteryMaxChargePercent', newPercent)
				if (valueNew):
					db.set('chargeIsPaused', 1)
			elif (newPercent == 10000):
				valueNew = gen24.write_data('BatteryMaxChargePercent', newPercent)
				if (valueNew):
					db.set('chargeIsPaused', 0)
			print(f'Changed maxChargePercentage from: {valueOld} to {newPercent}.')
			dataBatteryStats = gen24.read_section('StorageDevice')
			if (dataBatteryStats):
				#gen24.print_all()
				print(f'Battery Stats: {dataBatteryStats}')
				#print(f'Sunlight Weather: {dataWeatherSunlight}')
		gen24 = SymoGen24Connector.SymoGen24(config['gen24']['hostNameOrIp'], config['gen24']['port'], auto)
		dataBatteryStats = gen24.read_section('StorageDevice')
		print(f'Battery Stats: {dataBatteryStats}')
	finally:
		if (gen24 and not auto):
			gen24.modbus.close()
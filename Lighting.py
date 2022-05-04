import pyrebase
import bluetooth # needed for bluetooth communication
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
import smtplib
from dateutil import parser

#configuring firebase
config = {
  "apiKey": "AIzaSyA_4yKZbVoLD3MorPCiTEBH3Uszujip_g",
  "authDomain": "smarthome-lighting.firebaseapp.com",
  "databaseURL": "https://smarthome-lighting-default-rtdb.firebaseio.com",
  "projectId": "smarthome-lighting",
  "storageBucket": "smarthome-lighting.appspot.com",
  "messagingSenderId": "727516464300",
  "appID" : "1:727516464300:web:193e0e0ef022bf27facb09",
  "measurementId": "G-7DJXTSZZ2Z"
};

#function to change bits
def set_bit(v, index, x):
	mask = 1 << index
	v &= ~mask
	if x:
		v |= mask
	return v

#light class
class Light:
	def __init__(self, name, schedule, photolevel, runtime, sense, state, timeout):
		self.name = name
		self.schedule = schedule
		self.photolevel = photolevel
		self.runtime = runtime 
		self.sense = sense
		self.state = state
		self.timeout = timeout
		self.start = 0

#vacation class obv
class vacation:
	def __init__(self, end, sentry, start, state):
		self.end = end
		self.sentry = sentry
		self.start = start
		self.state = state

#setting vacation to default stuff until stream handler
vacCur = vacation("",False,"", False)

#listener for vacation updates
#will set vacation attributes depending on what is received
def stream_handler(message):
	print('path={m[path]};data={m[data]}'
		.format(m=message))
	incoming = 'path={m[path]};data={m[data]}'.format(m=message)
	if (incoming[0:12] == "path=/Sentry"):
		
		vacCur.sentry = message['data']
		goOnVacation();
		
	if(incoming[0:11] == "path=/Start"):
		vacCur.start = incoming[17:]
		
	if(incoming[0:9] == "path=/End"):
		vacCur.end = incoming[15:]
		
	if(incoming[0:11] == "path=/State"):
		print(bool(incoming[17:]))
		print("New State", message['data'])
		vacCur.state = message['data']
		if vacCur.state:
			goOnVacation()

#go on vacation! the light system has your back
def goOnVacation():
	#make sure vacation state is true
	if vacCur.state == True:
		#sent initial is for the turning on lights
		sentInitial = False
		#window index is for the current light that is on
		windowIndex = 0
		print("Initalizing Vacation Mode")
		format_str = "%H:%M"
		#turning off all of the lights and turning off sense
		for i in range(0, len(LightList)):
			db.child("Lights").child(str(i+1)).update({"sense": 0})
			sendingValue = 192 + (i * 16)
			bluetoothSocket.send(str(sendingValue))
			myTime.sleep(1)
		print("Within Window")
		#the end time
		endComp = (int(vacCur.end[0:2]) * 60) + int(vacCur.end[3:5])
		#start time window
		startComp = (int(vacCur.start[0:2]) * 60) + int(vacCur.start[3:5])
		#total time of vacation
		totalTime = endComp - startComp
		tempList = LightList
		totalRuntime = 0
		#sorting list by runtime
		tempList.sort(key=lambda x: x.runtime, reverse = True)
		for _ in tempList:
			#calculating runtime
			totalRuntime += _.runtime
		
		windowStart = parser.parse(vacCur.start)
		print("Window Start:", windowStart)
		#how long the light will stay on
		windowDelta = (tempList[windowIndex].runtime / totalRuntime) * totalTime
		print(windowDelta)
		windowEnd = windowStart+ timedelta(minutes = windowDelta)
		print("Window End:", windowEnd)
		print("Initalizing Complete")
		emailSent = False
	while vacCur.state == True:
		now = datetime.now()
		myTime.sleep(5)
		#listen for state and sentry updates
		vacCur.state = db.child("Vacation").child("State").get().val()
		vacCur.sentry = db.child("Vacation").child("Sentry").get().val()
		print("Current Time" , now)
		# while we are within the vacation window
		if (now < parser.parse(vacCur.end) and now >= parser.parse(vacCur.start)):
			# motion detection
			if (vacCur.sentry == True):
				try:
					received_data = bluetoothSocket.recv(1024)
					curValue = int.from_bytes(received_data,byteorder='big')
					#check is arduino detected motion
					print("Vacation value is: %d" % curValue)
					motion = f'{curValue:03b}'[7]
					#motion detected, send email
					if (motion == "1" and emailSent == False):
						smtpUser = "icontreras2170@gmail.com"
						smtpPass = "Hope828!"
						toAdd = "ivuncontreras@gmail.com"
						fromAdd = smtpUser
						subject = 'Smart Home Lighting System'
						header = 'To: ' + toAdd + '\n' + 'From: ' + fromAdd + '\n' + 'Subject: ' + subject
						body = 'Motion Detected!'
						print(header + '\n' + body)
						s = smtplib.SMTP('smtp.gmail.com', 587)
						s.ehlo()
						s.starttls()
						s.ehlo()
						s.login(smtpUser, smtpPass)
						s.sendmail(fromAdd, toAdd, header + '\n\n' + body)
						s.quit()
						emailSent = True
						print("Email Sent")
				except KeyboardInterrupt:
					print("keyboard interrupt detected")
					break
			# if light hasnt been turned on, turn it on
			if (sentInitial == False):
				LightList[windowIndex].state = 1
				db.child("Lights").child(windowIndex+1).update({"state": 1})
				sendingValue = 192 + (windowIndex * 16) + 4
				#pass instruction to arduino to toggle lights
				print("Sending Data", sendingValue)
				bluetoothSocket.send(str(sendingValue))
				sentInitial = True;
				#time to switch lights
			if now >= windowEnd:
				#turn off current light, turn on next light
				#change window sliders
				print("Switching Lights")
				LightList[windowIndex].state = 0
				db.child("Lights").child(windowIndex+1).update({"state": 0})
				sendingValue = 192 + (windowIndex * 16)
				print("Sending Data", sendingValue)
				bluetoothSocket.send(str(sendingValue))
				if(windowIndex < len(LightList)-1):
					print("Incrementing Window Value")
					windowIndex +=1
					windowStart = windowEnd
					windowDelta = (tempList[windowIndex].runtime / totalRuntime) * totalTime
					windowEnd = windowStart+ timedelta(minutes = windowDelta)
					print("Window Start:", windowStart)
					print("Window End:", windowEnd)
					sentInitial = False
				else:
					#finished last light, turn off all lights, wait until next day
					for i in range(0,len(LightList)):
						LightList[i].state = 0
						db.child("Lights").child(i+1).update({"state": 0})
					print("Window has ended")
					break;
		else:
			print("Out of Range")
# updates light 1 based on received data from firebase in real-time
def one_handler(message):
	if (message["event"] == "put"):
		if(message["path"][0:9] == "/Schedule"):
			
			dataList: List[dict] = message["data"]
			print("Data", dataList)
			print("Path", message["path"])
			#idk what goes on below, but it works so im leaving it
			#its purpose: add to light list if new, remove if removed on app
			if (int(message["path"][10:]) >= len(LightList[0].schedule)):
				if(dataList is not None):
					LightList[0].schedule.insert(int(message["path"][10:]),int(dataList))
			else:
				if(dataList is not None):
					LightList[0].schedule.pop(int(message["path"][10:]))
					LightList[0].schedule.insert(int(message["path"][10:]),int(dataList))
				if(dataList is None):
					LightList[0].schedule.pop(int(message["path"][10:]))
						
				print(LightList[0].schedule)
				#setting timeout value, send it to arduino
		elif(message["path"][0:8] == "/timeout"):
			dataList: List[dict] = message["data"]
			sendingValue = 0
			sendingValue = set_bit(sendingValue, 6, 1)
			LightList[0].timeout = int(dataList)
			sendingValue += int(dataList)
			print("Sending timeout:", sendingValue)
			bluetoothSocket.send(str(sendingValue))
			#setting photolevel value, send it to arduino
		elif(message["path"][0:11] == "/photolevel"):
			dataList: List[dict] = message["data"]
			sendingValue = 0
			sendingValue = set_bit(sendingValue, 7, 1)
			LightList[0].photolevel = int(dataList)
			sendingValue += int(dataList)
			print("Sending photolevel:", sendingValue)
			bluetoothSocket.send(str(sendingValue))
		#print('path={m[path]};data={m[data]}'.format(m=message))
		else:
			#data from app clicking, pass to arduino
			#making instruction to pass on
			dataList: List[dict] = message["data"]
			#print("Data:", dataList)
			print("Path:", message["path"])
			print("Event:", message["event"])
			sendingValue = 0
			sendingValue = set_bit(sendingValue, 7, 1)
			sendingValue = set_bit(sendingValue, 6, 1)
		
			if (message["path"] == "/state"):
				LightList[0].state = int(dataList)
			elif (message["path"] == "/sense"):
				LightList[0].sense = int(dataList)
			else:
				print(dataList)
				#LightList[0].state = int(dataList["state"])
				#LightList[0].sense = int(dataList["sense"])
			sendingValue = set_bit(sendingValue, 2, LightList[0].state)
			sendingValue = set_bit(sendingValue, 1, LightList[0].sense)
			print("Sending:", sendingValue)	
			bluetoothSocket.send(str(sendingValue))
#same as above but for second light
def two_handler(message):
	#if not put, then from self
	if (message["event"] == "put"):
		if(message["path"][0:9] == "/Schedule"):
			
			dataList: List[dict] = message["data"]
			print("Data", dataList)
			print("Path", message["path"])
			if (int(message["path"][10:]) >= len(LightList[1].schedule)):
				if(dataList is not None):
					LightList[1].schedule.insert(int(message["path"][10:]),int(dataList))
			else:
				if(dataList is not None):
					LightList[1].schedule.pop(int(message["path"][10:]))
					LightList[1].schedule.insert(int(message["path"][10:]),int(dataList))
				if(dataList is None):
					LightList[1].schedule.pop(int(message["path"][10:]))
				print(LightList[1].schedule)		
				
		elif(message["path"][0:8] == "/timeout"):
			dataList: List[dict] = message["data"]
			sendingValue = 0
			sendingValue = set_bit(sendingValue, 6, 1)
			sendingValue = set_bit(sendingValue, 4, 1)
			LightList[1].timeout = int(dataList)
			sendingValue += int(dataList)
			print("Sending timeout:", sendingValue)
			bluetoothSocket.send(str(sendingValue))
		elif(message["path"][0:11] == "/photolevel"):
			dataList: List[dict] = message["data"]
			sendingValue = 0
			sendingValue = set_bit(sendingValue, 7, 1)
			sendingValue = set_bit(sendingValue, 4, 1)
			LightList[1].photolevel = int(dataList)
			sendingValue += int(dataList)
			print("Sending photolevel:", sendingValue)
			bluetoothSocket.send(str(sendingValue))
				
	#print('path={m[path]};data={m[data]}'.format(m=message))
		else:
			dataList: List[dict] = message["data"]
			#print("Data:", dataList)
			print("Path:", message["path"])
			print("Event:", message["event"])
			sendingValue = 0
			sendingValue = set_bit(sendingValue, 7, 1)
			sendingValue = set_bit(sendingValue, 6, 1)
			sendingValue = set_bit(sendingValue, 4, 1)
			if (message["path"] == "/state"):
				LightList[0].state = int(dataList)
			elif (message["path"] == "/sense"):
				LightList[0].sense = int(dataList)
			else:
				print(dataList)
				#LightList[0].state = int(dataList["state"])
				#LightList[0].sense = int(dataList["sense"])
			sendingValue = set_bit(sendingValue, 2, LightList[0].state)
			sendingValue = set_bit(sendingValue, 1, LightList[0].sense)
			print("Sending:", sendingValue)	
			bluetoothSocket.send(str(sendingValue))

#setting up listeners and bluetooth
print("Initializing...")
bluetooth_addr = "00:14:03:05:59:C3" # The address from the HC-06 sensor
bluetooth_port = 1 # Channel 1 for RFCOMM
bluetoothSocket = bluetooth.BluetoothSocket (bluetooth.RFCOMM)
bluetoothSocket.connect((bluetooth_addr,bluetooth_port))
firebase = pyrebase.initialize_app(config)
storage = firebase.storage()
db = firebase.database()
lights = db.child("Lights")	
myTime = time;

#passing in lights to list
index = 1;
LightList = []
for light in lights.get().each():
	name = index
	tempList = db.child("Lights").child(index).child("Schedule").get().val()
	photolevel = db.child("Lights").child(index).child("photolevel").get().val()
	runtime = db.child("Lights").child(index).child("runtime").get().val()
	sense = db.child("Lights").child(index).child("sense").get().val()
	state = db.child("Lights").child(index).child("state").get().val()
	timeout = db.child("Lights").child(index).child("timeout").get().val()
	LightList.append(Light(name, tempList, photolevel, runtime, sense, state, timeout))
	index +=1
	
LightList.pop()
#setting up vacation attributes
vacCur.end = db.child("Vacation").child("End").get().val()
vacCur.sentry = db.child("Vacation").child("Sentry").get().val()
vacCur.start = db.child("Vacation").child("Start").get().val()
vacCur.state = db.child("Vacation").child("State").get().val()

#listeners
vacation_stream = db.child("Vacation").stream(stream_handler,stream_id ="smarhome_lighting")
one_stream = db.child("Lights").child(1).stream(one_handler,stream_id ="yes")
two_stream = db.child("Lights").child(2).stream(two_handler,stream_id ="smarhome_lighting")
scheduleSent = False
time.sleep(4)
print("Intialization Complete")

while 1:
	try:
		#if not in vacation mode, then control lights
		while vacCur.state == False:
			try:
				#listen for arduino values
				received_data = bluetoothSocket.recv(1024)
				receivedValue = int.from_bytes(received_data,byteorder='big')
				curValue = str(f'{receivedValue:08b}').rjust(8, '0')
				print("Arduino value is: ", curValue)
				curIndex = int(curValue[2:4],2)
				#parse value and send to database
				print("Current index", curIndex)
				curState = curValue[5]
				#increase runtime
				if (int(curState) == 1 and LightList[curIndex].start == 0):
					LightList[curIndex].start = int(myTime.time())
				if (int(curState) == 0 and LightList[curIndex].start != 0):
					LightList[curIndex].runtime += int(myTime.time() - LightList[curIndex].start)
					print("Runtime: %d" % LightList[curIndex].runtime)
					LightList[curIndex].start = 0
					db.child("Lights").child(curIndex+1).update({"runtime": int(LightList[curIndex].runtime)})
				curSense = curValue[6]
				curMotion = curValue[7]
				#passing to DB
				if (curState != LightList[curIndex].state):
					db.child("Lights").child(curIndex+1).update({"state": int(curState)})
					LightList[curIndex].state = curState;
				if (curSense != LightList[curIndex].sense):
					db.child("Lights").child(curIndex+1).update({"sense": int(curSense)})
					LightList[curIndex].sense = sense;
				now = datetime.now()
				format_str = "%H:%M"
				#get time of day for scheduled time
				current_time = now.strftime(format_str)
				dayOfWeek = datetime.today().isoweekday()
				print("Current Time", current_time)
				#check each schedule time for each light
				for i in range(0,len(LightList)):
					print("check")
					for time in LightList[i].schedule:
						formattedTime = str(time)[1:3] + ":" + str(time)[3:5]
						if(str(time)[0] == str(dayOfWeek) and formattedTime == current_time):
							print("Theres a match!")
							#times match up, toggle light to on or off
							#sending value to arduino to turn on light
							sendingValue = 0
							sendingValue = set_bit(sendingValue, 7, 1)
							sendingValue = set_bit(sendingValue, 6, 1)
							if(i==1):
								sendingValue = set_bit(sendingValue, 4, 1)
							if(i==2):
								sendingValue = set_bit(sendingValue, 5, 1)
							if(i==3):
								sendingValue = set_bit(sendingValue, 5, 1)
								sendingValue = set_bit(sendingValue, 5, 1)	
							sendingValue = set_bit(sendingValue, 2, int(str(time)[5]))
							db.child("Lights").child(i+1).update({"state": int(str(time)[5])})
							if scheduleSent == False:
								print("Scheduler Value", sendingValue)
								bluetoothSocket.send(str(sendingValue))
								scheduleSent = True
						else:
							scheduleSent = False
			except KeyboardInterrupt:
				print("keyboard interrupt detected")
				exit(0)
				break
				
	except KeyboardInterrupt:
			print("keyboard interrupt detected")
			exit(0)
			break
	
			
bluetoothSocket.close()

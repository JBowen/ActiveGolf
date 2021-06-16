from typing import Union, List
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from datetime import datetime
import configparser
import time
import requests
import json


		
class ActiveGolf:
	def __init__(self):
		configParser = configparser.RawConfigParser()  
		configParser.read(r'.\config.txt')
		
		self.base_url = "https://direct.activegolf.com/"
		self.base_url_s = "http://direct.activegolf.com/"
		self.session = requests.Session()
		self.courseSelected = False
		self.QLockCode = ""
		self.converted_date = ""
		self.coursesTable = {"1006": "BraeBen Golf Course", "1009": "BraeBen Par3 Academy - 9 holes only", "1010": "Lakeview Golf Course"}
		self.bookedTeeTime = False
		self.course = ""
		self.selectedTime = ""
		
		for configs in configParser.sections():
			for (each_key, each_val) in configParser.items(configs):
				if each_key == "date": self.date = each_val
				if each_key == "time": self.time = each_val   # ex: 09:00 AM
				if each_key == "holes": self.holes = each_val
				if each_key == "players": self.players = each_val
				if each_key == "username": self.username = each_val
				if each_key == "password": self.password = each_val
				if each_key == "preferred courses": self.courses = each_val.split(',')   # options: 'BraeBen', 'BraeBen Academy', 'Lakeview'
				if each_key == "first name": self.firstname = each_val
				if each_key == "last name": self.lastname = each_val
				if each_key == "address 1": self.address1 = each_val
				if each_key == "address 2": self.address2 = each_val
				if each_key == "city": self.city = each_val
				if each_key == "state": self.state = each_val
				if each_key == "zip": self.zip = each_val
				if each_key == "email": self.email = each_val
				if each_key == "home phone": self.homephone = each_val
				if each_key == "mobile phone": self.mobilephone = each_val
				if each_key == "work phone": self.workphone = each_val
				

		for course in self.courses:
			if course == "1009": self.holes = 0    # if they're playing BraeBen Par3 Academy, this *has* to be 9 holes 


		
	def formatHTML(self, res):
		soup = BeautifulSoup(res.content, "lxml")
		return soup
		
		
	def setHomePage(self) -> Union[requests.Response, None]:
		self.session.get(url=self.base_url+"home.asp", params={"WSID": "94"})
		return self.session.get(url=self.base_url+"default.asp")
		
	def goToLogin(self) -> Union[requests.Response, None]:
		
		return self.session.get(url=self.base_url+"crs/GetTeeTime.asp")
		
	def login(self) -> Union[requests.Response, None]:
		data = {
			"frmName": "Login",
			"MemberAccessNum": self.username,
			"MemberPIN": self.password,
			"LoginAttempts": 0
		}
		self.session.post(url=self.base_url+"crs/GetTeeTime.asp", data=data)
		return self.session.get(url=self.base_url+"crs/SearchTeeTime.asp")

	def searchTeeTime(self):
		return self.session.get(url=self.base_url+"crs/SearchTeeTime.asp")

	def listTeeTime(self, course):
		date_object = datetime.strptime(self.date, '%m/%d/%Y')
		self.converted_date = date_object.strftime("%b %d, %Y")
		start_time = self.time.split(":")
		start_time_loop = int(start_time[0])
		second_start_time_loop = int(start_time[1])
		start_time_ampm = "am"
		while start_time_loop <= 19:
			#time.sleep(5)
			if start_time_loop > 11:
				start_time_ampm = "pm"
			data = {
				"QTRSFacilityID": course,    # this is the course location
				"QDate": self.converted_date, 
				"QDateHidden": self.date,
				"QTimeHr": start_time_loop,
				"QTimeMin": second_start_time_loop,
				"QTimeAmPm":  start_time_ampm,
				"QHoles": self.holes,       # one refers to 18 holes
				"QGolfers": self.players,
				"frmName": "Search",
				"YourCartCheck": "",
				"GuestCartCheck": ""
			}
			res = self.session.post(url=self.base_url+"crs/ListTeeTime.asp", data=data)
			errMsg = self.formatHTML(res)
			if errMsg.find("input", {"name": "errMsg"}):
				#print("No Tee Time Available for: " + self.date + " at " + str(start_time_loop) + ":" + str(second_start_time_loop).zfill(2))
				#print(str(start_time_loop) + ":" + str(second_start_time_loop))
				if second_start_time_loop == 55:
					start_time_loop = start_time_loop + 1
					second_start_time_loop = 0
				else:
					second_start_time_loop = second_start_time_loop + 5
			else:
				self.selectedTime = str(start_time_loop) + ":" + str(second_start_time_loop).zfill(2) + " " + start_time_ampm
				if self.courses[0] == "1009":
					data["currentCourseID"] = "4"
				else:
					data["currentCourseID"] = "2"
				data["currentDate"] = "1"
				data["currentTime"] = "1"
				data["frmName"] = "Show"

				res = self.formatHTML(self.session.post(url=self.base_url+"crs/showTeeTime.asp", data=data))
				self.QLockCode = res.find('input', {"name": "QLockCode"})['value']
				print("Attempting to book Tee Time for " + self.date + " at " + str(start_time_loop) + ":" + str(second_start_time_loop).zfill(2) + " " + start_time_ampm)
				
				print("Booking is for: " + res.find("td", {"class": "fieldLabel"}).text)
				return True
			
		
	def reserveTeeTime(self):
		data_httpRequest2 = {
			"MemberFirstName": self.firstname,
			"MemberLastName": self.lastname,
			"MemberPassword": ("*" * len(self.password)),
			"ConfirmMemberPassword": ("*" * len(self.password)),
			"MemberAddress1": self.address1,
			"MemberAddress2": self.address2,
			"MemberCity": self.city,
			"MemberState": self.state,
			"MemberZip": self.zip,
			"MemberHomePhone": self.homephone,
			"MemberDayPhone": self.workphone,
			"MemberMobilePhone": self.mobilephone,
			"MemberEmail": self.email,
			"ConfirmMemberEmail": self.email,
			"MemberCCNumber": "",
			"MemberCCExpMonth": "1",
			"MemberCCExpYear": "1900",
			"MemberRrNumber": "",
			"MemberPoBox": "",
			"MemberStation": "",
			"MemberStreetNumber": "",
			"MemberAddressSuffix": "",
			"MemberSuiteNumber": "",
			"MemberPreStreetDir": "",
			"MemberPreStreetDirHidden": "",
			"MemberStreetName": "",
			"MemberStreetType": "",
			"MemberStreetTypeHidden": "",
			"MemberPostStreetDir": "",
			"MemberPostStreetDirHidden": "",
			"chkConfirmEmail": "1",
			"chkRemindEmail": "0"
		}
		res = self.session.post(url=self.base_url+"crs/httpRequest.asp", params={"requestType": "2"}, data=data_httpRequest2)
		data_reserveTeeTime = {
			"QLockCode": self.QLockCode,
			"QTRSFacilityID": self.course,
			"date": self.date,
			"hour": self.selectedTime.split(":")[0],
			"minute": ''.join('' if var in 'APM' else var for var in self.selectedTime.split(":")[1]).strip(),
			"pmam": "am" if int(self.selectedTime.split(":")[0]) <= 11 else "pm",
			"QGolfers": self.players,
			"QHoles": self.holes,
			"QGolfersRes": "1",
			"captainPrePayment": "0",
			"guestPrePayment": "0",
			"YourCartCheck": "0",
			"GuestCartCheck": "0",
			"QCartOption": "3",
			"merchantId": "",
			"ccNumber": "",
			"ccExpiryMonth": "1",
			"ccExpiryYear": "1900",
			"ccType": "0",
			"ccHolder": "",
			"ccToken": "",
			"ccTokenExpires": ""
		}
		
		res = self.session.post(url=self.base_url+"crs/reserveTeeTime.asp",  data=data_reserveTeeTime)
		res = self.session.post(url=self.base_url+"crs/httpRequest.asp", params={"requestType": "10"}, data={"text": "null"})
		print(self.formatHTML(res))
		"""
		data_saveTeeTime = {
			"QTRSFacilityID": "1006",
			"date": "Jun 18, 2021",
			"hour": "15",
			"minute": "0",
			"pmam": "pm",
			"QGolfers": "2",
			"QHoles": "1",
			"QGolfersRes": "1",
			"QLockCode": "2490405-3494753",
			"frmName": "Confirm",
			"YourCartOption": "0",
			"GuestCartOption": "0",
			"ccNumber": "",
			"sTable": "",
			"hidCCType": "0"
		}
		
		#return self.session.post(url=self.base_url+"crs/saveTeeTime.asp", data=data_saveTeeTime)
		"""

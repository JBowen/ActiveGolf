import requests
import urllib
import re
from ActiveGolf import ActiveGolf


golfSession = ActiveGolf()



golfSession.setHomePage()
golfSession.goToLogin() 
golfSession.login()
golfSession.searchTeeTime()
for course in golfSession.courses:
	if golfSession.listTeeTime(course): 
		golfSession.course = course
		golfSession.reserveTeeTime()


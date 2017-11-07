import argparse
import requests
import datetime
import sys
import time
import math
import ephem
import json
from twilio.rest import TwilioRestClient
import pygame
import RPi.GPIO as GPIO


# login data info

loginData = { 'identity' : 'ayarrab3@gmail.com',
              'password' : 'team17NETWORKAPPS' }
googleAPIkey_elevation = 'AIzaSyDcehBBYBrtHGlGdJ8zTj0JaXj2kqo78Jo'
googleAPIkey_geocoding = 'AIzaSyB8WgEbB-mOGI1bcq2AficBiLjMJJFMLJs'
d1 = datetime.datetime.now() + datetime.timedelta(days=14)
dstr = datetime.datetime.now().strftime("%Y-%m-%d")
d1str = d1.strftime("%Y-%m-%d")
lastDay = d1

# gets the coordinates based on the zipcode
def getCoordinates(zipcode):
    resp = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address='+zipcode+'&key='+googleAPIkey_geocoding)
    if(resp.status_code != 200):
        print("Response went wrong")
        return str(resp.status_code)
    latitude = resp.json()['results'][0]['geometry']['location']['lat']
    longitude = resp.json()['results'][0]['geometry']['location']['lng']
    return (str(latitude),str(longitude))

# turn the led on
def LED():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(29,GPIO.OUT)  #RED
    GPIO.setup(31,GPIO.OUT)	#GREEN
    GPIO.setup(33,GPIO.OUT)	#BLUE
    GPIO.setwarnings(False)

    GPIO.output(29, True)
    GPIO.output(31, True)
    GPIO.output(33, False)
    time.sleep(1)
    GPIO.output(29, False)
    GPIO.output(31, False)
    GPIO.output(33, False)
    time.sleep(1)
    GPIO.output(29, True)
    GPIO.output(31, True)
    GPIO.output(33, False)
    time.sleep(1)
    GPIO.output(29, False)
    GPIO.output(31, False)
    GPIO.output(33, False)
    time.sleep(1)
    GPIO.output(29, True)
    GPIO.output(31, True)
    GPIO.output(33, False)
    time.sleep(1)
    GPIO.output(29, False)
    GPIO.output(31, False)
    GPIO.output(33, False)
    time.sleep(1)
    GPIO.output(29, True)
    GPIO.output(31, True)
    GPIO.output(33, False)
    time.sleep(1)
    GPIO.output(29, False)
    GPIO.output(31, False)
    GPIO.output(33, False)
    time.sleep(1)
    GPIO.output(29, True)
    GPIO.output(31, True)
    GPIO.output(33, False)
    time.sleep(1)
    GPIO.output(29, False)
    GPIO.output(31, False)
    GPIO.output(33, False)
        

# gets the elevation based on lat and long
def getElevation(latitude, longitude):
    LED()
    resp = requests.get('https://maps.googleapis.com/maps/api/elevation/json?locations='+latitude+','+longitude+
                         '&key='+googleAPIkey_elevation)
    if(resp.status_code != 200):
        print("Response went wrong")
        return str(resp.status_code)
    return(resp.json()['results'][0]['elevation'])


# gets TLE data based on satellite id    
def getTLE(satID):
    resp1 = requests.post('https://www.space-track.org/ajaxauth/login', json=loginData)
    
    if(resp1.status_code != 200):
        print("Login failed")
        return str(resp1.status_code)

    resp = requests.get('https://www.space-track.org/basicspacedata/query/class/tle_latest/ORDINAL/1/NORAD_CAT_ID/'
                        +satID+"/predicates/TLE_LINE0,TLE_LINE1,TLE_LINE2", cookies=resp1.cookies)
    
    if(resp.status_code != 200):
        print("Response went wrong")
        return str(resp.status_code)
    
    return (resp.json())


# helper function converts time to datetime object
def datetime_from_time(tr):
    year, month, day, hour, minute, second = tr.tuple()
    dt = datetime.datetime(year, month, day, hour, minute, int(second))
    return dt

# gets weather data based on the zipcode
def getNOAA(zipcode):
    zipVal = str(zipcode)
    APIVal = "1eb667941c31e677adf539ed22c7adcd"

    NOAA = 'http://api.openweathermap.org/data/2.5/forecast/daily?zip='+zipVal+'&cnt=15&APPID='+APIVal

    NOAAresp = requests.get(NOAA)
    result = NOAAresp.json()
    day = 0
    cal = {}

    if(NOAAresp.status_code != 200):
        print("Login failed")
        return str(NOAAresp.status_code)

    global lastDay

    for i in result['list']:
        x = datetime.datetime.fromtimestamp(int(i['dt'])).strftime("%m-%d-%Y")
        lastDay = datetime.datetime.fromtimestamp(int(i['dt']))
        cal [(x)] = i['weather'][0]['description']
        print (x, i['weather'][0]['description'])
        day = day+1;
    return cal


# gets passes based on TLE, lat, long, elevation, weather
def getPasses(TLE, latitude, longitude, elevation, weather):
    print ("------------TLE DATA------------------------")
    print(TLE[0]['TLE_LINE0'])
    print(TLE[0]['TLE_LINE1'])
    print(TLE[0]['TLE_LINE2'])
    fivepasses = []

    iss = ephem.readtle(TLE[0]['TLE_LINE0'], TLE[0]['TLE_LINE1'], TLE[0]['TLE_LINE2'])

    obs = ephem.Observer()
    obs.lat = latitude
    obs.long = longitude
    obs.elevation = elevation
    obs.pressure = 0
    obs.horizon = '-0:34'

    now = datetime.datetime.now()
    obs.date = now

    tr, azr, tt, altt, ts, azs = obs.next_pass(iss)


    rise_time = datetime_from_time(tr)
    rise_time_date = rise_time.strftime("%m-%d-%Y")
    currentTime = datetime.datetime.now().strftime("%m-%d-%Y")
   
    # gets 5 observable events 
    while ((ephem.localtime(tr) < lastDay ) and len(fivepasses) < 5) :
   
            duration = abs(int((ts - tr) *60*60*24))
            rise_time = datetime_from_time(tr)
            max_time = datetime_from_time(tt)
            set_time = datetime_from_time(ts)

            obs.date = max_time

            sun = ephem.Sun()
            sun.compute(obs)
            iss.compute(obs)

            sun_alt = math.degrees(sun.alt)
            visible = False
            if (iss.eclipsed is False and -18 < sun_alt < -6):
                visible = True

            max_time_date = max_time.strftime("%m-%d-%Y")

            if ( ( ('clear' in weather[max_time_date]) | (weather[max_time_date] == 'mostly clear') ) & visible ):
                fivepasses.append((max_time, duration, azs, iss.sublat, iss.sublong))
                      
            obs.date = tr + ephem.minute
            tr, azr, tt, altt, ts, azs = obs.next_pass(iss)

    return fivepasses


# returns the visible passes
def getVisiblePasses(satID, latitude, longitude, elevation, weather):

    TLE = getTLE(satID)
    passes = getPasses(TLE, latitude, longitude, elevation, weather)
    print ("-------------VIEWABLE EVENTS----------------------")
    if(len(passes) < 5):
        print('Could not find five viewable passes in the next 15 days')
    for x in range(len(passes)):
        print("*Pass time: "+ str(passes[x][0]) + " Duration: "+ str(passes[x][1]))
        print("Direction: %.3f" % math.degrees(passes[x][2]) + " Location: ( %.3f" % math.degrees(passes[x][3]) +", %.3f" % math.degrees(passes[x][4])+")")
    return passes


# sends sms data
def sendSMS(msg):
    account_sid = "AC0d11dcf9eeea54fc1a42de65006d44e3"
    auth_token = "f360c891f7d9fc2f783bc98c65819cba"
    client = TwilioRestClient(account_sid, auth_token)

    message = client.messages.create(to="+18048366909", from_="+12604680505",
                                             body=msg)
    return

# plays sound on RPI
def playSound():
    pygame.mixer.init()
    pygame.mixer.music.load("bird.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy() == True:
        continue
    return


# check time
def checkTime(time):
    now = datetime.datetime.now()
    d15 = time - datetime.timedelta(minutes = 15);
    if(now > d15):
        return True
    else:
        return False
    
def main():
 
    parser = argparse.ArgumentParser()

    # parses command line arguments
    parser.add_argument('-z', required=True, dest="zipcode")
    parser.add_argument('-s', required=True, dest="satID")

    arguments = parser.parse_args()

    # gets the weather conditions
    print ("----------Weather Forecast for next 15 days----------------")

    weatherCond = getNOAA(arguments.zipcode)

    (latitude,longitude) = getCoordinates(arguments.zipcode)
    print("Latitude: " + latitude + "    Longitude: " + longitude)
    
    elevation = getElevation(latitude, longitude)
    
    passes = getVisiblePasses(arguments.satID, latitude, longitude, elevation, weatherCond)
  
    # checks for observable events and sends sms and plays sound        
    while(1):
        for x in range(len(passes)):
            if(checkTime(passes[x][0])):
                print("Alert: Pass is viewable: " +str(passes[x][0]))
                sendSMS("Pass is viewable at "+ str(passes[x][0]) )
                LED()
                playSound()
                break
                

if __name__ == "__main__":
    main()

#!/usr/bin/env python
#change concrete plant step motors speed through subscribing mqtt topic "motor_geer"
#diplay motor speed on OLED 128*64
#By Haotian Wang @Dec,2014

import time
import mosquitto
import json
import os
import RPi.GPIO as GPIO
import threading
import Adafruit_SSD1306
from PIL import Image
import ImageDraw
import ImageFont
import random
import traceback


#GPIO intitialization
GPIO.setmode (GPIO.BCM)
A_coil_A_1_pin = 17
A_coil_A_2_pin = 18
A_coil_B_1_pin = 22
A_coil_B_2_pin = 23
GPIO.setup(A_coil_A_1_pin,GPIO.OUT)
GPIO.setup(A_coil_A_2_pin,GPIO.OUT)
GPIO.setup(A_coil_B_1_pin,GPIO.OUT)
GPIO.setup(A_coil_B_2_pin,GPIO.OUT)
Mixer_motor_pin = 26
Conveyor_motor_pin1 = 20
Conveyor_motor_pin2 = 21
GPIO.setup(Mixer_motor_pin,GPIO.OUT)
GPIO.setup(Conveyor_motor_pin1,GPIO.OUT)
GPIO.setup(Conveyor_motor_pin2,GPIO.OUT)
Mixer_motor_pwm = GPIO.PWM(Mixer_motor_pin,1000)
Conveyor_motor_pwm1 = GPIO.PWM(Conveyor_motor_pin1,1000)
Conveyor_motor_pwm2 = GPIO.PWM(Conveyor_motor_pin2,1000)
Mixer_motor_pwm.start(100) #mixer motor init speed
Conveyor_motor_pwm1.start(100) #mixer motor init speed
Conveyor_motor_pwm2.start(100) #mixer motor init speed

LED_1 = 5
LED_2 = 6
LED_3 = 12
GPIO.setup(LED_1,GPIO.OUT)
GPIO.setup(LED_2,GPIO.OUT)
GPIO.setup(LED_3,GPIO.OUT)

RST = 24
#i2c display init
try:
    disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
    disp.begin()
    disp.clear()
    disp.display()
except:
    f = open('./error.log','a')
    f.write('=====================['+time.ctime()+']===================\n')
    traceback.print_exc(file=f)
    f.flush()
    f.close()

#font setup
font = ImageFont.load_default()
font1 = ImageFont.truetype("FreeSans.ttf",18)
font2 = ImageFont.truetype("FreeSans.ttf",14)
font3 = ImageFont.truetype("FreeSans.ttf",12)

def frange(start,stop,step):
    return [start+float(i)*(stop-start)/(float(step)-1) for i in range(step)]

def led_off(pin):
    GPIO.output(pin,True)

def led_on(pin):
    GPIO.output(pin,False)

def setStep(w1,w2,w3,w4):
    GPIO.output(A_coil_A_1_pin,w1)
    GPIO.output(A_coil_A_2_pin,w2)
    GPIO.output(A_coil_B_1_pin,w3)
    GPIO.output(A_coil_B_2_pin,w4)

#callback function for mqtt
def on_message(mosq, userdata, msg):
    global delay,alert,adj_delay,adj_button,Mixer_motor_pwm
    try:
        json_data = json.loads(str(msg.payload))
        print "json_data: "+str(json_data)+"id:"+json_data['id']
        if json_data['id'] == 'control':
            delay = json_data['value']
            Mixer_motor_pwm.ChangeDutyCycle(70+10*(0.01-delay)/0.002)
            Conveyor_motor_pwm1.ChangeDutyCycle(88+4*(0.01-delay)/0.002)
            Conveyor_motor_pwm2.ChangeDutyCycle(88+4*(0.01-delay)/0.002)
            print 'Now! Delay is '+str(delay)
        elif json_data['id'] == 'pumpAlert':
            alert = 1
            adj_delay = 0.01#the low geer ///json_data['value']
            print 'Oh yeah alert!'
        elif json_data['id'] == 'adjusting':
            if alert == 1:
                adj_button = 1
            else:
                pass
    except:
        f = open('./error.log','a')
        f.write('=====================['+time.ctime()+']===================\n')
        traceback.print_exc(file=f)
        traceback.print_exc()
        f.flush()
        f.close()

#mqtt initializaiton
mqtt_client = mosquitto.Mosquitto('plant')
mqtt_client.on_message = on_message
mqtt_client.connect('127.0.0.1')
mqtt_client.subscribe('pumpAlert')

#motor run thread
def motor_run():
    global delay,loop
    while loop:
        setStep(1,0,1,0)
        time.sleep(delay)
        setStep(0,1,1,0)
        time.sleep(delay)
        setStep(0,1,0,1)
        time.sleep(delay)
        setStep(1,0,0,1)
        time.sleep(delay)

global delay,loop,alert,adj_delay,adj_button
delay = 0.004
loop = 1
alert = 0
adj_delay = 1
adj_button = 0
conveyor_speed = 0
mixer_speed = 0
def oled_display():
    global delay,loop,alert,adj_delay,adj_button,mqtt_client,conveyor_speed,mixer_speed
    while loop:
        if alert == 1:
            led_off(LED_1)
            led_off(LED_2)
            led_on(LED_3)
            try:
                image = Image.open('alert.ppm').convert('1')
                draw = ImageDraw.Draw(image)
                disp.image(image)
                disp.display()
            except:
                f = open('./error.log','a')
                f.write('=====================['+time.ctime()+']===================\n')
                traceback.print_exc(file=f)
                traceback.print_exc()
                print 'Hi!Check the OLED display!'
                f.flush()
                f.close()

            if adj_button == 1:
                print 'addddddjusting!'
                try:
                    image = Image.open('adjusting.ppm').convert('1')
                    draw = ImageDraw.Draw(image)
                    disp.image(image)
                    disp.display()
                    #time.sleep(3)
                except:
                    f = open('./error.log','a')
                    f.write('=====================['+time.ctime()+']===================\n')
                    traceback.print_exc(file=f)
                    traceback.print_exc()
                    print 'Hi!Check the OLED display!'
                    f.flush()
                    f.close()
                for i in frange(0.004,0.01,10):
                    delay = i
                    time.sleep(1)
                delay = adj_delay
                Mixer_motor_pwm.ChangeDutyCycle(70+10*(0.01-delay)/0.002)
                Conveyor_motor_pwm1.ChangeDutyCycle(88+4*(0.01-delay)/0.002)
                Conveyor_motor_pwm2.ChangeDutyCycle(88+4*(0.01-delay)/0.002)
                alert = 0
                adj_button = 0
        else:
            led_off(LED_1)
            led_off(LED_3)
            led_on(LED_2)
            image = Image.open('bk.ppm').convert('1')
            draw = ImageDraw.Draw(image)
            draw.text((0,20), 'Conveyor', font=font2, fill=255)
            draw.text((80,20), 'Mixer', font=font2, fill=255)
            #conveyor_speed = (1.0/delay+random.uniform(-5,5))
            #mixer_speed = (1.0/delay+random.uniform(-5,5))
            draw.text((0,40), '%.2f'% conveyor_speed,font=font1, fill=255)
            draw.text((70,40), '%.2f'% mixer_speed, font=font1, fill=255)
            #mqtt_client.publish("conveyor",'{"id":"conveyorSpeed","value":"'+str(conveyor_speed)+'"}')
            #mqtt_client.publish("mixer",'{"id":"mixerSpeed","value":"'+str(mixer_speed)+'"}')
            #print "published!!"
            try:
                disp.image(image)
                disp.display()
            except:
                print 'check your oled connection!!'
            time.sleep(1)

def mqtt_publish():
    global delay,mqtt_client,loop,conveyor_speed,mixer_speed
    while loop:
        conveyor_speed = (1.0/delay+random.uniform(-5,5))
        mixer_speed = (1.0/delay+random.uniform(-5,5))
        mqtt_client.publish("conveyor",'{"id":"conveyorSpeed","value":"'+str(conveyor_speed)+'"}')
        mqtt_client.publish("mixer",'{"id":"mixerSpeed","value":"'+str(mixer_speed)+'"}')
        print "published"
        #conveyor_speed = (1.0/delay+random.uniform(-5,5))
        #mixer_speed = (1.0/delay+random.uniform(-5,5))
        time.sleep(1)
#start motor_run thread
t = threading.Thread(target=motor_run)
t.start()
t1 = threading.Thread(target=oled_display)
t1.start()
t2 = threading.Thread(target=mqtt_publish)
t2.start()
while loop :
    try:
        ret = mqtt_client.loop()
        if ret == 0:
            print 'mqtt listening!'
        else:
            mqtt_client.unsubscribe('pumpAlert')#motor_geer
            mqtt_client.disconnect()
            mqtt_client.connect('127.0.0.1')
            mqtt_client.subscribe('pumpAlert')
    except KeyboardInterrupt:
        print 'BYE!'
        loop = 0

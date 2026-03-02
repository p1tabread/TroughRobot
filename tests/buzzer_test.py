import RPi.GPIO as GPIO
import time

BUZZER_PIN = 13

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

pwm = GPIO.PWM(BUZZER_PIN, 1000)
pwm.start(50)
time.sleep(2)
pwm.ChangeDutyCycle(0)
pwm.stop()
GPIO.cleanup()
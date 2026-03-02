import serial
import time

ser = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=5)
time.sleep(5)  # Wait for connection to establish

print("Sending 'dfu'...")
ser.write(b'dfu')

print("Waiting for response...")
response = ser.read_until(b'\n', size=1024)
if response:
    print(f"Response: {response.decode('utf-8', errors='replace').strip()}")
else:
    print("No response received (timeout)")

ser.close()
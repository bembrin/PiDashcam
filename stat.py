import time
import psutil

while True:
    mem = psutil.virtual_memory()
    stor = psutil.disk_usage('.')
    cpu = psutil.cpu_percent(interval=1)
    temp = str(psutil.sensors_temperatures()['cpu_thermal'][0].current)

    print('memory: {}   CPU: {}     Storage Space: {}   temp: {}'.format(100 * mem.available/mem.total,cpu,stor.percent,temp))

    time.sleep(5)

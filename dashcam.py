import picamera as pc
import psutil
# import _strptime
import datetime
import os
import time
import serial
import pynmea2
from gpiozero import Button
from configparser import ConfigParser
from picamera import Color
#from file_sweeper import file_sweeper as clean

# class tic():
#     '''
#     Used in debugging to see how long a process takes
#     '''
#     def init(self):
#         self._times = []
# 
#     def tic(self):
#         ''' Initiate timer'''
#         self._times.append(time.time()) 
#     def toc(self):
#         ''' reveal time elapsed '''
#         print('Time elapsed: {}'.format(time.time() - self._times.pop(0)))

def space_check(min_space):
    '''check to make sure there is enough space in the filesystem'''
    return psutil.disk_usage('.').percent < min_space

def mem_check(minimum):
    '''Check to make sure there is enough available system memory'''
    mem = psutil.virtual_memory()
    percent = 100 * mem.available / mem.total
    return percent >= minimum
	
def file_sweeper(path=None, max_space=None):
    '''Remove the oldest video in the vids folder'''
    os.chdir(path)
    while not space_check(max_space):
        f = sorted(os.listdir(path))
        print('Removing: ' + f[0])
        os.remove(f[0])

def get_gps(port):
    '''
    This function reads a nmea string from port and parses gps data
    Returns False if the incorect nmea sentence was read
    Returns a nmea object if the correct sentence was read
    '''
    
    while True:
        try:
            msg = nmea2.parse(port.readline())
            if msg.sentence_type == 'RMC':
                return msg
        except:
            pass

def shutdown(stream, cam, **args):
    '''
    safe shutdown of pi
    ~Save stream loop
    ~Shutdown pi
    '''
    # msg = get_gps(port)
    # date_time = dict(date=msg.date, time=msg.time)
    stream.copy_to(format_filename(**args))
    # stop the camera
    print('Stopping recording...')
    cam.stop_recording()
    print('Stopping system. Goodby...')
    os.system('sudo shutdown -P now')

def highlight(stream, **args):
    '''
    Save current loop to perminant folder
    '''
    print('Hilighting current loop...')
    pwd = os.getcwd()
    parent = os.path.dirname(pwd)
    save_path = os.path.join(parent,'permanent',format_filename(**args))
    stream.copy_to(save_path)

def format_filename(date=None, time=None, fmrt='%Y-%m-%d%H:%M:%S', **args):
    '''
    Takes a date and time string and parses them into a datetime object with a format string
    then builds a file name from the datetime object
    '''
    now = datetime.datetime.strptime('{}{}'.format(date,time), fmrt)
    filename = now.strftime("%y%m%d%H%M_%d%b%y-%H%M") + '.h264'
    return filename


# ================== MAIN FUNCTION =======================================

def main(height=None, width=None, frames=None, clip_dur=None, min_space=None, vid_dir=None,
         shutdown_pin=None, highlight_pin=None, speed_conversion=1):
    # ensure device perameters type
    res = (int(width), int(height))  # resolution of the video recording 
    frames = int(frames)   # framerate of the video recording
    clip_dur = int(clip_dur)    # duration of individual clips
    min_space = int(min_space)  # the maximum percentage of used storage allowed
    convert = float(speed_conversion)     # Speed conversion factor
    # vid_dir = '/home/pi/dashcam/vids'  # Directory where clips are stored
   

    # initialize the serial port
    port = serial.Serial('/dev/serial0')

    # initialize shutdown button
    shutdown_btn = Button(shutdown_pin, hold_time=3)

    # initialize highlight button
    highlight_button = Button(highlight_pin)

    # Initialize the overaly text
    overlay = {
            'lat' : 'xxx',
            'lat_dir' : 'x',
            'lon' : 'xxx',
            'lon_dir' : 'x',
            'speed' : 'x',
            'trk' : 'x',
            'date' : 'xxxxxx',
            'time' : 'xxxxxx.xx'
            }

    # change to the videos directory
    os.chdir(vid_dir)
   
    # initialize the camera object
    cam = pc.PiCamera(
            resolution = res,
            framerate = frames
            )
    # initualize the video stream
    stream = pc.PiCameraCircularIO(cam, seconds=clip_dur)
    # start recording
    cam.start_recording(stream, format='h264')
    print('Recording...')

    # main while loop
    while True:
        # check the file system and remove oldest video if not enough storage
        file_sweeper(path=os.getcwd(),
              max_space=min_space
              )

        # wait while recording
        # cam.wait_recording(clip_dur - 30)
        timeout = time.time() + clip_dur - 30
        while time.time() < timeout:
            
            msg = get_gps(port)

            if msg:
                overlay['lat'] = msg.lat,
                overlay['lat_dir'] = msg.lat_dir,
                overlay['lon'] = msg.lon, 
                overlay['lon_dir'] = msg.lon_dir,
                overlay['speed'] = msg.spd_over_grnd * convert
                overlay['trk'] = msg.true_course
                overlay['date'] = msg.datestamp #!!! need to format these (probably with datetime)
                overlay['time'] = msg.timestamp
                msg = False
            
            cam.annotate_background = Color('black')
            cam.annotate_text = '{date} {time} | Position: {lat} {lat_dir} -- {lon} {lon_dir} | Speed: {speed} kph | Trk: {trk}'.format(
                    **overlay
                    )

            # Check shutdown button press
            if shutdown_btn.is_held:
                shutdown(stream, cam, **overlay)

            # Check highlight button press
            if False:
                highlight(stream, **overlay)

        # save the current video
        filename = format_filename(**overlay)
        stream.copy_to(filename)
        print('recording saved to ' + filename )
    
    #stop the camera
    print('Stopping recording...')
    cam.stop_recording()
    exit()


if __name__ == "__main__":
    config = ConfigParser()
    config.read('config.ini')
    settings = config['SETTINGS']

    main(**settings)



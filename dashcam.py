import picamera as pc
import psutil
import datetime
import os
import time
from serial import Serial
import pynmea2
from threading import Thread
from queue import Queue
from gpiozero import Button
from configparser import ConfigParser
from picamera import Color

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

def get_gps(port, queue):
    '''
    This function reads a nmea string from port and parses gps data
    '''
    while True:
       
        try:
            msg = pynmea2.parse(port.readline())
            if msg.sentence_type == 'RMC':
                queue.put(msg)
        except:
            pass

def shutdown(cam, vid_file):
    '''
    safe shutdown of pi
    ~Save stream loop
    ~Shutdown pi
    '''
    # Save current stream to file
    # filename = format_filename(**args)
    # print('Saving file to {}...'.format(filename))
    # stream.copy_to(filename)
    
    # stop the camera
    print('Stopping recording...')
    cam.stop_recording()
    vid_file.close()

    # Shut system down
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

def gps_loop(q,*args):
    while True:
        q.put(get_gps(*args))

def overlay_text(fields):
     overlay_text = '{date} {time} | Posit:ion: {lat} {lat_dir} -- {lon} {lon_dir} | Speed: {speed} {speed_units} | Trk: {trk}'.format(
            **fields
            )
     return overlay_text
# ================== MAIN FUNCTION =======================================

def main(height=None, width=None, frames=None, clip_dur=None, min_space=None, vid_dir=None,
         shutdown_pin=None, highlight_pin=None, speed_conversion=1, speed_units=''):
    # ensure device perameters type
    res = (int(width), int(height))  # resolution of the video recording 
    frames = int(frames)   # framerate of the video recording
    clip_dur = int(clip_dur)    # duration of individual clips
    min_space = int(min_space)  # the maximum percentage of used storage allowed
    convert = float(speed_conversion)     # Speed conversion factor
    # vid_dir = '/home/pi/dashcam/vids'  # Directory where clips are stored
      
    # change to the videos directory
    os.chdir(vid_dir)
    
    # initialize the serial port
    port = Serial('/dev/serial0')
    gps_q = Queue()
    gps_TH = Thread(target=get_gps, args=(port, gps_q))
    gps_TH.daemon = True
    gps_TH.start()
    msg = gps_q.get()

    # Initialize the overaly text
    overlay = {
            'lat' : 'xxx',
            'lat_dir' : 'x',
            'lon' : 'xxx',
            'lon_dir' : 'x',
            'speed' : 'x',
            'trk' : 'x',
            'date' : msg.datestamp,
            'time' : msg.timestamp,
            'speed_units' : speed_units
            }
    
    # Start Recording
    filename = os.path.join('vids', format_filename(**overlay))
    vid_file = [open(filename, 'wb')]
    cam = pc.PiCamera(resolution=res, framerate=frames)
    cam.start_recording(vid_file[0], 
                        format='h264',
                        quality=15,
                        resize=res,
                        sps_timing=True
                        )
    cam.annotate_background = Color('black')
    cam.annotate_text = overlay_text(overlay)
    print('Recording to {}...'.format(filename)) 

    # initialize shutdown button
    shutdown_pin = Button(shutdown_pin, pull_up=False)
    
    # initialize highlight button
    highlight_button = Button(highlight_pin)
    
    # main while loop
    while True:
        # check the file system and remove oldest video if not enough storage
        file_sweeper_TH = Thread(target=file_sweeper,
                                kwargs=dict(path=os.getcwd(), max_space=min_space)
                                )
        file_sweeper_TH.start()

        # Annotation loop
        timeout = time.time() + clip_dur #- 30
        tic = time.time()
        while time.time() < timeout:
           
            # update overlay text
            msg = gps_q.get()
            overlay['lat'] =msg.lat
            overlay['lat_dir'] = msg.lat_dir, 
            overlay['lon'] = msg.lon 
            overlay['lon_dir'] = msg.lon_dir,
            overlay['speed'] = msg.spd_over_grnd
            overlay['trk'] = msg.true_course
            overlay['date'] = msg.datestamp #!!! need to format these (probably with datetime)
            overlay['time'] = msg.timestamp
            cam.annotate_text = overlay_text(overlay)
            print(overlay_text(overlay))

            # Check shutdown button press
            toc = time.time() - tic
            if not shutdown_pin.is_pressed:
                shutdown(cam, vid_file.pop(-1))
            tic = time.time()
            
            # Check highlight button press
            if False:
                highlight(stream, **overlay)
            print('Time between shutdown checks: {}'.format(toc))


        # save the current video
        filename = os.path.join('vids',format_filename(**overlay))
        vid_file.append(open(filename, 'wb'))
        cam.split_recording(vid_file[-1])
        vid_file.pop(0).close()
        print('recording to ' + filename )
    
if __name__ == "__main__":
    # get arguments for main() from the config file
    config = ConfigParser()
    config.read('config.ini')
    settings = config['SETTINGS']

    main(**settings)



# Setup
## Pi Configuration
Several of your Pi's settings will need to be changed. Open your Pi's configuration menue by entering `sudo raspi-config` in a command prompt. We'll be making three changes in this menu. We'll want to setup a unique password for the "Pi" user, enable the Pi Camera and hardwar UART serial port. Use the arrow keys to navigate to the "Interface Options" (it should be the third option in the menu). Select the "P1 Camera" option and enable it. Next navigate back to the Interface Options and select "P6 Serial Port". There will be two prompts: The first prmpt asks if you'd like a login shell over serial. Select "<NO>". The next asks if you'd like to enable the serial port hardware. Select "<YES>". You should also take this opportunity to change the default password for the Pi user. This can be done in System Options > S3 Password.

## Packages to be installed
- picamera
- psutil
 

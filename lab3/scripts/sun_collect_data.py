# point at sun and collect data using threading

# use ipython instead of jupyter notebook
# pull up webcam 
# make sure we're repointing very often (faster than 4 min ?)

import ugradio
import astropy.coordinates
import astropy.time
import time
import matplotlib.pylab as plt
import numpy as np
import snap_spec
import threading
import logging

def track():
    i=0
    t0 = astropy.time.Time(time.time(), format='unix')
    t_e = 0
    logging.info(f'Tracking start time (JD): {t0}')
    while t_e < total_time:
        logging.info('')
        logging.info(f'Iteration: {i}')
        # get the coordinates of the sun in RA and DEC
        t = astropy.time.Time(time.time(), format='unix')
        t_e = t - t0
        t_e = t_e * 24 * 60
        logging.info(f'Tracking time elapsed (min): {t_e}')
        sun = astropy.coordinates.get_sun(t)
        # convert coordinates to alt az (Earth coordinates)
        altaz = astropy.coordinates.AltAz(obstime=t, location=obs) # defines a time and a location on earth
        pointing = sun.transform_to(altaz)
        logging.info(f'Sun is currently at alt, az: {pointing.alt.deg}, {pointing.az.deg}')
      

        # 3/6/23 EDIT: point interf twice: not necessary 
        try:
            interf.point(pointing.alt.deg, pointing.az.deg) # could set wait=False to do other stuff while the telescope is moving
            interf.point(pointing.alt.deg, pointing.az.deg)
            logging.info(f'interf now pointing at: {interf.get_pointing()}')
        except(AssertionError):
            logging.warning('Assertion Error in pointing: trying again')
#             interf.point(pointing.alt.deg, pointing.az.deg)
        i+=1
        
def record():
    i=0
    prev_cnt = None
    t0 = astropy.time.Time(time.time(), format='unix')
    t_e = 0
    logging.info(f'Recording start time (JD): {t0}')
    while t_e < total_time:
#     while True:
        t = astropy.time.Time(time.time(), format='unix')
        t_e = t - t0
        t_e = t_e * 24 * 60
        logging.info(f'Recording time elapsed (min): {t_e}')
        # collect data
        try:
            data = spec.read_data(prev_cnt=prev_cnt)
            prev_cnt = data['acc_cnt']
            np.save(f'{save_dir}sun_{i}', data)
            i+=1
        except(AssertionError):
            logging.warning('Assertion Error in recording: trying again')
            prev_cnt = None
    
           
    
if __name__=="__main__":
    
    save_dir = '/home/pi/Blueberry Pi/astro121lab/lab3/data/sun/full_day_sun_3_18/'
    logging.basicConfig(filename=f'{save_dir}full_day_sun_log.log', level=logging.INFO)
    total_time = 23*60 # duration of observation in minutes

    # create interferometer object
    interf = ugradio.interf.Interferometer()
    spec = snap_spec.snap.UGRadioSnap()
    spec.initialize(mode='corr')
    obs = astropy.coordinates.EarthLocation(lon=ugradio.nch.lon, lat=ugradio.nch.lat, height=ugradio.nch.alt)

    # try to point to the sun if the current az alt are within bounds
    risen = False
    while risen == False:
        t = astropy.time.Time(time.time(), format='unix')
        logging.info(f'First tracking start time (JD): {t}')
        sun = astropy.coordinates.get_sun(t)
        # convert coordinates to alt az (Earth coordinates)
        altaz = astropy.coordinates.AltAz(obstime=t, location=obs) # defines a time and a location on earth
        pointing = sun.transform_to(altaz)
        logging.info(f'Sun is currently at alt, az: {pointing.alt.deg}, {pointing.az.deg}')

        if not (pointing.alt.deg > ugradio.interf.ALT_MIN and
            pointing.alt.deg < ugradio.interf.ALT_MAX and
            pointing.az.deg > ugradio.interf.AZ_MIN and
            pointing.az.deg < ugradio.interf.AZ_MAX):
            logging.info(f'Sun has not risen yet')
            time.sleep(60)
            continue
        else:
            risen = True
            
    # only begin runs when the interfermeters are able to successfully point to the sun        
    successful_pointing=False
    while successful_pointing == False:
        try:
            interf.point(pointing.alt.deg, pointing.az.deg)
            successful_pointing=True
        except(AssertionError):
            logging.info(f'Unsuccessful pointing, trying again in a minute')
            time.sleep(60)
            
    

    # 3/6/23 EDIT: point interf twice: not necessary 
    interf.point(pointing.alt.deg, pointing.az.deg)
    interf.point(pointing.alt.deg, pointing.az.deg)
    logging.info(f'interf now pointing at: {interf.get_pointing()}')
    
    
    
    
    # start threading
    thrd = threading.Thread(target=track)
    thrd.start()
    record()
    logging.info('Finished collecting data!')
    interf.stow() # always finsih every observation with this
    interf.stow()
    logging.info(f'interf stowed at: {interf.get_pointing()}')

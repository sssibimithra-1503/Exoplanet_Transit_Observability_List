import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time
from astropy import units as u
from astroplan import Observer, FixedTarget, EclipsingSystem
from astroplan.plots import plot_altitude
from pytz import timezone
import matplotlib.dates as mdates

#Define Location
location = EarthLocation.from_geodetic(78.875 * u.deg, 12.34 * u.deg,700 * u.m)
vbo = Observer(location= location, name='VBO Kavalur', timezone=timezone('Asia/Kolkata'))

def JCBT_Observability_Chart(catalog_path, date_str, planet_name ):
    # Read catalog
    df = pd.read_csv(catalog_path)

    # select target from the catalog
    target_df = df[df['name'].str.strip() == planet_name]
    if target_df.empty:
        print(f"Error:{planet_name} not found")
        return
    plt.figure(figsize=[10, 7])

    # Start time in UT [ist=4pm: ut= ist-5.5]
    start_time = Time(f"{date_str} 10:30:00")


    #Calculate sunset & sunrise to get night duration of that date
    sunset = vbo.sun_set_time(start_time, which='next')
    sunrise = vbo.sun_rise_time(sunset, which='next')

    #To create grid
    plot_times = sunset + (sunrise-sunset) * np.linspace(0,1,150)

    #loop through the csv, select the given target and not the entire list
    for _, row in target_df.iterrows():
        try:
            coord = SkyCoord(row ['RA'], row['Dec'], unit = [u.hourangle, u.deg])
            target = FixedTarget(coord= coord, name=row['name'])

            #Transit Timing
            system = EclipsingSystem(primary_eclipse_time=Time(row['epoch'],format='jd'),orbital_period=row['period'] * u.day,duration=row['duration'] * u.hour)

            mid_transit= system.next_primary_eclipse_time(sunset)[0]

            if mid_transit < sunrise:
                transit_time = system.next_primary_ingress_egress_time(sunset, n_eclipses=1)
                ingress = transit_time[0][0]
                egress = transit_time[0][1]

                # calculate IST
                ist_tz = timezone('Asia/Kolkata')
                t_start = ingress.to_datetime(ist_tz).strftime('%I:%M %P')
                t_peak = mid_transit.to_datetime(ist_tz).strftime('%I:%M %P')
                t_end = egress.to_datetime(ist_tz).strftime('%I:%M %P')


            else:
                t_start = t_peak = t_end = "No Transit Today"

            #plotting
            a = plot_altitude(target, vbo, plot_times, brightness_shading = True)


            #x-axis in IST
            fmt=mdates.DateFormatter('%I:%M %P', tz=ist_tz)
            a.xaxis.set_major_formatter(fmt)


        except Exception  as e:
            print(f"Error plotting:{planet_name}: {e}")

    # Plot Vertical lines for the transit events and altitude limit line
    plt.axvline(x=ingress.plot_date, color='red', linestyle='--', label=f"T_Start:({t_start})")
    plt.axvline(x=egress.plot_date, color='red', linestyle='--', label=f"T_End:({t_end}")
    plt.axvspan(ingress.plot_date, egress.plot_date, color='yellow', alpha=0.2, label='Transit Duration')

    plt.axhline(y=30, color='green', linestyle='--', label="Limit (Alt 30°)")

    #Label
    plt.title(f"JCBT OBSERVABILITY CHART: {planet_name} | {date_str}\n" f"Start:{t_start} | Peak:{t_peak} | End:{t_end} (IST)")
    plt.xlabel("Time (IST)")
    plt.ylim(0, 90)
    plt.legend(loc = 'upper right')
    plt.grid(True, alpha=0)
    plt.tight_layout()
    plt.show()

#Execute
catalog_file="/home/hp/topcat/combine_2"
JCBT_Observability_Chart(catalog_file,"2026-02-16","TIC 437248515.01")
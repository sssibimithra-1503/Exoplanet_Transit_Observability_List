import pandas as pd
from astropy.coordinates import EarthLocation, SkyCoord
from astropy.time import Time
from astropy import units as u
from astroplan import Observer, FixedTarget, EclipsingSystem
from pytz import timezone
from astroplan import (PrimaryEclipseConstraint, is_event_observable,AtNightConstraint, AltitudeConstraint)

#Define Location
location = EarthLocation.from_geodetic(78.875 * u.deg, 12.34 * u.deg,700 * u.m)
vbo = Observer(location= location, name='VBO Kavalur', timezone=timezone('Asia/Kolkata'))

def Transit_time_csv(catalog_path, date_str, output_file ):
    # Read catalog
    df = pd.read_csv(catalog_path)

    #Creating Output File
    transit_csv=[]
    ist_tz = timezone('Asia/Kolkata')

    # strat time in UT [ist=6pm: ut= ist-5.5]
    start_time = Time(f"{date_str} 12:30:00")
    # end time in UT [ist=5am: ut= ist-5.5]
    end_time = Time(f"{date_str} 23:30:00")

    #Calculate sunset & sunrise to get night duration of that date
    #sunset = vbo.sun_set_time(start_time, which='next')
    #sunrise = vbo.sun_rise_time(sunset, which='next')

    #loop through the csv, select the given target and not the entire list
    for _, row in df.iterrows():
        try:
            RA_extract = str(row['RA']).strip()
            Dec_extract = str(row['Dec']).strip()
            vmag_extract = str(row['vmag']).strip()
            period_extract = str(row['period']).strip()
            duration_extract = str(row['duration']).strip()

            planet_name = str(row['name']).strip()
            coord = SkyCoord(row['RA'], row['Dec'], unit=[u.hourangle, u.deg])
            current_dec = coord.dec.deg
            target = FixedTarget(coord=coord, name=planet_name)

            vmag=pd.to_numeric(row['vmag'],errors='coerce')

            if current_dec < -65 or current_dec > 65:
                continue
            if pd.isna(vmag) or vmag > 15:
                continue

            #Transit Timing
            system = EclipsingSystem(primary_eclipse_time=Time(row['epoch'],format='jd'),orbital_period=row['period'] * u.day,duration=row['duration'] * u.hour)

            mid_transit= system.next_primary_eclipse_time(start_time)[0]

            transit_time = system.next_primary_ingress_egress_time(start_time, n_eclipses=1)
            ingress = transit_time[0][0]
            egress = transit_time[0][1]

            #Filters the object for which transition occurs in the given night:
            if ingress < start_time or egress > end_time:
                continue

            constraints = [AtNightConstraint.twilight_civil(), AltitudeConstraint(min=30 * u.deg)]

            is_obs = is_event_observable(constraints, vbo, target, times=[ingress,mid_transit,egress])

            if not all(is_obs[0]):
                continue

            # calculate IST
            ist_tz = timezone('Asia/Kolkata')
            t_start = ingress.to_datetime(ist_tz).strftime('%I:%M %P')
            t_peak = mid_transit.to_datetime(ist_tz).strftime('%I:%M %P')
            t_end = egress.to_datetime(ist_tz).strftime('%I:%M %P')

            transit_csv.append({"Planet Name": planet_name,"RA":RA_extract,"Dec":Dec_extract,"vmag":vmag_extract ,"Start Of Transit": t_start, "Peak Of Transit": t_peak, "End Of Transit": t_end,"Period":period_extract,"Duration":duration_extract})

        except Exception as e:
            pass

    new=pd.DataFrame(transit_csv)
    new.to_csv(output_file)

#Execute
catalog_file="/home/hp/topcat/combine_2"
Transit_time_csv(catalog_file,"2026-02-16","transit_csv_final")





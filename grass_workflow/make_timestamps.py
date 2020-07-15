#!/usr/bin/env python3

#%module
#% description: Retrieve timestamps from Sentinel bands and cloudmasks from current mapset.
#%end

#%option G_OPT_F_OUTPUT
#% key: output_ras
#% description: Name of output timestamps file for raster data (sentinel bands)
#%end

#%option G_OPT_F_OUTPUT
#% key: output_vec
#% description: Name of output timestamps file for vector data (cloudmasks)
#%end

# PyGrass Skript to retrieve timestamps for satellite data (raster) and cloudmasks (vector), save them to a textfile
# files will be used to space-time-datacube creation

import sys
import os
from datetime import datetime, timedelta

import grass.script as gs

from grass.pygrass.gis import Mapset
from grass.pygrass.modules import Module


def main():
    mapset = Mapset()
    mapset.current()

    with open(options['output_ras'], 'w') as fd:
        for rast in mapset.glist('raster'):
            items = rast.split('_')
            d = datetime.strptime(items[0], '%Y%m%dT%H%M%S')
            ## workaround to create timespan
            dd = d + timedelta(seconds=1)
            fd.write("{0}|{1}|{2}{3}".format(
                rast,
                d.strftime('%Y-%m-%d %H:%M:%S'),
                dd.strftime('%Y-%m-%d %H:%M:%S'),
                os.linesep))

    with open(options['output_vec'], 'w') as fd:
        for rast in mapset.glist('raster', pattern='*_B02.tif'):
            items = rast.split('_')
            d = datetime.strptime(items[0], '%Y%m%dT%H%M%S')
            ## workaround
            dd = d + timedelta(seconds=1)

            vect = 'cloudmask_{}_mergedvector'.format(items[0])

            Module('r.mask', vector=vect, overwrite=True)
            Module('g.remove', flags='f', type='vector', name=vect)
            Module('g.rename', raster=['MASK', vect])
            fd.write("{0}|{1}|{2}{3}".format(
                vect,
                d.strftime('%Y-%m-%d %H:%M:%S'),
                dd.strftime('%Y-%m-%d %H:%M:%S'),
                os.linesep))

    return 0


if __name__ == "__main__":
    options, flags = gs.parser()

    sys.exit(main())

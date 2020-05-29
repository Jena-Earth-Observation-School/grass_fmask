# this script takes as an input a directory with cloudmasks generated by fmask (i.e. iter_fmask script)
# it detects cloudmasks of the same date and creates a merged vector file with clouds and clouds mask for Jena Roda AOI

import numpy as np
import os
import sys
import rasterio.features
import rasterio.mask
from shapely.geometry import shape, MultiPolygon
import geopandas as gpd


def reclass_to_file(cloudmask):

    with rasterio.open(cloudmask) as clouds:
        reclass = clouds.read()
        profile = clouds.profile  # save metadata for file creation/writing
        reclass = binary_reclass(reclass) # reclassify values of fmask result
        #TRY IF THESE CHANGES WORK:
        #reclass_filename = cloudmask.replace('.img', '.tif') # create new filename

        with rasterio.open(cloudmask, 'w', **profile) as dst:
            # Write reclassfied raster to disk
            dst.write(reclass)
        print(cloudmask + ' was reclassified and saved to tif file.')

        # with rasterio.open(reclass_filename, 'w', **profile) as dst:
        #     # Write reclassfied raster to disk
        #     dst.write(reclass)
    #return(reclass_filename)


def binary_reclass(cloudmask):
    # reclassify values in order to only keep clouds (fmask value 2) and cloud shadow (fmask value 3)
    cloudmask[np.where(cloudmask < 2)] = 0
    cloudmask[np.where(cloudmask == 2)] = 1
    cloudmask[np.where(cloudmask == 3)] = 1
    cloudmask[np.where(cloudmask > 3)] = 0
    return cloudmask


def reclass_to_mergedvector(clouds_reclass, new_dir): # clouds_reclass is a list of the two reclassified rasters of one date

    with rasterio.open(clouds_reclass[0]) as clouds_rc1, \
            rasterio.open(clouds_reclass[1]) as clouds_rc2:

        clouds_crs = str(clouds_rc1.crs) # retrieve crs for saving of vector data

        cl_shp1 = binary_to_vector(clouds_rc1)
        cl_shp2 = binary_to_vector(clouds_rc2)

        clouds_gpd = gpd.GeoDataFrame(geometry=[cl_shp1, cl_shp2]) # convert to geopanda dataframe

        geoms = clouds_gpd.geometry.unary_union # merge/unite polygons of overlapping areas
        clouds_vec = gpd.GeoDataFrame(geometry=[geoms])
        clouds_vec.crs = clouds_crs

        # create new filename to save merged vectordata into new_dir
        dir = clouds_reclass[0].split('/')
        names = dir[-1].split('_')
        clouds_gp = names[2] + '_' + names[1]
        clouds_gp += '_cloudmask_mergedvector.gpkg'
        # save to file
        clouds_vec.to_file(os.path.join(new_dir, clouds_gp), driver='GPKG')
        print('Merged vector file ' + clouds_gp + ' was saved to file.')


def binary_to_vector(binary_raster):
    vector = rasterio.features.dataset_features(binary_raster, as_mask=True, geographic=False) # vectorize raster data
    shapes = MultiPolygon([shape(feature['geometry']).buffer(0) for feature in vector]) # extract polygon geometries
    return shapes


def main():
    cloudmasks_dir = sys.argv[1]
    # create new directory for merged cloudmasks
    merged_clouds_dir = os.path.join(cloudmasks_dir, 'merged_cloudmasks')
    os.makedirs(merged_clouds_dir, exist_ok=True)

    # get all cloudmasks listed in input directory
    masks = os.listdir(cloudmasks_dir)
    masks_img = []
    for i in masks:
        if i.endswith('.img'):
            masks_img.append(i)
    print(masks_img)
    # get unique sensing dates
    dates = []
    for i in masks_img:
            dates.append(i.split('_')[2])
    dates_unique = list(set(dates))

    # iterate over unique dates to merge cloudmasks
    for c in dates_unique:
        # get full paths of matching cloudmasks

        clmasks = [i for i in masks_img if c in i]

        if len(clmasks) != 2:
            print('There are more than two cloudmasks of the same date available for ' + str(c) +
                  '. Please check the data. We will go on with the next date.')
            continue
        elif len(clmasks) < 2:
            print('There are less than two cloudmasks of the same date available for ' + str(c) +
                  '. Please check the data. We will go on with the next date.')
            continue

        clmasks = [os.path.join(cloudmasks_dir, i) for i in clmasks]
        [reclass_to_file(i) for i in clmasks] # reclassify both masks
        #cl_reclass = [reclass_to_file(i) for i in clmasks] # reclassify both masks
        reclass_to_mergedvector(clmasks, merged_clouds_dir)
        #reclass_to_mergedvector(cl_reclass, merged_clouds_dir)



if __name__ == '__main__':
    main()


#!/usr/bin/env python3

# Given:
#  - a dicom file a t1 structural that has been processed by recon-all ('args.source_dicom_filename')
#  - a dicom-seg file ('args.dicom_seg_filename')
#  - a aseg.stats file ('args.aseg_stats_filename')
#  - a json encoding the template dcmqi instructions for generating a DICOM-sr from aseg.stats ('args.aseg_to_dicom_sr_template')
#    - This is the file `aseg-to-DICOM-sr-template.json` in this repo
#  - the output filename for the dcmqi instructions for generating the DICOM-sr ('args.output_aseg_to_dicom_sr_json')

# Produce:
#  - A json file used to convert aseg.stats to dicom-sr ('args.output_aseg_to_dicom_sr_json')

from __future__ import print_function
import argparse
import pydicom
import json
import csv
import os
import pprint

# Parse inputs
parser = argparse.ArgumentParser(description='Parse the input to the container')
parser.add_argument('source_dicom_filename')
parser.add_argument('dicom_seg_filename')
parser.add_argument('aseg_stats_filename')
parser.add_argument('aseg_to_dicom_sr_template')
parser.add_argument('output_aseg_to_dicom_sr_json')

args = parser.parse_args()

# Populate the list of relevant dicom files
dcm_filelist = []
dcm_series_uid = pydicom.dcmread(args.source_dicom_filename).SeriesInstanceUID 
dicom_dir = os.path.dirname(args.source_dicom_filename)
for f in os.listdir(dicom_dir):
    try:
        if (pydicom.dcmread(os.path.join(dicom_dir, f)).SeriesInstanceUID == dcm_series_uid):
            dcm_filelist.append(f)
    except:
        pass
#print(dcm_filelist)

# Read in aseg.stats
aseg_stats = []
with open(args.aseg_stats_filename) as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in csvreader:
        aseg_stats.append(row)
#print(aseg_stats)

# Read in template json
with open(args.aseg_to_dicom_sr_template) as f:
    data = json.load(f)
#print(data)
pprint.pprint(data)


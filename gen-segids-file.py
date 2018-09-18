#!/usr/bin/env python3

# Given:
#  a json file used to convert an aseg to dicom-seg ('args.aseg_to_dicom_seg_json')

# Produce:
#  A list of seg ids that can be passed to asegstats2table (as --segids-from-file <file>)

# Example:
#  python ./gen-segids-file.py ./fs-aseg.json > segids.txt

from __future__ import print_function
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('aseg_to_dicom_seg_json')
args = parser.parse_args()

with open(args.aseg_to_dicom_seg_json) as f:
    dcm_seg_data = json.load(f)

label_set = set([])
for label in dcm_seg_data["segmentAttributes"][0]:
	label_set.add(label["labelID"])

# As of fs v6.0.1, the following labels are included in aseg.mgz, but not in 
# aseg.stats, so remove them from the label set
# - "labelID": 2,  "SegmentDescription": "Left-Cerebral-White-Matter"
# - "labelID": 3,  "SegmentDescription": "Left-Cerebral-Cortex"
# - "labelID": 41, "SegmentDescription": "Right-Cerebral-White-Matter"
# - "labelID": 42, "SegmentDescription": "Right-Cerebral-Cortex"

labels_to_exclude = set({2,3,41,42})
final_label_set = label_set - labels_to_exclude

print(*final_label_set,sep='\n')

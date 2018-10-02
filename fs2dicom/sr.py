import json
import os

import jinja2
import numpy as np
import pandas as pd
import pydicom

from fs2dicom import utils

SeriesInstanceUID = (0x0020, 0x000e)
SOPInstanceUID = (0x0008, 0x0018)


# create_dicom_sr
def add_gm_wm_to_dataframe(aseg_dataframe, aseg_stats_file):
    label_number_dict = {'Left-Cerebral-White-Matter': 2,
                         'Left-Cerebral-Cortex': 3,
                         'Right-Cerebral-White-Matter': 41,
                         'Right-Cerebral-Cortex': 42}

    label_name_dict = {'lhCerebralWhiteMatter': 'Left-Cerebral-White-Matter',
                       'lhCortex': 'Left-Cerebral-Cortex',
                       'rhCerebralWhiteMatter': 'Right-Cerebral-White-Matter',
                       'rhCortex': 'Right-Cerebral-Cortex'}

    def get_volume(line):
        return float(line.split(',')[-2])

    label_stats = []
    with open(aseg_stats_file) as f:
        for line in f:
            for label in label_name_dict:
                if label in line:
                    vol = get_volume(line)
                    struct = label_name_dict[label]
                    row = {'SegId': label_number_dict[struct],
                           'NVoxels': np.nan,
                           'Volume_mm3': vol,
                           'StructName': struct,
                           'normMean': np.nan,
                           'normStdDev': np.nan,
                           'normMin': np.nan,
                           'normMax': np.nan,
                           'normRange': np.nan}
                    label_stats.append(row)

    aseg_gm_wm_dataframe = aseg_dataframe.append(label_stats).reset_index(drop=True)

    return aseg_gm_wm_dataframe


def get_aseg_stats_dataframe(aseg_stats_file):
    column_headers = ['SegId',
                      'NVoxels',
                      'Volume_mm3',
                      'StructName',
                      'normMean',
                      'normStdDev',
                      'normMin',
                      'normMax',
                      'normRange']

    aseg_dataframe = pd.read_table(aseg_stats_file,
                                   delim_whitespace=True,
                                   header=None,
                                   comment='#',
                                   index_col=0,
                                   names=column_headers)

    aseg_gm_wm_dataframe = add_gm_wm_to_dataframe(aseg_dataframe, aseg_stats_file)

    return aseg_gm_wm_dataframe


def get_dicom_tag_value(dicom_file, tag):
    dcm = pydicom.dcmread(dicom_file)
    tag_value = dcm[tag].value

    return str(tag_value)


def get_t1_dicom_files_dict(t1_dicom_file):
    """ (file) -> dict(str: [str])
    """
    t1_dicom_files = []

    t1_dicom_series_uid = get_dicom_tag_value(t1_dicom_file, SeriesInstanceUID)
    t1_dicom_dir = utils.abs_dirname(t1_dicom_file)

    for dcm in os.listdir(t1_dicom_dir):
        dcm_file_path = os.path.join(t1_dicom_dir, dcm)
        dcm_series_uid = get_dicom_tag_value(dcm_file_path, SeriesInstanceUID)
        if dcm_series_uid == t1_dicom_series_uid:
            t1_dicom_files.append(dcm)

    return {str(t1_dicom_series_uid): t1_dicom_files}

# ## need {seg_number: label_name} dict to make sure aseg.csv matches label names
# ## rewrite a simple parser instead?
# for segno in seg_numbers:
#     find_matching_label_name()
#     add_to_template(label_name, segno, label_dict, stats_file)


def generate_aseg_dicom_sr_metadata(dicom_sr_template,
                                    aseg_dicom_seg_metadata_file,
                                    aseg_dicom_seg_file,
                                    t1_dicom_file,
                                    aseg_dicom_sr_metadata,
                                    aseg_stats_file):
    """

    Use jinja2 template to fill in values, based on pdf-report code and
    https://gist.github.com/sevennineteen/4400462

    """
    template_path = utils.abs_dirname(dicom_sr_template)
    sr_template_filename = os.path.basename(dicom_sr_template)

    aseg_dicom_filename = os.path.basename(aseg_dicom_seg_file)

    t1_files_dict = get_t1_dicom_files_dict(t1_dicom_file)
    for key in t1_files_dict:
        t1_dicom_files = t1_files_dict[key]
        t1_dicom_series_instance_uid = key

    dicom_seg_instance_uid = get_dicom_tag_value(aseg_dicom_seg_file, SeriesInstanceUID)

    with open(aseg_dicom_seg_metadata_file) as f:
        aseg_dicom_seg_metadata = json.load(f)

    aseg_stats_data = get_aseg_stats_dataframe(aseg_stats_file)

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
    template = env.get_template(sr_template_filename)
    template_vars = {'aseg_dicom_seg_file': aseg_dicom_filename,
                     't1_dicom_files': t1_dicom_files,
                     't1_dicom_series_instance_uid': t1_dicom_series_instance_uid,
                     'dicom_seg_instance_uid': dicom_seg_instance_uid,
                     'aseg_dicom_seg_metadata': aseg_dicom_seg_metadata,
                     'aseg_stats_data': aseg_stats_data}

    template.stream(template_vars).dump(aseg_dicom_sr_metadata)


def get_generate_dicom_sr_cmd(t1_dicom_file,
                              aseg_dicom_seg_file,
                              aseg_dicom_sr_output,
                              aseg_dicom_sr_metadata):
    command_template = '''\
tid1500writer \
--inputImageLibraryDirectory {t1_dicom_dir} \
--inputCompositeContextDirectory {aseg_dicom_seg_dir} \
--outputDICOM {aseg_dicom_sr_output} \
--inputMetadata {aseg_dicom_sr_metadata}'''

    t1_dicom_dir = utils.abs_dirname(t1_dicom_file)
    aseg_dicom_seg_dir = utils.abs_dirname(aseg_dicom_seg_file)

    return command_template.format(t1_dicom_dir=t1_dicom_dir,
                                   aseg_dicom_seg_dir=aseg_dicom_seg_dir,
                                   aseg_dicom_sr_output=aseg_dicom_sr_output,
                                   aseg_dicom_sr_metadata=aseg_dicom_sr_metadata)

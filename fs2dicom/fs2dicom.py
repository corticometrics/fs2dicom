import base64
import json
import pkg_resources
import os
import shlex
import subprocess
import sys
import tempfile

import click
import numpy as np
import pandas as pd
import pydicom
from jinja2 import Environment, FileSystemLoader


CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help']}

SeriesInstanceUID = (0x0020, 0x000e)
SOPInstanceUID = (0x0008, 0x0018)

TEMPLATE_PATH = pkg_resources.resource_filename('fs2dicom', 'templates')

aseg_metadata_filename = 'fs-aseg.json'
sr_template_filename = 'fs-aseg-sr-template.json'
aseg_metadata = os.path.join(TEMPLATE_PATH, aseg_metadata_filename)
sr_template = os.path.join(TEMPLATE_PATH, sr_template_filename)

no_fs_license_message = 'Path to FreeSurfer License file is needed. Pass it with the --fs_license_key flag, or set the environment variable FS_LICENSE_KEY'


# basic defs
def run_docker_commands(commands, docker_image, volumes, environment, pull=False):
    client = docker.from_env()

    if pull:
        client.images.pull(docker_image)
    for command in commands:
        client.containers.run(docker_image, command=shlex.split(command), volumes=volumes, environment=environment)
    client.close()


def run_local_commands(commands):
    for command in commands:
        subprocess.run(shlex.split(command))


def base64_convert(file):
    """ (file) -> str
    command to create `-e FS_KEY=...` input:
    base64 -w 1000 cat /home/ltirrell/local/freesurfer/license.txt
    """
    with open(file, 'rb') as f:
        encoded_file = base64.b64encode(f.read()).decode('ascii')

    return encoded_file


# create_dicom_seg
def get_resample_aseg_cmd(aseg_image_file, t1_dicom_file, output_dir):
    command_template = 'mri_vol2vol --mov {aseg_image_file} --targ {t1_dicom_file} --regheader --nearest --o {output_dir}/aseg_native_space.nii.gz'

    return command_template.format(aseg_image_file=aseg_image_file,
                                   t1_dicom_file=t1_dicom_file,
                                   output_dir=output_dir)


def get_generate_dicom_seg_cmd(resampled_aseg, aseg_dicom_seg_metadata, t1_dicom_file, aseg_dicom_seg_output):
    command_template = 'itkimage2segimage --inputDICOMDirectory {t1_dicom_dir} --inputMetadata {aseg_dicom_seg_metadata} --inputImageList {resampled_aseg} --outputDICOM {aseg_dicom_seg_output} --skip'

    t1_dicom_dir = os.path.dirname(t1_dicom_file)

    return command_template.format(resampled_aseg=resampled_aseg,
                                   aseg_dicom_seg_metadata=aseg_dicom_seg_metadata,
                                   t1_dicom_dir=t1_dicom_dir,
                                   aseg_dicom_seg_output=aseg_dicom_seg_output)


def add_gm_wm_to_dataframe(aseg_dataframe, aseg_stats_file):
    label_dict = {'Left-Cerebral-White-Matter': [2],
                  'Left-Cerebral-Cortex': [3],
                  'Right-Cerebral-White-Matter': [41],
                  'Right-Cerebral-Cortex': [42]}

    with open(aseg_stats_file) as f:
        for line in f:
            if 'lhCerebralWhiteMatter' in line:
                label_dict['Left-Cerebral-White-Matter'].append(float(line.split(',')[-2]))
            if 'rhCerebralWhiteMatter' in line:
                label_dict['Right-Cerebral-White-Matter'].append(float(line.split(',')[-2]))
            if 'lhCortex' in line:
                label_dict['Left-Cerebral-Cortex'].append(float(line.split(',')[-2]))
            if 'rhCortex' in line:
                label_dict['Right-Cerebral-Cortex'].append(float(line.split(',')[-2]))
    # create list of dicts for each column, with np.nan for values not available



# create_dicom_sr
def get_aseg_stats_dataframe(aseg_stats_file):
    column_headers = ['SegId', 'NVoxels', 'Volume_mm3', 'StructName', 'normMean', 'normStdDev', 'normMin', 'normMax', 'normRange']

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
    t1_dicom_dir = os.path.dirname(t1_dicom_file)

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


def generate_aseg_dicom_sr_metadata(dicom_sr_template, aseg_dicom_seg_file, t1_dicom_file, aseg_dicom_sr_metadata, aseg_stats_file):
    """

    Use jinja2 template to fill in values, based on pdf-report code and
    https://gist.github.com/sevennineteen/4400462

    """
    template_path = os.path.dirname(dicom_sr_template)
    sr_template_filename = os.path.dirname(dicom_sr_template)

    t1_files_dict = get_t1_dicom_files_dict(t1_dicom_file)
    for key in t1_files_dict:
        t1_dicom_files = t1_files_dict[key]
        t1_dicom_series_instance_uid = key

    aseg_dicom_filename = os.path.basename(aseg_dicom_seg_file)
    dicom_seg_instance_uid = get_dicom_tag_value(aseg_dicom_seg_file, SeriesInstanceUID)
    aseg_stats_data = get_aseg_stats_dataframe(aseg_stats_file)

    env = Environment(loader=FileSystemLoader(template_path))
    template = env.get_template(sr_template_filename)

    template_vars = {'aseg_dicom_seg_file': aseg_dicom_filename,
                     't1_dicom_files': t1_dicom_files,
                     't1_dicom_series_instance_uid': t1_dicom_series_instance_uid,
                     'dicom_seg_instance_uid': dicom_seg_instance_uid,
                     'aseg_dicom_seg_metadata': aseg_dicom_seg_metadata,
                     'aseg_stats_data': aseg_stats_data}

    template.stream(template_vars).dump(aseg_dicom_sr_metadata)


def get_generate_dicom_sr_cmd(t1_dicom_file, aseg_dicom_seg_dir, aseg_dicom_sr_output, aseg_dicom_sr_metadata):
    command_template = 'tid1500writer --inputImageLibraryDirectory {t1_dicom_dir} --inputCompositeContextDirectory {aseg_dicom_seg_dir} --outputDICOM {aseg_dicom_sr_output} --inputMetadata {aseg_dicom_sr_metadata}'

    t1_dicom_dir = os.path.dirname(t1_dicom_file)
    aseg_dicom_seg_dir = os.path.dirname(aseg_dicom_seg_file)

    return command_template.format(t1_dicom_dir=t1_dicom_dir,
                                   aseg_dicom_seg_dir=aseg_dicom_seg_dir,
                                   aseg_dicom_sr_output=aseg_dicom_sr_output,
                                   aseg_dicom_sr_metadata=aseg_dicom_sr_metadata)


# help messages:
dcmqi_type_help = 'Use docker or local installed version of dcmqi (default: docker)'
dcmqi_docker_image_help = 'Name of the dcmqi docker image (default: qiicr/dcmqi:latest)'
freesurfer_type_help = 'Use docker or local installed version of freesurfer (default: docker)'
freesurfer_docker_image_help = 'Name of the FreeSurfer docker image. Currently only supports corticometrics/fs6-base (default: corticometrics/fs6-base:latest)'
fs_license_key_help = 'Path to FreeSurfer License key file. (default: path set by environment variable FS_LICENSE_KEY)'
aseg_dicom_seg_metadata_help = 'Path to the DICOM SEG metadata schema describing the aseg (default: provided within package)'
t1_dicom_file_help = 'Path to one of the DICOM files of the T1-weighted image processed with FreeSurfer to create the aseg.'
dicom_sr_template_help = 'Path to DICOM SR template that is filled in with aseg.stats values (default: provided within package)'


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--dcmqi_type', type=click.Choice(['docker', 'local']), default='docker', help=dcmqi_type_help)
@click.option('--dcmqi_docker_image', default='qiicr/dcmqi:latest', help=dcmqi_docker_image_help)
@click.option('--freesurfer_type', type=click.Choice(['docker', 'local']), default='docker', help=freesurfer_type_help)
@click.option('--freesurfer_docker_image', default='corticometrics/fs6-base:latest', help=freesurfer_docker_image_help)
@click.option('--fs_license_key', envvar='FS_LICENSE_KEY', help=fs_license_key_help)
@click.pass_context
def cli(ctx, dcmqi_type, dcmqi_docker_image, freesurfer_type, freesurfer_docker_image,  fs_license_key):
    """
    Create DICOM Segmentation Image and Structured Report objects from FreeSurfer segmentations.

    Currently requires either docker OR FreeSurfer and dcmqi installed locally

    Docker is the default way to run FreeSurfer and dcmqi commands needed to create DICOM SEG/SR


    A FreeSurfer License key is required to run the docker image. This can be downloaded from: https://surfer.nmr.mgh.harvard.edu/registration.html

    FreeSurfer commands are used to resample the aseg to native space and convert aseg.stats to a csv using asegstats2table. Future versions may remove this dependency
    """
    ctx.obj = ctx.params

    if ctx.obj['freesurfer_type'] == 'docker':
        import docker
        if ctx.obj['fs_license_key'] is None:
            sys.exit(no_fs_license_message)
    elif ctx.obj['dcmqi_type'] == 'docker':
        import docker


@click.command()
@click.argument('aseg_image_file', type=click.Path(exists=True))
@click.argument('aseg_dicom_seg_output', type=click.Path(), default='aseg.dcm')
@click.option('--aseg_dicom_seg_metadata', '-m', type=click.Path(exists=True), default=aseg_metadata, help=aseg_dicom_seg_metadata_help)
@click.option('--t1_dicom_file', '-d', type=click.Path(exists=True), help=t1_dicom_file_help)
@click.pass_context
def create_dicom_seg(ctx, aseg_image_file, aseg_dicom_seg_output, aseg_dicom_seg_metadata, t1_dicom_file):
    """

    FS
      - resample aseg
    dcmqi:
      - generate dicom seg
    """

    if ctx.obj['freesurfer_type'] == 'docker':
        run_docker_command()
        client = docker.from_env(ctx.obj['freesurfer_docker_image'],
                                 get_resample_aseg_cmd())
        client.images.pull(ctx.obj['freesurfer_docker_image'])
        client.containers.run(ctx.obj['freesurfer_docker_image'], command=resample_aseg_command, volumes=resample_aseg_volume_dict, environment=resample_aseg_environment_dict)

    resample_aseg(aseg_image_file, t1_dicom_file)
    generate_dicom_seg(resampled_aseg, aseg_dicom_seg_metadata, aseg_dicom_seg_output)


@click.command()
@click.argument('aseg_stats_file', type=click.Path(exists=True))
@click.argument('aseg_dicom_seg_file', type=click.Path(), default='aseg.dcm')
@click.argument('aseg_dicom_sr_metadata_output', type=click.Path(), default='fs-aseg-sr.json')
@click.argument('aseg_dicom_sr_output', default='aseg-sr.dcm')
@click.option('--aseg_dicom_seg_metadata', '-m', type=click.Path(exists=True), default=aseg_metadata, help=aseg_dicom_seg_metadata_help)
@click.option('--dicom_sr_template', '-t', type=click.Path(exists=True), default=sr_template, help=dicom_sr_template_help)
@click.option('--t1_dicom_file', '-d', type=click.Path(exists=True), help=t1_dicom_file_help)
@click.pass_context
def create_dicom_sr(aseg_stats_file,  aseg_dicom_seg_file, aseg_dicom_sr_metadata, aseg_dicom_sr_output, aseg_dicom_seg_metadata, dicom_sr_template, t1_dicom_file):
    """
    # with tempfile.TemporaryDirectory() as tmpdirname:
    #     print('created temporary directory', tmpdirname)
    FS
      - convert aseg stats
    python
      - generate_aseg stats json
    dcmqi:
     - generate dicom sr
    """
    ...


cli.add_command(create_dicom_seg)
cli.add_command(create_dicom_sr)

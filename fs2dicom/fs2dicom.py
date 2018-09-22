import json
import pkg_resources
import os
import subprocess
import sys
import tempfile

import click
import pydicom
from jinja2 import Environment, FileSystemLoader


CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help']}

TEMPLATE_PATH = pkg_resources.resource_filename('fs2dicom', 'templates')
aseg_metadata_filename = 'fs-aseg.json'
sr_template_filename = 'fs-aseg-sr-template.json'
aseg_metadata = os.path.join(TEMPLATE_PATH, aseg_metadata_filename)
sr_template = os.path.join(TEMPLATE_PATH, sr_template_filename)

no_fs_license_message = 'Path to FreeSurfer License file is needed. Pass it with the --fs_license_key flag, or set the environment variable FS_LICENSE_KEY'

def run_docker_command(docker_image, command, volumes, environment, pull=False):
        client = docker.from_env()
        client.images.pull(ctx.obj['freesurfer_docker_image'])
        client.containers.run(ctx.obj['freesurfer_docker_image'], command=resample_aseg_command, volumes=resample_aseg_volume_dict, environment=resample_aseg_environment_dict)

def base64_convert(license_file):
    ...

def get_convert_t1_cmd(t1_dicom_file):
    ...
    
def get_resample_aseg_cmd(aseg_image_file, t1_dicom_file):
    convert_t1(t1_dicom_file)


def get_generate_dicom_seg_cmd(resampled_aseg, aseg_dicom_metadata, t1_dicom_dir, aseg_dicom_seg_output):
    ...


def get_convert_aseg_stats_cmd():
    ...


def generate_aseg_stats_json():
    """

    Use jinja2 template to fill in values, based on pdf-report code and
    https://gist.github.com/sevennineteen/4400462
    """
    ...
    env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))
    env.filters['jsonify'] = json.dumps
    template = env.get_template(sr_template_filename)

    template_vars = {
        "aseg_dcm": aseg_dcm,
    }

    aseg_stats_json = template.render(template_vars)

    return aseg_stats_json

def get_generate_dicom_sr_cmd():
    ...

# help messages:

dcmqi_type_help = 'Use docker or local installed version of dcmqi (default: docker)'
dcmqi_docker_image_help = 'Name of the dcmqi docker image (default: qiicr/dcmqi:latest)'
freesurfer_type_help = 'Use docker or local installed version of freesurfer (default: docker)'
freesurfer_docker_image_help = 'Name of the FreeSurfer docker image. Currently only supports corticometrics/fs6-base (default: corticometrics/fs6-base:latest)'
fs_license_key_help = 'Path to FreeSurfer License key file. (default: path set by environment variable FS_LICENSE_KEY)'
aseg_dicom_metadata_help = 'Path to the DICOM SEG metadata schema describing the aseg (default: provided within package)'
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
        if ctx.obj['fs_license_key'] == None:
            sys.exit(no_fs_license_message)
    elif ctx.obj['dcmqi_type'] == 'docker':
        import docker 



@click.command()
@click.argument('aseg_image_file', type=click.Path(exists=True))
@click.argument('aseg_dicom_seg_output', type=click.Path(), default='aseg.dcm')
@click.option('--aseg_dicom_metadata', '-m', type=click.Path(exists=True), default=aseg_metadata, help=aseg_dicom_metadata_help)
@click.option('--t1_dicom_file', '-d', type=click.Path(exists=True), help=t1_dicom_file_help)
@click.pass_context
def create_dicom_seg(ctx, aseg_image_file, aseg_dicom_seg_output, aseg_dicom_metadata, t1_dicom_file):
    """
    command to create `-e FS_KEY=...` input:
    base64 -w 1000 cat /home/ltirrell/local/freesurfer/license.txt
    """
    if ctx.obj['freesurfer_type'] == 'docker':
        client = docker.from_env()
        client.images.pull(ctx.obj['freesurfer_docker_image'])
        client.containers.run(ctx.obj['freesurfer_docker_image'], command=resample_aseg_command, volumes=resample_aseg_volume_dict, environment=resample_aseg_environment_dict)


    resample_aseg(aseg_image_file, t1_dicom_file, t1_dicom_dir)
    generate_dicom_seg(resampled_aseg, aseg_dicom_metadata, t1_dicom_dir, aseg_dicom_seg_output)


@click.command()
@click.argument('aseg_stats_file', type=click.Path(exists=True))
@click.argument('aseg_dicom_sr_output', default='aseg-sr.dcm')
@click.argument('aseg_dicom_seg_file', type=click.Path(), default='aseg.dcm')
@click.option('--aseg_dicom_metadata', '-m', type=click.Path(exists=True), default=aseg_metadata, help=aseg_dicom_metadata_help)
@click.option('--dicom_sr_template', '-t', type=click.Path(exists=True), default=sr_template, help=dicom_sr_template_help)
@click.option('--t1_dicom_file', '-d', type=click.Path(exists=True), help=t1_dicom_file_help)
@click.pass_context
def create_dicom_sr(aseg_stats_file, aseg_dicom_sr_output, aseg_dicom_seg_file, aseg_dicom_metadata, dicom_sr_template, t1_dicom_file):
    click.echo('fs type is: {}'.format(ctx.obj['freesurfer']['type']))
    ...
    # with tempfile.TemporaryDirectory() as tmpdirname:
    #     print('created temporary directory', tmpdirname)

cli.add_command(create_dicom_seg)
cli.add_command(create_dicom_sr)



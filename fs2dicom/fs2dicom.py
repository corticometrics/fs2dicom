import pkg_resources
import os
import tempfile

import click

import seg
import sr
import utils


CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help']}

TEMPLATE_PATH = pkg_resources.resource_filename('fs2dicom', 'templates')

aseg_metadata_filename = 'fs-aseg.json'
sr_template_filename = 'fs-aseg-sr-template.json'
aseg_metadata = os.path.join(TEMPLATE_PATH, aseg_metadata_filename)
sr_template = os.path.join(TEMPLATE_PATH, sr_template_filename)

# help messages:
dcmqi_type_help = '''\
Use docker or local installed version of dcmqi \
(default: docker)'''
dcmqi_docker_image_help = '''\
Name of the dcmqi docker image \
(default: qiicr/dcmqi:latest)'''
freesurfer_type_help = '''\
Use docker or local installed version of freesurfer \
(default: docker)'''
freesurfer_docker_image_help = '''\
Name of the FreeSurfer docker image. \
Currently only supports corticometrics/fs6-base \
(default: corticometrics/fs6-base:latest)'''
fs_license_key_help = '''\
Path to FreeSurfer License key file. \
(default: path set by environment variable FS_LICENSE_KEY)'''
aseg_dicom_seg_metadata_help = '''\
Path to the DICOM SEG metadata schema describing the aseg \
(default: provided within package)'''
t1_dicom_file_help = '''\
Path to one of the T1-weighted DICOM files processed with FreeSurfer to create the aseg.'''
dicom_sr_template_help = '''\
Path to DICOM SR template that is filled in with aseg.stats values \
(default: provided within package)'''


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--dcmqi_type',
              type=click.Choice(['docker', 'local']),
              default='docker',
              help=dcmqi_type_help)
@click.option('--dcmqi_docker_image',
              default='qiicr/dcmqi:latest',
              help=dcmqi_docker_image_help)
@click.option('--freesurfer_type',
              type=click.Choice(['docker', 'local']),
              default='docker',
              help=freesurfer_type_help)
@click.option('--freesurfer_docker_image',
              default='corticometrics/fs6-base:latest',
              help=freesurfer_docker_image_help)
@click.option('--fs_license_key',
              envvar='FS_LICENSE_KEY',
              help=fs_license_key_help)
@click.pass_context
def cli(ctx,
        dcmqi_type,
        dcmqi_docker_image,
        freesurfer_type,
        freesurfer_docker_image,
        fs_license_key):
    """
    Create DICOM Segmentation Image and Structured Report objects from FreeSurfer segmentations.

    Currently requires either docker OR FreeSurfer and dcmqi installed locally

    Docker is the default way to run FreeSurfer and dcmqi commands needed to create DICOM SEG/SR


    A FreeSurfer License key is required to run the docker image.
    This can be downloaded from: https://surfer.nmr.mgh.harvard.edu/registration.html

    FreeSurfer commands are used to resample the aseg to native space
    Future versions may remove this dependency
    """
    ctx.obj = ctx.params


@click.command()
@click.argument('t1_dicom_file',
                type=click.Path(exists=True))
@click.argument('aseg_image_file',
                type=click.Path(exists=True))
@click.argument('aseg_dicom_seg_output',
                type=click.Path(),
                default='./aseg.dcm')
@click.option('--aseg_dicom_seg_metadata', '-m',
              type=click.Path(exists=True),
              default=aseg_metadata,
              help=aseg_dicom_seg_metadata_help)
@click.pass_context
def create_seg(ctx,
               aseg_image_file,
               aseg_dicom_seg_output,
               aseg_dicom_seg_metadata,
               t1_dicom_file):
    """
    Creates a DICOM Segementation Image object from the T1_DICOM_FILE (one of
    the T1w DICOM files processed with FreeSurfer) and ASEG_IMAGE_FILE,
    and outputs to the ASEG_DICOM_SEG_OUTPUT file name (default: ./aseg.dcm)
    """
    ctx = utils.check_docker_and_license(ctx)

    with tempfile.TemporaryDirectory() as seg_temp_dir:
        resampled_aseg = os.path.join(seg_temp_dir,
                                      'aseg_native_space.nii.gz')

        resample_aseg_cmd = seg.get_resample_aseg_cmd(aseg_image_file,
                                                      t1_dicom_file,
                                                      resampled_aseg)
        generate_dicom_seg_cmd = seg.get_generate_dicom_seg_cmd(resampled_aseg,
                                                                aseg_dicom_seg_metadata,
                                                                t1_dicom_file,
                                                                aseg_dicom_seg_output)

    fs_commands = [resample_aseg_cmd]
    if ctx.obj['freesurfer_type'] == 'docker':
        utils.run_docker_commands(fs_commands)
    else:
        utils.run_local_commands(fs_commands)

    dcmqi_commands = [generate_dicom_seg_cmd]
    if ctx.obj['dcmqi_type'] == 'docker':
        utils.run_docker_commands(dcmqi_commands)
    else:
        utils.run_local_commands(dcmqi_commands)


@click.command()
@click.argument('t1_dicom_file',
                type=click.Path(exists=True))
@click.argument('aseg_stats_file',
                type=click.Path(exists=True))
@click.argument('aseg_dicom_seg_file',
                type=click.Path(),
                default='aseg.dcm')
@click.argument('aseg_dicom_sr_metadata_output',
                type=click.Path(),
                default='fs-aseg-sr.json')
@click.argument('aseg_dicom_sr_output',
                default='aseg-sr.dcm')
@click.option('--aseg_dicom_seg_metadata', '-m',
              type=click.Path(exists=True),
              default=aseg_metadata,
              help=aseg_dicom_seg_metadata_help)
@click.option('--dicom_sr_template', '-t',
              type=click.Path(exists=True),
              default=sr_template,
              help=dicom_sr_template_help)
@click.pass_context
def create_sr(ctx,
              aseg_stats_file,
              aseg_dicom_seg_file,
              aseg_dicom_sr_metadata,
              aseg_dicom_sr_output,
              aseg_dicom_seg_metadata,
              dicom_sr_template,
              t1_dicom_file):
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
    ctx = utils.check_docker_and_license(ctx)

    fs_commands = []
    if ctx.obj['freesurfer_type'] == 'docker':
        utils.run_docker_commands(fs_commands)
    else:
        utils.run_local_commands(fs_commands)

    dcmqi_commands = []
    if ctx.obj['dcmqi_type'] == 'docker':
        utils.run_docker_commands(dcmqi_commands)
    else:
        utils.run_local_commands(dcmqi_commands)


cli.add_command(create_seg)
cli.add_command(create_sr)

import pkg_resources
import os
import tempfile

import click

from fs2dicom import seg
from fs2dicom import sr
from fs2dicom import utils


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
seg_metadata_help = '''\
Path to the DICOM SEG metadata schema describing the aseg \
(default: provided within package)'''
t1_dicom_file_help = '''\
Path to one of the T1-weighted DICOM files processed with FreeSurfer to create the aseg.'''
sr_template_help = '''\
Path to DICOM SR template that is filled in with aseg.stats values \
(default: provided within package)'''
aseg_dicom_seg_file_help = '''\
DICOM SEG of the aseg, for example created by `fs2dicom create-seg` \
(default: ./aseg.dcm)'''
sr_metadata_output_help = '''\
JSON file output containing the values used to create the DICOM SR \
(default: ./fs-aseg-sr.json)
'''


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
                type=click.Path(exists=True, resolve_path=True))
@click.argument('aseg_image_file',
                type=click.Path(exists=True, resolve_path=True))
@click.argument('aseg_dicom_seg_output',
                type=click.Path(),
                default=os.path.join(os.getcwd(), 'aseg.dcm'))
@click.option('--seg_metadata',
              type=click.Path(exists=True, resolve_path=True),
              default=aseg_metadata,
              help=seg_metadata_help)
@click.pass_context
def create_seg(ctx,
               t1_dicom_file,
               aseg_image_file,
               aseg_dicom_seg_output,
               seg_metadata):
    """
    Creates a DICOM Segementation Image object from the T1_DICOM_FILE (one of
    the T1w DICOM files processed with FreeSurfer) and ASEG_IMAGE_FILE,
    and outputs to the ASEG_DICOM_SEG_OUTPUT file name (default: ./aseg.dcm)
    """
    ctx = utils.check_docker_and_license(ctx)

    # make sure any tilde in path names are resolved
    t1_dicom_file = os.path.expanduser(t1_dicom_file)
    aseg_image_file = os.path.expanduser(aseg_image_file)
    aseg_dicom_seg_output = os.path.expanduser(aseg_dicom_seg_output)
    seg_metadata = os.path.expanduser(seg_metadata)

    docker_user_string = utils.get_docker_user(aseg_image_file)

    with tempfile.TemporaryDirectory() as seg_temp_dir:
        print('[fs2dicom] Running create-seg with {temp_dir} as tempdir\n'.format(temp_dir=seg_temp_dir))
        resampled_aseg = os.path.join(seg_temp_dir,
                                      'aseg_native_space.nii.gz')
        t1_dicom_dir = utils.abs_dirname(t1_dicom_file)
        docker_user_string = utils.get_docker_user(aseg_image_file)

        resample_aseg_cmd = seg.get_resample_aseg_cmd(aseg_image_file,
                                                      t1_dicom_file,
                                                      resampled_aseg)
        generate_dicom_seg_cmd = seg.get_generate_dicom_seg_cmd(resampled_aseg,
                                                                seg_metadata,
                                                                t1_dicom_file,
                                                                aseg_dicom_seg_output)

        fs_commands = [resample_aseg_cmd]
        if ctx.obj['freesurfer_type'] == 'docker':
            """
            Inputs (ro):
                t1_dicom_dir
                aseg_image_file
            Output directories (rw):
                seg_temp_dir
            """
            volumes_dict = {t1_dicom_dir: {'bind': t1_dicom_dir,
                                           'mode': 'ro'},
                            aseg_image_file: {'bind': aseg_image_file,
                                              'mode': 'ro'},
                            seg_temp_dir: {'bind': seg_temp_dir,
                                           'mode': 'rw'}}

            environment_dict = {'FS_KEY': utils.base64_convert(ctx.obj['fs_license_key'])}

            utils.run_docker_commands(docker_image=ctx.obj['freesurfer_docker_image'],
                                      commands=fs_commands,
                                      volumes=volumes_dict,
                                      user='root',  # corticometrics/fs6-base needs to be root
                                      environment=environment_dict,
                                      working_dir=seg_temp_dir)
        else:
            utils.run_local_commands(fs_commands)

        dcmqi_commands = [generate_dicom_seg_cmd]
        if ctx.obj['dcmqi_type'] == 'docker':
            """
            Inputs (ro):
                resampled_aseg
                seg_metadata
                t1_dicom_dir
            Output directories (rw):
                aseg_dicom_seg_output directrory (output dir)
            """
            output_dir = utils.abs_dirname(aseg_dicom_seg_output)
            volumes_dict = {resampled_aseg: {'bind': resampled_aseg,
                                             'mode': 'ro'},
                            seg_metadata: {'bind': seg_metadata,
                                           'mode': 'ro'},
                            t1_dicom_dir: {'bind': t1_dicom_dir,
                                           'mode': 'ro'},
                            output_dir: {'bind': output_dir,
                                         'mode': 'rw'}}

            utils.run_docker_commands(docker_image=ctx.obj['dcmqi_docker_image'],
                                      commands=dcmqi_commands,
                                      volumes=volumes_dict,
                                      user=docker_user_string,
                                      working_dir=output_dir)
        else:
            utils.run_local_commands(dcmqi_commands)


@click.command()
@click.argument('t1_dicom_file',
                type=click.Path(exists=True, resolve_path=True))
@click.argument('aseg_stats_file',
                type=click.Path(exists=True, resolve_path=True))
@click.argument('aseg_dicom_sr_output',
                default=os.path.join(os.getcwd(), 'aseg-sr.dcm'))
@click.option('--aseg_dicom_seg_file',
              type=click.Path(exists=True, resolve_path=True),
              default=os.path.join(os.getcwd(), 'aseg.dcm'),
              help=aseg_dicom_seg_file_help)
@click.option('--sr_metadata_output',
              type=click.Path(resolve_path=True),
              default=os.path.join(os.getcwd(), 'fs-aseg-sr.json'),
              help=sr_metadata_output_help)
@click.option('--seg_metadata',
              type=click.Path(exists=True, resolve_path=True),
              default=aseg_metadata,
              help=seg_metadata_help)
@click.option('--sr_template',
              type=click.Path(exists=True, resolve_path=True),
              default=sr_template,
              help=sr_template_help)
@click.pass_context
def create_sr(ctx,
              t1_dicom_file,
              aseg_stats_file,
              aseg_dicom_sr_output,
              aseg_dicom_seg_file,
              sr_metadata_output,
              seg_metadata,
              sr_template):
    """
    Creates a DICOM Structured Report object ASEG_DICOM_SR_OUTPUT (default:
    ./aseg-sr.dcm) using the values from the ASEG_STATS_FILE created by
    FreeSurfer. The T1_DICOM_FILE (one of the T1w DICOM files processed with
    FreeSurfer) and aseg_dicom_seg_file (default: ./aseg.dcm, specified with
    --aseg_dicom_seg_file) are needed to provide context for this DICOM SR.
    sr_metadata_output is also created (default: ./fs-aseg-sr.json, specified
    with --sr_metadata_output), containing the values used to create the DICOM SR.
    """
    ctx = utils.check_docker_and_license(ctx)

    # make sure any tilde in path names are resolved
    t1_dicom_file = os.path.expanduser(t1_dicom_file)
    aseg_stats_file = os.path.expanduser(aseg_stats_file)
    aseg_dicom_sr_output = os.path.expanduser(aseg_dicom_sr_output)
    aseg_dicom_seg_file = os.path.expanduser(aseg_dicom_seg_file)
    sr_metadata_output = os.path.expanduser(sr_metadata_output)
    seg_metadata = os.path.expanduser(seg_metadata)
    sr_template = os.path.expanduser(sr_template)

    docker_user_string = utils.get_docker_user(aseg_stats_file)

    sr.generate_aseg_dicom_sr_metadata(sr_template,
                                       seg_metadata,
                                       aseg_dicom_seg_file,
                                       t1_dicom_file,
                                       sr_metadata_output,
                                       aseg_stats_file)

    generate_dicom_sr_cmd = sr.get_generate_dicom_sr_cmd(t1_dicom_file,
                                                         aseg_dicom_seg_file,
                                                         aseg_dicom_sr_output,
                                                         sr_metadata_output)

    print('[fs2dicom] Running create-sr\n')

    dcmqi_commands = [generate_dicom_sr_cmd]
    if ctx.obj['dcmqi_type'] == 'docker':
        """
        Inputs (ro):
            t1_dicom_dir
            aseg_dicom_dir
            aseg_dicom_sr_metadata
        Output directories (rw):
            aseg_dicom_sr_output directory (output dir)
        """
        t1_dicom_dir = utils.abs_dirname(t1_dicom_file)
        aseg_dicom_dir = utils.abs_dirname(aseg_dicom_seg_file)
        output_dir = utils.abs_dirname(aseg_dicom_sr_output)

        volumes_dict = {t1_dicom_dir: {'bind': t1_dicom_dir,
                                       'mode': 'ro'},
                        aseg_dicom_dir: {'bind': aseg_dicom_dir,
                                         'mode': 'ro'},
                        sr_metadata_output: {'bind': sr_metadata_output,
                                             'mode': 'ro'},
                        output_dir: {'bind': output_dir,
                                     'mode': 'rw'}}

        utils.run_docker_commands(docker_image=ctx.obj['dcmqi_docker_image'],
                                  commands=dcmqi_commands,
                                  volumes=volumes_dict,
                                  user=docker_user_string,
                                  working_dir=output_dir)

    else:
        utils.run_local_commands(dcmqi_commands)


cli.add_command(create_seg)
cli.add_command(create_sr)

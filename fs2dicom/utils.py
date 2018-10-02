import base64
import distutils
import os
import shlex
import subprocess
import sys

import docker


no_docker_message = '''\
docker not available on your system.
either install docker (https://docs.docker.com/install/),
or run FreeSurfer/dcmqi commands locally (using the "local" option)'''

no_fs_license_message = '''\
Path to FreeSurfer License file is needed!
Pass it with the --fs_license_key flag, \
or set the environment variable FS_LICENSE_KEY'''


# basic defs
def check_for_docker():
    docker_available = distutils.spawn.find_executable('docker')
    if not docker_available:
        sys.exit(no_docker_message)


def check_docker_and_license(context):
    if context.obj['freesurfer_type'] == 'docker':
        check_for_docker()
        if context.obj['fs_license_key'] is None:
            sys.exit(no_fs_license_message)
        else:
            fs_license_var = base64_convert(context.obj['fs_license_key'])
            context.obj['fs_license_var'] = fs_license_var

    if context.obj['dcmqi_type'] == 'docker':
        check_for_docker()

    return context


def get_docker_user(file):
    uid = str(os.getuid())
    gid = str(os.stat(file).st_gid)

    return ':'.join([uid, gid])


def run_docker_commands(docker_image,
                        commands,
                        volumes,
                        user,
                        environment=None,
                        working_dir=os.getcwd(),
                        pull=False):
    client = docker.from_env()

    if pull:
        client.images.pull(docker_image)
    for command in commands:
        print('[RunningCommand] {command}\n'.format(command=command))
        container = client.containers.run(docker_image,
                                          command=shlex.split(command),
                                          volumes=volumes,
                                          environment=environment,
                                          user=user,
                                          working_dir=working_dir)
        log = container.decode('utf-8')
        for i in log.split('\n'):
            print(i)
        print('--------')
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


def abs_dirname(file):
    return os.path.dirname(os.path.abspath(os.path.expanduser(file)))

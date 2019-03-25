'''
ssh.py

Contains wrappers around paramiko ssh sessions.
'''

# Imported Modules
import os
import logging
from paramiko.client import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import AuthenticationException, BadHostKeyException, SSHException
import sys

# Global & Default Settings
ALLOW_AGENT = False
AUTH_TIMEOUT = None
BANNER_TIMEOUT = None
CERT = None
COMMAND_TIMEOUT = None
COMPRESS = False
LOOK_FOR_KEYS = False
PASSWORD = None
PORT = 22
SH_FILE = '/tmp/reftmp.sh'
TIMEOUT = None
USER = ''

# Disable annoying paramiko messages
logging.getLogger('paramiko').setLevel(1000)

# ---------- Private Functions ----------

# ---------- Public Functions ----------

def command(client, cmd):
    '''
    Executes the specified command on the remote server.
    '''
    i, o, e = client.exec_command(cmd, timeout=COMMAND_TIMEOUT, get_pty=True)
    i.close()
    e.close()
    return o


def connect(host, port=PORT, user=USER, password=PASSWORD, cert=CERT):
    '''
    Creates a new `paramiko.client.SSHClient` connection, returning the created
    object.
    '''
    try:
        client = SSHClient()
    except Exception as e:
        raise Exception('Unable to create client object - ' + str(e))
    try:
        client.set_missing_host_key_policy(AutoAddPolicy())
    except Exception as e:
        raise Exception('Unable to set missing host key policy of client object - ' + str(e))
    try:
        client.connect(
            host,
            port = port,
            username = user,
            password = password,
            key_filename = cert,
            timeout = TIMEOUT,
            allow_agent = ALLOW_AGENT,
            look_for_keys = LOOK_FOR_KEYS,
            compress = COMPRESS,
            banner_timeout = BANNER_TIMEOUT,
            auth_timeout = AUTH_TIMEOUT
        )
    except AuthenticationException as e:
        raise Exception('Unable to authenticate with remote server - ' + str(e))
    except BadHostKeyException as e:
        raise Exception('Unable to verify host key of remote server - ' + str(e))
    except SSHException as e:
        raise Exception('Unable to establish ssh connection to remote server - ' + str(e))
    except Exception as e:
        raise Exception('Unable to connect to remote server - ' + str(e))
    return client


def write_to_file(client, file_path, contents, executable=True):
    '''
    Writes the specified contents to the specified file path on the given
    client.
    '''
    try:
        sftp = client.open_sftp()
    except Exception as e:
        raise Exception('Unable to initialize SFTP client - ' + str(e))
    try:
        with sftp.open(file_path, 'w') as f:
            f.write(contents)
    except Exception as e:
        raise Exception('Unable to write file on remote host - ' + str(e))
    if executable:
        try:
            sftp.chmod(file_path, 0o755)
        except Exception as e:
            raise Exception('Unable to set executable bit on remote file - ' + str(e))


def run_task(client, incommand, argv=[]):
    '''
    Executes the specified command on the given client as a task.
    '''
    full_command  = '#!/bin/bash\n'
    full_command += '# Temporary file written by Harrison\'s "remote execution framework"\n'
    full_command += 'set -e\n'
    full_command += 'sleep 0.1\n\n'
    full_command += incommand + '\n'
    try:
        write_to_file(client, SH_FILE, full_command)
    except Exception as e:
        raise e
    if argv:
        run_command = SH_FILE + ' ' + ' '.join(argv)
    else:
        run_command = SH_FILE
    return command(client, run_command)

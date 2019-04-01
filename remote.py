#!/bin/env python3
'''
remote

The main script of the remote execution framework.
'''

# ------- Python Library Imports -------

# Standard Libraries
import argparse
import getpass
import glob
import itertools
import logging
import multiprocessing as mp
import os
import re
import shutil
import socket
import subprocess
import sys
import time

# Additional Libraries
try:
    import paramiko
except ImportError as IE:
    sys.exit('Unable to import paramiko library - ' + str(IE))
try:
    import yaml
except ImportError as IE:
    sys.exit('Unable to import PyYAML library - ' + str(IE))
    
# Custom Modules
try:
    import lib.io as io
    import lib.parser as parser
    import lib.ssh as ssh
except ImportError as IE:
    sys.exit('Unable to import supporting libraries - ' + str(IE))

# --------------------------------------



# ----------- Initialization -----------

HELP_DESCRIPTION = """
A simple remote execution framework.
"""

HELP_EPILOG = """

----- Environment Variables -----

The following maps each available environment variable with its corresponding CLI argument:

REMOTE_AUTH_TIMEOUT     :  --auth-timeout
REMOTE_CERT             :  --cert
REMOTE_COMMAND_TIMEOUT  :  --command-timeout
REMOTE_CONFIG_FILE      :  --config-file
REMOTE_LOG_FILE         :  --log-file
REMOTE_LOG_LEVEL        :  --log-level
REMOTE_LOG_MODE         :  --log-mode
REMOTE_PASSWORD         :  --password
REMOTE_PORT             :  --port
REMOTE_TIMEOUT          :  --timeout
REMOTE_USER             :  --user
"""

# Color Sequences
C_BLUE   = '\033[94m'
C_GREEN  = '\033[92m'
C_ORANGE = '\033[93m'
C_RED    = '\033[91m'
C_END    = '\033[0m'
C_BOLD   = '\033[1m'

# --------------------------------------



# ---------- Private Functions ---------

def _parse_arguments():
    '''
    Parses the command-line arguments into a global namespace called "args".
    '''
    # Do some pre-parsing for some of the environment variables to prevent crashes
    if not os.getenv('REMOTE_LOG_LEVEL', 'info') in ['info', 'debug']:
        sys.exit('Invalid value set for environment variable "REMOTE_LOG_LEVEL".')
    if not os.getenv('REMOTE_LOG_MODE', 'append') in ['append', 'overwrite']:
        sys.exit('Invalid value set for environment variable "REMOTE_LOG_MODE".')
    if not os.getenv('REMOTE_AUTH_TIMEOUT', '5').isdigit():
        sys.exit('Invalid value set for environment variable "REMOTE_AUTH_TIMEOUT".')
    if not os.getenv('REMOTE_COMMAND_TIMEOUT', '0').isdigit():
        sys.exit('Invalid value set for environment variable "REMOTE_COMMAND_TIMEOUT".')
    if not os.getenv('REMOTE_TIMEOUT', '5').isdigit():
        sys.exit('Invalid value set for environment variable "REMOTE_TIMEOUT".')
    if not os.getenv('REMOTE_PORT', '22').isdigit():
        sys.exit('Invalid value set for environment variable "REMOTE_PORT".')
    argparser = argparse.ArgumentParser(
        description = HELP_DESCRIPTION,
        epilog = HELP_EPILOG,
        usage = 'remote SERVERS/TARGETS [FLAGS/OPTIONS] (-c COMMAND | -C | -r TASK)',
        add_help = False,
        formatter_class = lambda prog: argparse.RawDescriptionHelpFormatter(prog, max_help_position=45, width=100)
    )
    if not '--list-targets' in sys.argv and not '--list-tasks' in sys.argv:
        argparser.add_argument(
            'targets',
            nargs = '+',
            help = 'Specifies the target server(s) to connect to.',
        )
    argparser.add_argument(
        '--auth-timeout',
        default = int(os.getenv('REMOTE_AUTH_TIMEOUT', '5')),
        dest = 'auth_timeout',
        help = 'Specifies the remote authentication and banner timeout, in seconds. Defaults to 5 seconds. Set to "0" to disable the timeout.',
        metavar = 'SEC',
        type = int
    )
    argparser.add_argument(
        '--cert',
        default = os.getenv('REMOTE_CERT', ''),
        dest = 'cert',
        help = 'Specifies a default certificate file to use when authenticating with remote servers.',
        metavar = 'FILE'
    )
    argparser.add_argument(
        '-c',
        '--command',
        default = '',
        dest = 'command',
        help = 'Executes the specified command on the specified target server(s).',
        metavar = 'CMD'
    )
    argparser.add_argument(
        '-T',
        '--command-timeout',
        default = int(os.getenv('REMOTE_COMMAND_TIMEOUT', '0')),
        dest = 'command_timeout',
        help = 'Specifies the timeout in waiting for remote commands to complete, in seconds. Defaults to "0" (no timeout).',
        metavar = 'SEC',
        type = int
    )
    argparser.add_argument(
        '--compress',
        action = 'store_true',
        dest = 'compress',
        help = 'Enables compression of the communication with remote servers.'
    )
    argparser.add_argument(
        '-y',
        '--config-file',
        default = os.getenv('REMOTE_CONFIG_FILE', os.path.expanduser('~/remote.yaml')),
        dest = 'config_file',
        help = 'Specifies the primary remote framework configuration file to load. Defaults to "~/remote.yaml"',
        metavar = 'FILE'
    )
    argparser.add_argument(
        '-C',
        '--console',
        action = 'store_true',
        dest = 'console',
        help = 'Opens an interactive console with the specified target server(s).'
    )
    argparser.add_argument(
        '-d',
        '--dry-run',
        action = 'store_true',
        dest = 'dry_run',
        help = 'Specifies that the script should only execute a dry-run. This is typically used to test connectivity.'
    )
    argparser.add_argument(
        '-h',
        '--help',
        action = 'help',
        help = 'Displays help and usage information.'
    )
    argparser.add_argument(
        '--list-targets',
        action = 'store_true',
        dest = 'list_targets',
        help = 'Lists the available targets.'
    )
    argparser.add_argument(
        '--list-tasks',
        action = 'store_true',
        dest = 'list_tasks',
        help = 'Lists the available tasks.'
    )
    argparser.add_argument(
        '-f',
        '--log-file',
        default = os.getenv('REMOTE_LOG_FILE', os.path.expanduser('~/remote.log')),
        dest = 'log_file',
        help = 'Specifies a log file to write to in addition to stdout/stderr. Defaults to "~/remote.log".',
        metavar = 'FILE'
    )
    argparser.add_argument(
        '-l',
        '--log-level',
        choices = ['info', 'debug'],
        default = os.getenv('REMOTE_LOG_LEVEL', 'info'),
        dest = 'log_level',
        help = 'Specifies the log level of the script, being either "info" or "debug". Defaults to "info".',
        metavar = 'LVL'
    )
    argparser.add_argument(
        '-m',
        '--log-mode',
        choices = ['append', 'overwrite'],
        default = os.getenv('REMOTE_LOG_MODE', 'append'),
        dest = 'log_mode',
        help = 'Specifies whether to "append" or "overwrite" the specified log file. Defaults to "append".',
        metavar = 'MODE'
    )
    argparser.add_argument(
        '--no-color',
        action = 'store_false',
        dest = 'color_output',
        help = 'Disables color output to stdout/stderr.'
    )
    argparser.add_argument(
        '-o',
        '--output-only',
        action = 'store_true',
        default = not sys.stdout.isatty(),
        dest = 'output_only',
        help = 'Instructs the script to only output data from the remote execution process itself. This is automatically selected when redirecting the script to a file.'
    )
    argparser.add_argument(
        '-P',
        '--parallel',
        action = 'store_true',
        dest = 'parallel',
        help = 'Specifies that the remote commands should be executed in parallel.'
    )
    argparser.add_argument(
        '-p',
        '--password',
        const = 'DEFAULT',
        default = os.getenv('REMOTE_PASSWORD', ''),
        dest = 'password',
        help = 'Specifies the default password to use when connecting to remote hosts. If this option is supplied without specifying a value, the user will be prompted to enter a password.',
        metavar = 'STR',
        nargs = '?'
    )
    argparser.add_argument(
        '--port',
        default = int(os.getenv('REMOTE_PORT', '22')),
        dest = 'port',
        help = 'Specifies the default port to use when connecting to remote hosts. Defaults to port 22.',
        metavar = 'PORT',
        type = int
    )
    argparser.add_argument(
        '-r',
        '--run',
        default = '',
        dest = 'run',
        help = 'Executes the specified task on the specified target server(s).',
        metavar = 'TASK [ARGS]'
    )
    argparser.add_argument(
        '-t',
        '--timeout',
        default = int(os.getenv('REMOTE_TIMEOUT', '5')),
        dest = 'timeout',
        help = 'Specifies the general timeout for all remote connections, in seconds. Defaults to 5 seconds. Set to "0" to disable the timeout.',
        metavar = 'SEC',
        type = int
    )
    argparser.add_argument(
        '-u',
        '--user',
        default = os.getenv('REMOTE_USER', getpass.getuser()),
        dest = 'user',
        help = 'Specifies the default user to use when connecting to remote hosts. Defaults to the current executing user.',
        metavar = 'USR'
    )
    global args
    args = argparser.parse_args()


# --------------------------------------



# ---------- Public Functions ----------


def connect():
    '''
    Connects to the various target servers, storing the conections into a global
    dictionary mapped by hostname.
    '''
    EC = 7
    printed = False
    logging.debug('Connecting to remote hosts...')
    global connections
    connections = {}
    for t in targets:
        if t != 'other':
            logging.debug('Connecting to hosts in "' + t + '" target...')
            if 'user' in config['targets'][t]:
                user = config['targets'][t]['user']
            else:
                user = args.user
            logging.debug('Connection User: ' + user)
            if 'port' in config['targets'][t]:
                port = config['targets'][t]['port']
            else:
                port = args.port
            logging.debug('Connection Port: ' + str(port))
            if 'cert' in config['targets'][t]:
                cert = config['targets'][t]['cert']
                logging.debug('Connection Cert: ' + cert)
            elif args.cert:
                cert = args.cert
                logging.debug('Connection Cert: ' + cert)
            else:
                cert = None
                logging.debug('Connection Cert: [not present]')
            if 'password' in config['targets'][t]:
                password = config['targets'][t]['password']
                logging.debug('Connection Password: [present]')
            elif args.password:
                password = args.password
                logging.debug('Connection Password: [present]')
            else:
                password = None
                logging.debug('Connection Password: [not present]')
        else:
            user = args.user
            logging.debug('Connection User: ' + user)
            port = args.port
            logging.debug('Connection Port: ' + str(port))
            if args.cert:
                cert = args.cert
                logging.debug('Connection Cert: ' + cert)
            else:
                cert = None
                logging.debug('Connection Cert: [not present]')
            if args.password:
                password = args.password
                logging.debug('Connection Password: [present]')
            else:
                password = None
                logging.debug('Connection Password: [not present]')   
        for h in targets[t]:
            logging.debug('Connecting to "' + h + '"...')
            try:
                client = ssh.connect(
                    h,
                    port = port,
                    user = user,
                    password = password,
                    cert = cert
                )
            except Exception as e:
                if not printed:
                    io.write(io.bold('Connecting to remote hosts...'), 1, '')
                    printed = True
                io.write(h, 3, '')
                io.write(io.red(str(e)), 4, 'err')
                continue
            connections[h] = client


def disconnect():
    '''
    Disconnects from the various target servers.
    '''
    EC = 9
    printed = False
    logging.debug('Disconnecting from remote hosts...')
    for h in connections:
        logging.debug('Disconnecting from "' + h + '"...')
        try:
            connections[h].close()
        except Exception as e:
            if not printed:
                io.write(io.bold('Disconnecting from remote hosts...'), 1, '')
                printed = True
            io.write(h, 3, '')
            io.write(io.red('Unable to close connection - ' + str(e)), 4, 'err')
            continue


def load_config():
    '''
    Loads the specified primary configuration file into a global dictionary
    called "config".
    '''
    EC = 3
    logging.debug('Reading configuration file...')
    try:
        with open(args.config_file, 'r') as f:
            raw_config = f.read()
    except Exception as e:
        io.write(io.red('Unable to read configuration file - ' + str(e)), 2, 'cri')
        sys.exit(EC)
    logging.debug('Parsing configuration file...')
    try:
        global config
        config = yaml.load(raw_config)
    except Exception as e:
        io.write(io.red('Unable to parse configuration file - ' + str(e)), 2, 'cri')
        sys.exit(EC)


def handle_command():
    '''
    Handles the --command action.
    '''
    EC = 8
    io.write(io.bold('Executing specified command...'), 1, 'inf')
    global task
    task = args.command
    global argv
    argv = []
    if args.parallel:
        global lock
        lock = mp.Lock()
        c_keys = list(connections.keys())
        p = mp.Pool(4)
        results = p.imap(connection_run, c_keys)
        p.close()
        p.join()
        logging.debug('RESULTS: ' + str(results))
        if False in results:
            sys.exit(EC)
    else:
        for h in connections: connection_run(h)


def handle_console():
    '''
    Handle the --console action.
    '''
    EC = 8


def handle_list_targets():
    '''
    Handles the --list-targets flag.
    '''
    try:
        with open(args.config_file, 'r') as f:
            targets = yaml.load(f.read())['targets']
        longest = max(map(len, targets))
        for t in targets:
            print(t + (' ' * (longest - len(t))) + '  :  ' + ', '.join(targets[t]['hosts']))
    except: sys.exit(1)
    sys.exit(0)


def handle_list_tasks():
    '''
    Handles the --list-tasks flag.
    '''
    try:
        with open(args.config_file, 'r') as f:
            tasks = yaml.load(f.read())['tasks']
        longest = max(map(len, tasks))
        for t in tasks:
            if 'desc' in tasks[t]:
                print(t + (' ' * (longest - len(t))) + '  :  ' + tasks[t]['desc'])
            else:
                print(t + (' ' * (longest - len(t))) + '  :  (no description)')
    except: sys.exit(1)
    sys.exit(0)
    

def handle_run():
    '''
    Handle the --run action.
    '''
    EC = 8
    io.write(io.bold('Running ' + args.run + '...'), 1, 'inf')
    global task
    global argv
    if ' ' in args.run:
        spl = args.run.split(' ', 1)
        task = spl[0]
        argv = spl[1]
    else:
        task = args.run
        argv = ''
    if args.parallel:
        c_keys = list(connections.keys())
        p = mp.Pool(4)
        results = p.imap(connection_run, c_keys)
        p.close()
        p.join()
        logging.debug('RESULTS: ' + str(results))
        if False in results:
            sys.exit(EC)
    else:
        for h in connections: connection_run(h)
    

def main():
    '''
    The entrypoint of the script.
    '''
    # Parse command-line arguments
    _parse_arguments()

    # Handle --list-targets or --list-tasks
    if args.list_targets: handle_list_targets()
    if args.list_tasks: handle_list_tasks()

    # Prepare IO
    io.COLOR_ENABLED = args.color_output
    io.OUTPUT_ONLY = args.output_only
    io.setup_logging(args.log_file, args.log_mode, args.log_level)

    # Log CLI arguments at the DEBUG level
    logging.debug('----- CLI Arguments -----')
    dargs = vars(args)
    for a in dargs:
        logging.debug(a + ' : ' + str(dargs[a]))
    logging.debug('-------------------------')

    # Get a password if necessary
    if args.password == 'DEFAULT':
        if args.output_only:
            sys.exit('Error: "-P"/"--password" prompts are not supported when running the script in output-only mode.')
        else:
            args.password = getpass.getpass('Enter Connection Password: ')

    # Perpare for execution
    logging.debug('Preparing working environment...')
    validate_environment()
    load_config()
    validate_config()
    parse_targets()
    validate_selected_targets()
    validate_selected_task()

    # Prepare SSH
    if args.auth_timeout > 0:
        ssh.AUTH_TIMEOUT = args.auth_timeout
        ssh.BANNER_TIMEOUT = args.auth_timeout
    if args.cert: ssh.CERT = args.cert
    if args.command_timeout > 0: ssh.COMMAND_TIMEOUT = args.command_timeout
    ssh.COMPRESS = args.compress
    if args.password: ssh.PASSWORD = args.password
    ssh.PORT = args.port
    if args.timeout > 0: ssh.TIMEOUT = args.timeout
    ssh.USER = args.user

    # Connect to the target servers
    connect()

    # Handle the general process
    if args.command:
        handle_command()
    elif args.console:
        handle_console()
    elif args.run:
        handle_run()

    # Disconnect from the target servers
    disconnect()

    # We are done
    sys.exit(0)


def parse_targets():
    '''
    Parses the specified targets into a dictionary containing the _actual_
    list of corresponding hosts.
    '''
    EC = 5
    logging.debug('Parsing specified targets...')
    global targets
    targets = {'other':[]}
    for t in args.targets:
        if not t in config['targets']:
            try:
                targets['other'].extend(parser.parse_host_str(t))
            except Exception as e:
                io.write(io.red('Unable to parse ') + io.bold(t) + io.red(' as host specification - ' + str(e)), 2, 'cri')
                sys.exit(EC)
        else:
            targets[t] = []
            for h in config['targets'][t]['hosts']:
                try:
                    targets[t].extend(parser.parse_host_str(h))
                except Exception as e:
                    io.write(io.red('Unable to parse host specification ') + io.bold(h) + io.red(' for target ') + io.bold(t) + io.red(' - ' + str(e)), 2, 'cri')
                    sys.exit(EC)
    logging.debug('Parsed Target Dictionary: ' + str(targets))


def connection_run(host):
    '''
    Represents an iteration of a running process, returning whether the command was a success.
    '''
    if args.parallel:
        if args.run:
            logging.debug('Executing parallel task "' + task + '" with arguments ' + argv + ' on "' + host + '"...')
            true_command = config['tasks'][task]['cmd']
        else:
            logging.debug('Executing parallel command "' + task + '" on "' + host + '"...')
            true_command = task
        try:
            stdout = ssh.run_task(connections[host], true_command, argv)
            output = stdout.read().splitlines()
            ec = stdout.channel.recv_exit_status()
            stdout.close()
        except Exception as e:
            logging.critical('Unable to execute command(s) on host "' + host + '" - ' + str(e))
            logging.debug(host + ' | Waiting for thread lock...')
            lock.acquire()
            logging.debug(host + ' | Acquired thread lock...')
            io.write(host, 3, '')
            io.write(io.red('Unable to execute command(s) - ' + str(e)), 4, '')
            logging.debug(host + ' | Flushing stdout/stderr...')
            sys.stdout.flush()
            sys.stderr.flush()
            logging.debug(host + ' | Releasing thread lock...')
            lock.release()
            logging.debug(host + ' | Released thread lock...')
            return False
        logging.debug(host + ' | Waiting for thread lock...')
        lock.acquire()
        logging.debug(host + ' | Acquired thread lock...')
        io.write(host, 3, '')
        if output:
            for l in output:
                logging.info(host + ' : ' + l)
                if args.output_only:
                    print(host + ' : ' + l)
                else:
                    io.write(l, 4, '')
        if args.output_only:
            print(host + ' < ' + str(ec))
        if ec != 0:
            logging.error(host + ' < ' + str(ec))
            io.write(io.red('Error: Remote execution returned non-zero exit code.'), 4, 'err')
            logging.debug(host + ' | Flushing stdout/stderr...')
            sys.stdout.flush()
            sys.stderr.flush()
            logging.debug(host + ' | Releasing thread lock...')
            lock.release()
            logging.debug(host + ' | Released thread lock...')
            return False
        else:
            logging.debug(host + ' < ' + str(ec))
            logging.debug(host + ' | Flushing stdout/stderr...')
            sys.stdout.flush()
            sys.stderr.flush()
            logging.debug(host + ' | Releasing thread lock...')
            lock.release()
            logging.debug(host + ' | Released thread lock...')
            return True
    else:
        io.write(host, 3, '')
        if args.run:
            logging.debug('Executing task "' + task + '" with arguments ' + argv + ' on "' + host + '"...')
            true_command = config['tasks'][task]['cmd']
        else:
            logging.debug('Executing command "' + task + '" on "' + host + '"...')
            true_command = task
        try:
            stdout = ssh.run_task(connections[host], true_command, argv)
            for l in iter(stdout.readline, ''):
                logging.info(host + ' : ' + l.rstrip())
                if args.output_only:
                    print(host + ' : ' + l.rstrip())
                else:
                    io.write(l.rstrip(), 4, '')
            ec = stdout.channel.recv_exit_status()
            stdout.close()
        except Exception as e:
            io.write(io.red('Unable to execute command(s) - ' + str(e)), 4, '')
            logging.critical('Unable to execute command(s) on host "' + host + '" - ' + str(e))
            return False
        if args.output_only:
            print(host + ' < ' + str(ec))
        if ec != 0:
            logging.error(host + ' < ' + str(ec))
            io.write(io.red('Error: Remote execution returned non-zero exit code.'), 4, 'err')
            return False
        else:
            logging.debug(host + ' < ' + str(ec))
            return True


def validate_config():
    '''
    Validates the parsed configuration file contents.
    '''
    EC = 4
    logging.debug('Validating configuration file contents...')
    if 'targets' in config:
        logging.debug('Validating "targets" key...')
        if not isinstance(config['targets'], dict):
            io.write(io.bold('Preparing working environment...'), 1, '')
            io.write(io.red('Unable to validate "targets" key - key not mapped to dictionary of target specifications.'), 2, 'cri')
            sys.exit(EC)
        for t in config['targets']:
            logging.debug('Validating "' + t + '" target specification...')
            if not isinstance(config['targets'][t], dict):
                io.write(io.bold('Preparing working environment...'), 1, '')
                io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' target specification - specification not a dictionary of target parameters.'), 2, 'cri')
                sys.exit(EC)
            if not 'hosts' in config['targets'][t]:
                io.write(io.bold('Preparing working environment...'), 1, '')
                io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' target specification - target does not specify a list of corresponding hosts.'), 2, 'cri')
                sys.exit(EC)
            if isinstance(config['targets'][t]['hosts'], str) or not isinstance(config['targets'][t]['hosts'], list):
                io.write(io.bold('Preparing working environment...'), 1, '')
                io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' target specification - "hosts" parameter is not a list of host strings.'), 2, 'cri')
                sys.exit(EC)
            if 'user' in config['targets'][t]:
                if not isinstance(config['targets'][t]['user'], str):
                    io.write(io.bold('Preparing working environment...'), 1, '')
                    io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' target specification - specified "user" parameter is not a username string.'), 2, 'cri')
                    sys.exit(EC)
            if 'password' in config['targets'][t]:
                if not isinstance(config['targets'][t]['password'], str):
                    io.write(io.bold('Preparing working environment...'), 1, '')
                    io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' target specification - specified "password" parameter is not a password string.'), 2, 'cri')
                    sys.exit(EC)
            if 'cert' in config['targets'][t]:
                if not isinstance(config['targets'][t]['cert'], str):
                    io.write(io.bold('Preparing working environment...'), 1, '')
                    io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' target specification - specified "cert" parameter is not a certificate file path string.'), 2, 'cri')
                    sys.exit(EC)
            if 'port' in config['targets'][t]:
                if not isinstance(config['targets'][t]['port'], int):
                    io.write(io.bold('Preparing working environment...'), 1, '')
                    io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' target specification - specified "port" parameter is not an integer.'), 2, 'cri')
                    sys.exit(EC)
                if config['targets'][t]['port'] < 1:
                    io.write(io.bold('Preparing working environment...'), 1, '')
                    io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' target specification - specified "port" parameter is not a positive integer.'), 2, 'cri')
                    sys.exit(EC)
    if 'tasks' in config:
        logging.debug('Validating "tasks" key...')
        if not isinstance(config['tasks'], dict):
            io.write(io.bold('Preparing working environment...'), 1, '')
            io.write(io.red('Unable to validate "tasks" key - key not mapped to dictionary of task specifications.'), 2, 'cri')
            sys.exit(EC)
        for t in config['tasks']:
            logging.debug('Validating "' + t + '" task specification...')
            if not isinstance(config['tasks'][t], dict):
                io.write(io.bold('Preparing working environment...'), 1, '')
                io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' task specification - specification not a dictionary of task parameters.'), 2, 'cri')
                sys.exit(EC)
            if not 'cmd' in config['tasks'][t]:
                io.write(io.bold('Preparing working environment...'), 1, '')
                io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' task specification - task does not specify a command to execute.'), 2, 'cri')
                sys.exit(EC)
            if not isinstance(config['tasks'][t]['cmd'], str):
                io.write(io.bold('Preparing working environment...'), 1, '')
                io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' task specification - specified "cmd" parameter is not a command string.'), 2, 'cri')
                sys.exit(EC)
            if 'desc' in config['tasks'][t]:
                if not isinstance(config['tasks'][t]['desc'], str):
                    io.write(io.bold('Preparing working environment...'), 1, '')
                    io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' task specification - specified "desc" parameter is not a comment string.'), 2, 'cri')
                    sys.exit(EC)
                    

def validate_environment():
    '''
    Validates that the execution environment is sufficient to proceed.
    '''
    EC = 2
    logging.debug('Looking for argument conflicts...')
    if not args.run and not args.command and not args.console:
        io.write(io.bold('Preparing working environment...'), 1, '')
        io.write(io.red('Argument conflict found - One of "-c"/"--command", "-C"/"--console", or "-r"/"--run" must be present.'), 2, 'cri')
        sys.exit(EC)
    if (args.run and args.command) or (args.run and args.console) or (args.console and args.command):
        io.write(io.bold('Preparing working environment...'), 1, '')
        io.write(io.red('Argument conflict found - Only one of "-c"/"--command", "-C"/"--console", or "-r"/"--run" may be present.'), 2, 'cri')
        sys.exit(EC)
    logging.debug('Looking for invalid argument values...')
    if args.timeout < 0:
        io.write(io.bold('Preparing working environment...'), 1, '')
        io.write(io.red('Invalid argument value found - Value of "-t"/"--timeout" must be zero or a positive integer.'), 2, 'cri')
        sys.exit(EC)
    if args.auth_timeout < 0:
        io.write(io.bold('Preparing working environment...'), 1, '')
        io.write(io.red('Invalid argument value found - Value of "--auth-timeout" must be zero or a positive integer.'), 2, 'cri')
        sys.exit(EC)
    if args.command_timeout < 0:
        io.write(io.bold('Preparing working environment...'), 1, '')
        io.write(io.red('Invalid argument value found - Value of "-T"/"--command-timeout" must be zero or a positive integer.'), 2, 'cri')
        sys.exit(EC)
    if args.port < 1:
        io.write(io.bold('Preparing working environment...'), 1, '')
        io.write(io.red('Invalid argument value found - Value of "--port" must be a positive integer.'), 2, 'cri')
        sys.exit(EC)
    logging.debug('Validating configuration file path...')
    if not os.path.isfile(args.config_file):
        io.write(io.bold('Preparing working environment...'), 1, '')
        io.write(io.red('Unable to validate configuration file path - specified file does not exist.'), 2, 'cri')
        sys.exit(EC)
    if args.cert:
        logging.debug('Validating default certificate file path...')
        if not os.path.isfile(args.cert):
            io.write(io.bold('Preparing working environment...'), 1, '')
            io.write(io.red('Unable to validate default certificate file path - specified file does not exist.'), 2, 'cri')
            sys.exit(EC)


def validate_selected_targets():
    '''
    Validates the selected targets.
    '''
    EC = 6
    logging.debug('Validating selected targets...')
    for t in targets:
        if t == 'other': continue
        logging.debug('Validating "' + t + '" target...')
        if not 'cert' in config['targets'][t] and not 'password' in config['targets'][t] and not args.password and not args.cert:
            io.write(io.bold('Preparing working environment...'), 1, '')
            io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' target - some form of authentication must be specified in the target specification or via CLI arguments.'), 2, 'cri')
            sys.exit(EC)
        if 'cert' in config['targets'][t]:
            if not os.path.isfile(config['targets'][t]['cert']):
                io.write(io.bold('Preparing working environment...'), 1, '')
                io.write(io.red('Unable to validate ') + io.bold(t) + io.red(' target - specified certificate file does not exist.'), 2, 'cri')
                sys.exit(EC)


def validate_selected_task():
    '''
    Validates the selected task (if there is one).
    '''
    EC = 6
    logging.debug('Validating selected task...')
    if not args.run:
        logging.debug('No task specified.')
        return
    if ' ' in args.run:
        tsk = args.run.split(' ', 1)[0]
    else:
        tsk = args.run
    logging.debug('Task Name: ' + tsk)
    if not tsk in config['tasks']:
        io.write(io.bold('Preparing working environment...'), 1, '')
        io.write(io.red('Unable to validate ') + io.bold(tsk) + io.red(' task - specified task does not exist.'), 2, 'cri')
        sys.exit(EC)

    
# --------------------------------------



# ---------- Boilerplate Magic ---------

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError) as ki:
        sys.stderr.write('Recieved keyboard interrupt!\n')
        sys.exit(100)

# --------------------------------------

'''
io.py

Contains methods for printing to, and interacting with, the console and filesystem.
'''
# Imports
import logging
import os
import re
import sys

# Options
COLOR_ENABLED = True
OUTPUT_ONLY = False

# Color Sequences
COLOR_BLUE   = '\033[94m'
COLOR_GREEN  = '\033[92m'
COLOR_ORANGE = '\033[93m'
COLOR_RED    = '\033[91m'
COLOR_END    = '\033[0m'
COLOR_BOLD   = '\033[1m'

# Regular Expressions
ANSI_ESC_REGEX = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')


# ---------- Private Functions ----------

def _fmt_step(instring, lvl=0, color=COLOR_BLUE):
    '''
    Formats the string to a particular "step" level. Note that the color here
    only controls the color of the ligature to the left of the step.

    Where the levels are:
    -1|[no output]
     0|foo
     1|:: foo
     2|   foo
     3|  --> foo
     4|      foo
     5|       * foo
     6|         foo
    '''
    if lvl == -1:
        return ''
    elif lvl == 1:
        return colorize('::', color) + ' ' + instring
    elif lvl == 2:
        return '   ' + instring
    elif lvl == 3:
        return '  ' + colorize('-->', color) + ' ' + instring
    elif lvl == 4:
        return '      ' + instring
    elif lvl == 5:
        return '       ' + colorize('*', color) + ' ' + instring
    elif lvl == 6:
        return '         ' + instring
    return instring




# ---------- Public Functions ----------

def blue(instring):
    '''
    Returns a blue version of the specified string.
    '''
    return colorize(instring, COLOR_BLUE)


def bold(instring):
    '''
    Returns a bold version of the specified string.
    '''
    return colorize(instring, COLOR_BOLD)


def colorize(instring, color=COLOR_BLUE):
    '''
    Colorizes the specified input string.

    The input string will be returned unaltered if `COLOR_ENABLED` is set to `False`.
    '''
    if COLOR_ENABLED and not color is None:
        return color + instring + COLOR_END
    return instring


def orange(instring):
    '''
    Returns an orange version of the specified string.
    '''
    return colorize(instring, COLOR_ORANGE)


def red(instring):
    '''
    Returns a red version of the specified string.
    '''
    return colorize(instring, COLOR_RED)


def setup_logging(log_file, log_mode='append', log_level='info'):
    '''
    Sets-up logging.
    '''
    if log_file:
        try:
            if log_mode == 'append':
                logging_fmode = 'a'
            else:
                logging_fmode = 'w'
            if log_level == 'info':
                logging_level = logging.INFO
            else:
                logging_level = logging.DEBUG
            logging.basicConfig(
                filename = log_file,
                filemode = logging_fmode,
                level    = logging_level,
                format   = '[%(levelname)s] [%(asctime)s] [%(process)d] %(message)s',
                datefmt  = '%m/%d/%Y %I:%M:%S %p'
            )
            logging.addLevelName(logging.CRITICAL, 'CRI')
            logging.addLevelName(logging.ERROR, 'ERR')
            logging.addLevelName(logging.WARNING, 'WAR')
            logging.addLevelName(logging.INFO, 'INF')
            logging.addLevelName(logging.DEBUG, 'DEB')
        except Exception as e:
            sys.exit('Unable to initialize logging system - ' + str(e) + '.')
    else:
        logger = logging.getLogger()
        logger.disabled = True

        
def write(instring, step_lvl=0, log_lvl='INF', color=COLOR_BLUE, new_line=True):
    '''
    Writes the specified to string stdout/stderr (and to the log, if specified).

    Where `log_lvl` is one of "" (don't log to file), "DEB", "INF", "WAR",
    "ERR", or "CRI".
    '''
    ll = log_lvl.lower()
    if not ll in ['', 'deb', 'inf', 'war', 'err', 'cri']:
        raise Exception('Inavlid (code-level) log level - "' + log_lvl + '"')
    outstring = _fmt_step(instring, step_lvl, color)
    logstring = ANSI_ESC_REGEX.sub('', instring)
    if ll in ['war', 'err', 'cri']:
        if outstring and not OUTPUT_ONLY:
            sys.stderr.write(outstring)
            if new_line:
                sys.stderr.write('\n')
        if ll == 'war':
            logging.warning(logstring)
        elif ll == 'err':
            logging.error(logstring)
        elif ll == 'cri':
            logging.critical(logstring)
    else:
        if outstring and not OUTPUT_ONLY:
            sys.stdout.write(outstring)
            if new_line:
                sys.stdout.write('\n')
        if ll == 'deb':
            logging.debug(logstring)
        elif ll == 'inf':
            logging.info(logstring)
            

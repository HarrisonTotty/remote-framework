'''
parser.py

Contains code for parsing various expressions.
'''

# Imports
import re

# Regular Expressions
host_range_regex = re.compile(
    r'^[\w\d\-\.]*(?P<expr>\[(?P<lower>\d+)\-(?P<upper>\d+)\])[\w\d\-\.]*$'
)
host_list_regex = re.compile(
    r'^[\w\d\-\.]*(?P<expr>\[[\w\d\,\-\.]+\])[\w\d\-\.]*$'
)

# ---------- Public Functions ----------

def parse_host_str(instring):
    '''
    Parses the specified host string (potentially containing range or list
    expansions) into a list.

    In other words:
    "foo"           becomes ["foo"]
    "foo[1-3]"      becomes ["foo1", "foo2", "foo3"]
    "foo-[bar,baz]" becomes ["foo-bar", "foo-baz"]
    '''
    if not '[' in instring and not ']' in instring:
        return [instring]
    if '[' in instring and ']' in instring:
        hosts = []
        guts = instring.split('[', 1)[1]
        if not ']' in guts:
            raise Exception('host string has its shoelaces untied')
        guts = guts.split(']', 1)[0]
        if '-' in guts:
            host_range_match = host_range_regex.match(instring)
            if not host_range_match:
                raise Exception('host string not a valid range expansion')
            expr = host_range_match.group('expr')
            lb = int(host_range_match.group('lower'))
            ub = int(host_range_match.group('upper'))
            if not ub > lb:
                raise Exception('upperbound in host string range expansion is not greater than the lowerbound')
            for i in range(lb, ub + 1):
                hosts.append(instring.replace(expr, str(i)))
        elif ',' in guts:
            host_list_match = host_list_regex.match(instring)
            if not host_list_match:
                raise Exception('host string not a valid list expansion')
            expr = host_list_match.group('expr')
            parts = expr[1:-1].split(',')
            for p in parts:
                hosts.append(instring.replace(expr, p))
        else:
            raise Exception('host string does not specify a range or list expansion')
        return hosts
    else:
        raise Exception('host string does not have balanced brackets')

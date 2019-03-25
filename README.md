# Introduction

`remote` is a Python script that forms a lightweight system for performing remote operations on multiple machines. It was designed to be a simpler alternative to more "feature-rich" remote execution frameworks like Ansible, Salt, or Fabric.


## System Requirements

* Python 3
* [PyYAML](https://pyyaml.org/)
* [Paramiko](http://www.paramiko.org/)


## Installation

There is currently no installer, but here's the quick way to get up-and-running:

1. Clone the repository into some directory with _full path_ `DIR`.

2. Create a file called `/usr/local/bin/remote` with the following contents (replacing `DIR` with the _full path_ to your directory):

```bash
#!/bin/bash
set -e

# You can set environment variables for the script here:
#export REMOTE_USER="root"

cd DIR
DIR/remote.py $@
```

Be sure to run `chmod +x /usr/local/bin/remote` after you've created the file.

3. Now you can run `remote` like in the examples!


## Known Bugs & Potential Issues

* `remote` currently doesn't supply any way for remote commands to attach to the executing terminal's standard input stream. This means that running commands like `less` on remote hosts will currently not work.
* `remote` currently doesn't support task arguments that contain `:` characters, due to the way that the script calls `str.split(':')` under the hood.
* `remote` currently doesn't support the `-P`/`--parallel` flag.
* `remote` currently doesn't support the `-C`/`--console` flag.
* Currently only _one_ substitution of the form `[a,b,c...]` or `[x-y]` may be specified with a single string in the `hosts` key of a target specification in the framework configuration file, however you can easily get around this by just specifying multiple strings.

----
# Usage

## Basic Example

`remote` is invoked by specifying a list of servers followed by the `--command`, `--console`, or `--run` arguments (or their shorthand aliases). The "list of servers" may correspond to specific hostnames _or_ a valid target within the script's corresponding configuration file (see `CONFIGURATION.md`). The `--command` argument (or `-c` for short) is the simplest use case. This argument will execute the specified command on all of the supplied target machines. For example

```bash
$ remote foo{1..5}.example.com -c 'echo hello world'
```

would execute `echo hello world` on `foo1.example.com`, `foo2.example.com`, etc. The corresponding output would look like:

```
:: Preparing working environment...
:: Connecting to remote hosts...
:: Executing specified command...
  --> foo1.example.com
      hello world
  --> foo2.example.com
      hello world
  --> foo3.example.com
      hello world
  --> foo4.example.com
      hello world
  --> foo5.example.com
      hello world
:: Disconnecting from remote hosts...
```

However, if we instead redirect the script to a file called `remote.out`:

```bash
$ remote foo{1..5}.example.com -c 'echo hello world' > remote.out
```

... the script will automatically format the output like so:

```
foo1.example.com : hello world
foo1.example.com < 0
foo2.example.com : hello world
foo2.example.com < 0
foo3.example.com : hello world
foo3.example.com < 0
foo4.example.com : hello world
foo4.example.com < 0
foo5.example.com : hello world
foo5.example.com < 0
```

In the above, we can see that when the script is redirected to a file (or run with the `-o`/`--output-only` flag), it will write entries of the forms `HOST : OUTPUT` and `HOST < EXIT_CODE`.


## CLI Arguments

The following table describes the various command-line arguments:

| Argument(s)               | Description                                                                                                                                                         |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `--auth-timeout`          | Specifies the remote authentication and banner timeout, in seconds. Set to `0` to disable.                                                                          |
| `--cert`                  | Specifies a default certificate file to use when authenticating with remote servers.                                                                                |
| `-c`, `--command`         | Executes the specified command on the supplied target server(s).                                                                                                    |
| `-T`, `--command-timeout` | Specifies the timeout in regards to waiting for remote commands to complete, in seconds. Set to `0` to disable.                                                     |
| `--compress`              | Enables compression in the communication with remote servers.                                                                                                       |
| `-y`, `--config-file`     | Specifies the remote framework YAML configuration file to load.                                                                                                     |
| `-C`, `--console`         | Opens an interactive console with the specified target server(s).                                                                                                   |
| `-d`, `--dry-run`         | Specifies that the script should not actually execute any commands on the specified remote target server(s).                                                        |
| `-h`, `--help`            | Displays help and usage information.                                                                                                                                |
| `--list-targets`          | Lists all of the available targets in the specified (or default) configuration file.                                                                                |
| `--list-tasks`            | Lists all of the available tasks in the specified (or default) configuration file.                                                                                  |
| `-f`, `--log-file`        | Specifies a log file to write events to in addition to stdout/stderr.                                                                                               |
| `-l`, `--log-level`       | Specifies the log level of the script.                                                                                                                              |
| `-m`, `--log-mode`        | Specifies whether to append to, or overwrite, the specified (or default) log file on each run.                                                                      |
| `--no-color`              | Disables color output to stdout/stderr.                                                                                                                             |
| `-o`, `--output-only`     | Instructs the script to only output data from the remote execution process itself. This is automatically selected when redirecting the script's output to a file.   |
| `-P`, `--parallel`        | Specifies that the remote commands should be executed in parallel.                                                                                                  |
| `-p`, `--password`        | Specifies the default password to use when connecting to remote hosts. If this argument is supplied without a value, the user will be prompted to enter a password. |
| `--port`                  | Specifies the default port to use when connecting to remote hosts.                                                                                                  |
| `-r`, `--run`             | Executes the specified task on the supplied target server(s).                                                                                                       |
| `-t`, `--timeout`         | Specifies the general communication timeout for all remote connections. Set to `0` to disable.                                                                      |
| `-u`, `--user`            | Specifies the default user to use when connecting to remote hosts.                                                                                                  |

The following table expands upon the one above to list the value types, default values, and associated environment variables for the arguments:

| Argument(s)               | Value Type / Possible Values | Default Value   | Associated Environment Variable |
|---------------------------|------------------------------|-----------------|---------------------------------|
| `--auth-timeout`          | Positive Integer or `0`      | `5`             | `REMOTE_AUTH_TIMEOUT`           |
| `--cert`                  | File Path                    |                 | `REMOTE_CERT`                   |
| `-c`, `--command`         | Command String               |                 |                                 |
| `-T`, `--command-timeout` | Positive Integer or `0`      | `0`             | `REMOTE_COMMAND_TIMEOUT`        |
| `-y`, `--config-file`     | File Path                    | `~/remote.yaml` | `REMOTE_CONFIG_FILE`            |
| `-f`, `--log-file`        | File Path                    | `~/remote.log`  | `REMOTE_LOG_FILE`               |
| `-l`, `--log-level`       | `info` or `debug`            | `info`          | `REMOTE_LOG_LEVEL`              |
| `-m`, `--log-mode`        | `append` or `overwrite`      | `append`        | `REMOTE_LOG_MODE`               |
| `-p`, `--password`        | Password String (Optional)   |                 | `REMOTE_PASSWORD`               |
| `--port`                  | Positive Integer             | `22`            | `REMOTE_PORT`                   |
| `-r`, `--run`             | Task String (See Below)      |                 |                                 |
| `-t`, `--timeout`         | Positive Integer or `0`      | `5`             | `REMOTE_TIMEOUT`                |
| `-u`, `--user`            | User Name                    | (Current User)  | `REMOTE_USER`                   |


## Remote Authentication

Remote authentication in the remote framework may be handled in one of the following ways:

* Specifying the `--cert` argument (or setting the `REMOTE_CERT` environment variable) with a path to a certificate file, which will be used as the default authentication certificate if none is specified for the given target in the framework configuration file.
* Specifying the `-p`/`--password` argument (or setting the `REMOTE_PASSWORD` environment variable) with a string value, which will be used as the default connection password if none is specified for the given target in the framework configuration file.
* Specifying the `-p`/`--password` argument without specifying a value, which will prompt the user to securely enter one.
* Specifying a value for the `cert` key for the given target in the framework configuration file (which will also override `--cert`/`REMOTE_CERT` if it is also set).
* Specifying a value for the `password` key for the given target in the framework configuration file (which will also override `-p`/`--password`/`REMOTE_PASSWORD` if it is also set).

If both a certificate _and_ a password are supplied for a given host or target, then the script will follow [Paramiko's rules for authentication](http://docs.paramiko.org/en/2.4/api/client.html#paramiko.client.SSHClient.connect).


## Running Arbitrary Commands

As demonstrated in the _Basic Example_ section, arbitrary commands may be executed on the specified target server(s) by providing the script with the `-c`/`--command` argument.


## Running Tasks

`remote` supports the execution of pre-defined commands ("tasks") on the specified target server(s) by providing the script with the `-r`/`--run` argument. The value of this argument is the name of the task as defined in the framework configuration file. For example, if the framework configuration file contained the following task definition:

```yaml
tasks:
  update_puppet:
    desc: 'Executes "puppet agent --test" on the specified target(s).'
    cmd: 'puppet agent --test'
```

Then `puppet agent --test` may be executed on a collection of remote servers by running the following on the command-line:

```bash
$ remote foo{1..5}.example.com -r update_puppet
```

In addition to simple commands, tasks may actually be formulated into complex scripts with command-line arguments. Take for example the following task definition which will disable puppet on the specified target(s) with an optional message:

```yaml
tasks:
  disable_puppet:
    desc: 'Disables the puppet agent on the specified target(s), with an optional message.'
    cmd: >-
      if [ "$#" -eq 1 ]; then
        puppet agent --disable "$1"
      else
        puppet agent --disable
      fi
```

Task command-line arguments are passed to the script by separating arguments by a single `:` character after the task name. With the above example, one might execute:

```bash
$ remote foo{1..5}.example.com -r 'disable_puppet:Doing some debugging on these nodes'
```


## Interactive Console (WIP)

The script supports the ability to run in a sort-of interactive terminal mode with the `-C`/`--console` flag.


## Listing Targets and Tasks

The script provides a convenient way to display what targets/tasks are available in the framework configuration file with the `--list-targets` and `--list-tasks` flags. When listing targets, the script displays the name of each target, followed by the list of hosts it corresponds to, like so:

```
$ remote --list-targets
prd_all  : db-prd[1-8].example.com, web-prd[1-8].example.com
prd_db   : db-prd[1-8].example.com
prd_web  : web-prd[1-8].example.com
tst_all  : db-tst[1-4].example.com, web-tst[1-4].example.com
tst_db   : db-tst[1-4].example.com
tst_web  : web-tst[1-4].example.com
```

Similarly, `--list-tasks` will display the names of each task, as well as the task's description (if it has one specified):

```
$ remote --list-tasks
disable_puppet  : Disables the puppet agent on the specified target(s), with an optional message.
enable_puppet   : Re-enables the puppet agent on the specified target(s).
restart_tomcat  : Restarts the "tomcat" service on the specified target(s).
update_puppet   : Executes "puppet agent --test" on the specified target(s).
```

----
# Framework Configuration File

See `CONFIGURATION.md` for more information.

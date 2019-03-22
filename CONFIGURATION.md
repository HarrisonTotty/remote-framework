# Remote Framework Configuration

Custom "targets" and "tasks" may be specified in a remote framework configuration file. This is a YAML file located at `~/remote.yaml` (or wherever specified by the `-y`/`--config-file` command-line argument or the `REMOTE_CONFIG_FILE` environment variable).

## Target Specifications

Target specifications are dictionaries mapped to keys within `targets` key of the framework configuration file. Looking within the `example/remote.yaml` file within this repository, this corresponds to the following section:

```yaml
targets:
  # ----- Tomcat Nodes -----
  tomcat_nodes:
    hosts:
      - "foo[1-10].example.com"
    user: "root"
    password: "Un1ncrypt3d P455w0rd"

  # ----- Apache Nodes -----
  apache_nodes:
    hosts:
      - "bar[1,3,5].example.com"
    user: "admin"
    cert: "~/.ssh/apache-cert.pem"

  # ----- MySQL Nodes -----
  mysql_nodes:
    hosts:
      - "baz.example.com"
      - "whamzo.example.com"
```

In the above example, we can see that three targets are defined: `tomcat_nodes`, `apache_nodes`, and `mysql_nodes`. Within each target is the required `hosts` key, which maps to a list of strings specifying the remote server(s) associated with the target. These strings may either directly correspond to a hostname or FQDN, or may contain one of two supported expansion expressions:

* Expressions of the form `[a,b,c,d...]` list out substitution substrings, similar to `{a,b,c,d...}` in most shell languages. These substrings need not be numeric and can contain any valid hostname character (`[a-z0-9\-\.]` in regular expressions).
* Expressions of the form `[x-y]` provide an inclusive numeric range substitution. Both `x` and `y` must be integer values, where `y > x`.

In addition to the `hosts` key, a target specification may include any of the following additional key-value pairs:

| Key        | Value Type       | Description                                                                        |
|------------|------------------|------------------------------------------------------------------------------------|
| `cert`     | String           | The path to the certificate file to use for connections within this specification. |
| `password` | String           | The password to use for connections within the specification.                      |
| `port`     | Positive Integer | The port to use for connections within the specification.                          |
| `user`     | String           | The user to use for connections within the specification.                          |

Note that each of the above key-value pairs will override any values specified via the corresponding relevant command-line argument.


## Task Specifications

Like target specifications, task specifications are dictionaries mapped to keys within the `tasks` key in the framework configuration file. Within `example/remote.yaml`, this corresponds to the following section:

```yaml
tasks:
  # ----- Run Puppet -----
  run_puppet:
    desc: "Executes a puppet run on the target machine(s)."
    cmd: "puppet agent --test"

  # ----- Install a Package -----
  install:
    desc: "Installs the specified package via yum."
    cmd: "yum install $1"

  # ----- Do something complicated -----
  complex_example:
    desc: "Does something a bit more complex."
    cmd: >-
      for i in {foo,bar,baz}; do
        echo "Creating $i..."
        touch $i
      done
```

Each task specification requires the `cmd` key, which is bound to a (potentially multi-line) string containing the command(s) to execute when the task is run. As explained in the _Running Tasks_ section within `README.md`, these strings are essentially `bash` scripts, and thus may reference their command-line arguments as expected with `$1`, `$#`, etc.

A task may also optionally (although recommended) include a short description by specifying a string value for the `desc` key. This description will be printed when the `--list-tasks` flag is passed to the script.

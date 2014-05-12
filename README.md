# python autoldap wrapper

Provides a simple ldap wrapper for binding and searching ldap via the python-ldap library.

Designed to work with python 2.5 or higher (including python 3.x)


## Example Usage:

```python
from autoldap import AutoLDAP

# method one, zero-conf

ldap = AutoLDAP()

# method two, specified configuration

ldap = AutoLDAP(config="./path/to/autoldap.conf")

# method three, deferred bind

ldap = AutoLDAP(config="./path/to/autoldap.conf", defer=True)
ldap.bind()

# method four, argparse options (requires deferred bind)

ldap = AutoLDAP(config="./path/to/autoldap.conf", defer=True)
parser = ldap.init_argparse()
# ...
# add additional arguments via argparse api.
# ...
args = parser.parse_args()
ldap.load_arguments(args)
ldap.bind()


```

## Configuration options:
An example configuration can be found in the root of the repository

```ini
[AutoLDAP]
     URI = ldap://ldap.example.com           # URI will default to ldapi:/// if none is provided
  binddn = uid=test,dc=example,dc=com        # bind_dn (defaults to anonymous)
  passwd = password                          # clear-text password (make sure the config file is protected)
  prompt = TRUE | YES | 1 | FALSE | NO | 0   # boolean, should the user be prompted for a password (interactive)
saslmech = GSSAPI | EXTERNAL                 # if sasl auth use this mech
starttls = none | try | demand               # starttls protocol
    auth = anon[ymous] | simple | sasl       # authentication modes
  basedn = dc=example,dc=com                 # default search base (used in auto_search methods)
 version = 3                                 # ldap protocol version

```

## Default configuration search paths:

1. /etc/autoldap/autoldap.conf
2. ~/.autoldaprc
3. ./autoldap.conf

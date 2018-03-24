# python autoldap wrapper

Provides a simple ldap wrapper for binding and searching ldap via the python-ldap library.

Designed to work with python 2.5 or higher (including python 3.x)


## Installation
```bash
# Install dependencies
# Debian/Ubuntu
sudo apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev
# RedHat/CentOS/Fedora
sudo yum install python-devel openldap-devel

# Install autoldap
pip install git+https://github.com/rjancewicz/autoldap.git
```


## Example Usage:

#### Instantiation
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

# addtional option for all methods options

options = {
     'URI': 'ldap://foo.example.com',
  'basedn': 'dc=foo,dc=example,dc=com'
}

ldap = AutoLDAP(config="./path/to/autoldap.conf", options=options)

# update configuration

ldap.set_config('uri': 'ldap://bar.example.com')
ldap.set_config('basedn', 'dc=bar,dc=example,dc=com')

ldap.rebind()
```


#### Searching

```python
# single entry search (returns a tuple unpacked from a regular ldap.search or None)

(dn,attrs) = ldap.fetch_entry('uid=test,dc=example,dc=com')

# paged searches (useful for large search results)

for chunk in ldap.paged_search(page_size=512):
  for (dn, attr) in chunk:
    print(dn)

# auto_search_ext_s, search without specifying base and scope
#  by default searches the basedn from configuration with subtree scope

results = ldap.auto_search_ext_s()
results = ldap.auto_search_ext_s(uid=russ)
results = ldap.auto_search_ext_s(uid=russ)
```

#### Unpacking

```python
# unpack a single value (specifically the first value) from an attribute set

value = ldap.unpack_one(attrs, 'attrName')

# this is a shorthand for the following (including None initialization)

value = None

if 'attrName' in attrs:
  value = attrs['attrName'][0]

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

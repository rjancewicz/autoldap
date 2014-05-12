#
# autoldap 
#   Russell J. Jancewicz - 2014-05-08 
#
#

# import members of the python standard library
import os
import sys
import getpass
from pprint import pprint

# ConfigParser [configparser] is part of the standard library but has querks.
try: 
    import configparser 
except ImportError as error:
    # ConfigParser is the original name in the 2.x builds, 
    #   'import as' rename maintains python 3.x compatibility
    #   PEP 8 specifies package names should be lowercase
    import ConfigParser as configparser

try: 
    import ldap
    from ldap import sasl
    from ldap import ldapobject
except ImportError as error:
    sys.stderr.write('python-ldap is required for autoldap, install via pip or easy_install.\n');
    sys.exit(1)


try: 
    from ldap.controls.libldap import SimplePagedResultsControl
except:
    if __debug__:
        sys.stderr.write('Warning: unable to import ldap.controls.libldap.SimplePagedResultsControl; paged_search is disabled.\n')

try:
    import argparse
except ImportError as error:
    if __debug__:
        sys.stderr.write('Warning: unable to import argparse; init_argparser and load_arguments are disabled.\n')


class AutoLDAP(ldapobject.SimpleLDAPObject):

# configurations: 
    ENV_HOME     = os.path.expanduser("~")
    CFG_HOME     = "{0}/.autoldaprc".format(ENV_HOME)
    CFG_LOCAL    = "./autoldap.conf"
    CFG_GLOBAL   = "/etc/autoldap/autoldap.conf"

    CFG_SECTION  = "AutoLDAP"
    CFG_URI      = "URI"
    CFG_BINDDN   = "binddn"
    CFG_PASSWD   = "passwd"
    CFG_PROMPT   = "prompt"
    CFG_SASLMECH = "saslmech"
    CFG_STARTTLS = "starttls"
    CFG_AUTH     = "auth"
    CFG_BASEDN   = "basedn"
    CFG_VERSION  = "version"

    SCOPE_BASE     = ldap.SCOPE_BASE
    SCOPE_ONELEVEL = ldap.SCOPE_ONELEVEL 
    SCOPE_SUBTREE  = ldap.SCOPE_SUBTREE

    default_configuration = {
        CFG_URI:     'ldapi:///',
        CFG_BINDDN:   None,
        CFG_PASSWD:   None,
        CFG_PROMPT:   False,
        CFG_SASLMECH: 'EXTERNAL', #['GSSAPI'],
        CFG_STARTTLS: 'try',
        CFG_AUTH:     'SASL', #['simple', 'anonymous']
        CFG_BASEDN:   None,
        CFG_VERSION:  3
    }

    '''
    Parameters:
        URI      = 'ldapi:///'
        # host   = '127.0.0.1' # NO HOST AND PORT... JUST USE URI
        # port   = 386
        binddn   = cn=root,dc=example,dc=com
        passwd   = password
        prompt   = {YES, NO, True, False, 1, 0}
        saslmech = {gssapi, external}
        starttls = {none, try, demand}
        auth     = {sasl, simple, anon[ymous]}
        basedn   = dc=example,dc=com
        version  = 3
    '''

    def __init__(self, config=None, options=None, defer=False, debug_level=0x0): 

        self.debug_level = debug_level

        self.load_configuration(config)

        if options is not None: 
            self.set_configs(options)

        if not defer:
            self.bind()

    def debug_print_configuration(self):

        pprint(self.configuration)

    # Auto Search Methods

    # paged_search is only availible if the controller is available
    #   technically we can achive this without the controller (as paged results is simple)
    #   however it is easer to delegate the operation to the default controller.
    if 'SimplePagedResultsControl' in globals():
        def paged_search(self,
            base        = None, 
            scope       = ldap.SCOPE_SUBTREE, 
            page_size   = 1000,
            criticality = True,
            serverctrls = None,
            **search_args):

            cookie = ''
            criticality = criticality

            initial = True

            if serverctrls is None:
                serverctrls = []
            else:
                serverctrls = list(serverctrls)
            
            if base is None:
                base = self._config(self.CFG_BASEDN)

            if base: 

                page_control = SimplePagedResultsControl(criticality, page_size, cookie)

                while initial or page_control.cookie:
                    initial = False

                    try: 
                        msgid = self.search_ext(base, scope, 
                            serverctrls = serverctrls + list([page_control]), 
                            **search_args)

                    except ldap.LDAPError as error:
                        raise error

                    #(rtype, results, msgid, sent_serverctrls)
                    (_, results, _, controls) = self.result3(msgid)

                    for control in controls:
                        if control.controlType == page_control.controlType:
                            page_control.cookie = control.cookie

                    yield results
            
    def auto_search_ext_s(self, 
        base        = None, 
        scope       = ldap.SCOPE_SUBTREE, 
        **search_args):

        results = None

        base = base or self._config(self.CFG_BASEDN)

        if base:
            results = self.search_ext_s(base, scope, **search_args)

        return results

    def fetch_entry(self, base, **search_args):

        scope = ldap.SCOPE_BASE

        result = self.search_ext_s(base, scope, sizelimit = 1, **search_args)

        if result:
            result = result[0]

        return result

    # Unpacking helper

    def unpack_one(self, attrs, name):

        value = None

        if name in attrs:
            value = attrs[name][0]

        return value
  
    # Configuration and Bind Methods

    def starttls(self): 

        starttls = self._config(self.CFG_STARTTLS).upper()


        if starttls in ['TRY', 'DEMAND']:
            try:
                self.start_tls_s()
            except ldap.LDAPError as error:
                print(error)
                if 'DEMAND' in starttls:
                    self.unbind_s()
                    del self
                    raise error

    def bind_anonymous(self): 

        self.simple_bind_s()

    def bind_simple(self): 

        binddn = self._config(self.CFG_BINDDN)
        passwd = self._config(self.CFG_PASSWD)
        prompt = self._config(self.CFG_PROMPT)

        if binddn and not passwd and prompt:
            sys.stdout.write("LDAP ")
            sys.stdout.flush()
            passwd = getpass.getpass()

        if binddn and passwd:
            self.simple_bind_s(binddn, passwd)
        else:
            raise ldap.INVALID_CREDENTIALS

    def bind_sasl(self): 

        mech = self._config(self.CFG_SASLMECH).upper()

        if 'EXTERNAL' in mech:
            self.sasl_interactive_bind_s('', sasl.external())

        if 'GSSAPI' in mech:
            self.sasl_interactive_bind_s('', sasl.gssapi())
                
    def bind(self): 

        # initialize the ldap handle for self first.
        ldapobject.SimpleLDAPObject.__init__(self, self._config(self.CFG_URI))
        
        self.starttls()

        auth = self._config(self.CFG_AUTH).upper()

        if "SASL" in auth:
            self.bind_sasl()
        elif "SIMPLE" in auth:
            self.bind_simple() 
        elif "ANON" in auth:
            self.bind_anonymous()
        else:
            raise ldap.AUTH_UNKNOWN

    def rebind(self):

        self.unbind_s()
        self.bind()

    # argparse methods are added depending on availibility
    if 'argparse' in sys.modules:
        def init_argparser(self, parser=None):

            if not isinstance(parser, argparse.ArgumentParser):
                parser = argparse.ArgumentParser()

            parser.add_argument('-D',  default=None, dest=self.CFG_BINDDN,   help="bind DN",                                   metavar="binddn")
            parser.add_argument('-H',  default=None, dest=self.CFG_URI,      help="LDAP Uniform Resource Identifier(s)",       metavar="URI")
            parser.add_argument('-Y',  default=None, dest=self.CFG_SASLMECH, help="SASL mechanism",                            metavar="mech")
            parser.add_argument('-w',  default=None, dest=self.CFG_PASSWD,   help="bind password (for simple authentication)", metavar="passwd")
            parser.add_argument('-W',  default=None, dest=self.CFG_PROMPT,   help="prompt for bind password", action='store_true')
            parser.add_argument('-x',  default=None, dest=self.CFG_AUTH,     help="Simple authentication",    action='store_const', const='SIMPLE')
            parser.add_argument('-Z',  default=None, dest=self.CFG_STARTTLS, help="Try Start TLS request",    action='store_const', const='TRY')
            parser.add_argument('-ZZ', default=None, dest=self.CFG_STARTTLS, help="Demand Start TLS request", action='store_const', const='DEMAND')

            return parser

        def load_arguments(self, args):

            if isinstance(args, argparse.Namespace):
                args = vars(args)

            if not isinstance(args, dict):
                return

            for option, value in args.iteritems():
                if value is not None:
                    if option in self.configuration:
                        self.configuration[option] = value

    # Convenience method for unpacking options falling back on defaults
    def _config(self, cfg):

        return self.configuration.get(cfg, self.default_configuration[cfg])


    def set_config(self, cfg, option):

        cfg = cfg.lower()

        for key in self.configuration:
            if key.lower() == cfg:
                self.configuration[key] = option
                break

    def set_configs(self, options):

        if isinstance(options, dict):
            for cfg, value in options.iteritems():
                self.set_config(cfg, option)

    # ConfigParser loading of configuration
    def load_configuration(self, config_path):

        self.configuration = self.default_configuration

        config = configparser.ConfigParser()

        sources = [self.CFG_GLOBAL, self.CFG_HOME, self.CFG_LOCAL]

        if config_path:
            sources.append(config_path)

        config.read(sources)

        if config.has_section(self.CFG_SECTION):

            for option in self.default_configuration:

                if config.has_option(self.CFG_SECTION, option):
                    self.configuration[option] = config.get(self.CFG_SECTION, option)

            if config.has_option(self.CFG_SECTION, self.CFG_PROMPT):
                try:
                    self.configuration[self.CFG_PROMPT] = config.getboolean(self.CFG_SECTION, self.CFG_PROMPT)
                except ValueError:
                    self.configuration[self.CFG_PROMPT] = False







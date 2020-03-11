""" Author: Megarushing
    This is a simple script to automate configuration persistence
    and accessibility throughout the system using python default config parser,
    the only thing you need to edit is the default_values field for the default
    settings desired, you may do this by inheriting this class or modifying
    that field before creating an instance.
    You can also provide a filename when instatiating if you desire so,
    instead of the standard config.ini. If the file does not exist,
    it will be created with the default settings.
    Multiple file names in a list are also possible, in which case all are used to load the
    settings in order, same settings take precedence on later files while
    only the most precedent last file is used for saving new settings"""
import os
import sys
import json
import logging
if sys.version_info >= (3, 0): #Python 3 configparser
    from configparser import ConfigParser
    from configparser import Error as ParserError
else:
    from ConfigParser import ConfigParser
    from ConfigParser import Error as ParserError

logging.basicConfig()
logger = logging.getLogger('easyfig')

class Easyfig(object):
    # In default_values set all possible configs, and their default values
    # the exact config type will be inferred based on its default values type
    # every dict key will become a global variable under this lib for ease of access
    # NOTE: if config name starts with a _(underscore) it will be protected from the script
    # and only modifiable through manually editing the ini file
    defaults = {
        "GENERAL" : {
            "example" : 1,
            "_protected_example": 0
        }
    }

    @staticmethod
    def set_defaults(defaults_dict,section="GENERAL"):
        """ We can use this method to set the default values for the configuration,
         this needs to be set before creating the instance, so the correct file is created
         automatically on first run
        :param dict defaults_dict: dictionary with variable names and default values
                                  to be persisted accross multiple runs, this goes
                                  in the form
                                    {
                                        "example" : 1,
                                        "_protected_example": 0
                                    }
                                  the names that begin with _ are protected and can
                                  only be edited by _set or by modifying the config file
        :param str section: variables are usually created in the default "GENERAL"
                            section, in case you need additional sections you can
                            specify default values for it by setting this variable
        """
        Easyfig.defaults[section] = defaults_dict

    # override this function if you need to load additional custom sections not
    # controlled by this script
    def load_additional_sections(self):
        """ override this function if you need to load additional custom sections not
            controlled by easyfig, you can use self._parser as the preloaded ConfigParser object """
        return

    # set this to the desired config file(s), this can be either a string or a list
    # of multiple strings, when multiple config files are detected, settings are
    # loaded from all files in order, but saved only to the last one
    def __init__(self,filename='config.ini'):
        """ loads the configuration file as fields in this object
            filename accepts both a list of config files to load or a single string"""
        self._config_filename = filename #updates config filename
        #os.path.dirname(os.path.realpath(__file__)) was writing to module path
        if type(self._config_filename) == str:
            self._config_filename = [self._config_filename]
        if os.path.isdir(os.path.realpath(sys.argv[0])):
            self._script_dir = os.path.realpath(sys.argv[0])
        else:
            self._script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        self._parser = None
        self._save_parser = None
        self._load()

    def _load(self):
        # for saving we use only last file
        self._save_parser = ConfigParser()
        self._save_parser.read(os.path.join(self._script_dir, self._config_filename[-1]))
        #for loading we use all files
        self._parser = ConfigParser()
        for filename in self._config_filename:
            #loads all ini files, last one has precedence over first
            self._parser.read(os.path.join(self._script_dir,filename))

        #generates all global variables representing config sections
        for section,defaults in self.defaults.items():
            for option,default_value in defaults.items():
                varname = option
                if option.startswith("_"):
                    varname = option.replace("_","",1)
                    #if there is a config with same name remove it, only protected one stays
                    if self._parser.has_section(section) and varname in self._parser.items(section):
                        self._parser.remove_option(section=section,option=varname)
                    if self._save_parser.has_section(section) and varname in self._save_parser.items(section):
                        self._save_parser.remove_option(section=section,option=varname)
                if section != "GENERAL":
                    varname = section.lower() + "_" + varname
                #cast read string variable to type from default_values
                val = self.get(option,default=default_value,section=section)
                self._set_attribute(varname, val, default_value)
        self.save()
        self.load_additional_sections()

    def _set_attribute(self, varname, value, default):
        """ Helper function to cast value type according to default value type
         from string and setting the ambient global variable of variable_name"""
        if type(default) in [list, dict, tuple]:  # load as json instead
            try:
                setattr(self,varname,json.loads(value.replace("'", '"')))
            except json.decoder.JSONDecodeError:
                setattr(self,varname,type(default)(value))
        else:
            try:
                setattr(self,varname,type(default)(value))
            except Exception as e:
                logger.warning("Error setting config variable %s, keeping old value: %s", varname, e)

    def get(self,key,default=None,section="GENERAL"):
        """gets config value string representation, if not possible
         creates it with the default value provided"""
        value = default
        try:
            value = self._parser.get(section,key)
        except ParserError as e:
            logger.warning("Error getting config %s from section %s: %s\nSetting default value: %s",key,
                  section,e,default)
            value = self._set(key,value,section=section)
        return str(value)

    def _set(self,option,value,section="GENERAL"):
        """ This is the internal set function which does not verify value protection """
        if not self._save_parser.has_section(section):
            self._save_parser.add_section(section)
        # decide wether we should save it as small json or regular string
        setval = value
        if type(value) in [list, dict, tuple]:  # save as json instead
            try:
                self._save_parser.set(section, option, json.dumps(value))
                setval = json.dumps(value)
            except json.decoder.JSONDecodeError:
                self._save_parser.set(section, option, str(value))
                setval = str(value)
        else:
            self._save_parser.set(section, option, str(value))
            setval = str(value)
        return setval

    def set(self,option,value,section="GENERAL"):
        """ For security only allow setting values that previously exist,
        also, do not allow setting protected values """
        if not self._parser.has_section(section):
            self._load() #probably just generated the config
        if self._parser.has_section(section) and\
            option in dict(self._parser.items(section))\
            and not option.startswith("_"):
            setval = self._set(option,value,section)
            self.save()
            self._load()
            return setval
        else:
            return False

    def save(self):
        """saves current configs (only the ones set with set() method)"""
        # Writing to last configuration file
        with open(os.path.join(self._script_dir, self._config_filename[-1]), 'w') as configfile:
            self._save_parser.write(configfile)

    def tostring(self,section="GENERAL"):
        """
        :return: Returns string representation of section configs
        """
        items = dict(self._parser.items(section))

        out = ""
        for k, v in items.items():
            if not k.startswith("_"):
                out += "{} : {}\n".format(k,v)
        return out


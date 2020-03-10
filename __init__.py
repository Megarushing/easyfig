""" Author: Megarushing
    This is a quick and dirty script to automate configuration persistence
    and accessibility throughout the system using python default config parser,
    the only thing you need to edit is the _default_values field for the default
    settings desired, you may do this by inheriting this class or modifying
    the variable before creating an instance.
    You can also provide a filename when instancing if you desire so,
    instead of the standard config.ini. If the file does not exist,
    it will be created with the default settings.
    Multiple file names are also possible, in which case all are used to load the
    settings in order, repeated settings take precedence on later files while
    only the last file is used for saving new settings"""
import os
import sys
import json
if sys.version_info >= (3, 0): #Python 3 configparser
    from configparser import ConfigParser
    from configparser import Error as ParserError
else:
    from ConfigParser import ConfigParser
    from ConfigParser import Error as ParserError

class Easyfig(object):
    # Here you should set all possible configs, and their default values
    # the exact config type will be inferred based on its default values type
    # every dict key will become a global variable under this lib for ease of access
    # NOTE: if config name starts with a _(underscore) it will be protected from the script
    # and only modifiable through manually editing the ini file
    _default_values = {
        "GENERAL" : {
            "example" : 1,
            "_protected_example": 0
        }
    }

    # set this function if you need to load additional custom sections not
    # controlled by this script
    def load_additional_sections(self):
        """ here you should treat the load of additional sections that require special treatment """
        pass

    # set this to the desired config file(s), this can be either a string or a list
    # of multiple strings, when multiple config files are detected, settings are
    # loaded from all files in order, but saved only to the last one
    def __init__(self,filename='config.ini'):
        """ loads the configuration file as fields in this object
            filename accepts both a list of config files to load or a single string"""
        self._config_filename = filename #updates config filename
        if type(self._config_filename) == str:
            self._config_filename = [self._config_filename]
        self._script_dir = os.path.dirname(os.path.realpath(__file__))
        self._parser = None
        self._save_parser = None
        self._load()

    def _load(self):
        # for saving we use only last file
        save_parser = ConfigParser()
        save_parser.read(os.path.join(self._script_dir, self._config_filename[-1]))
        #for loading we use all files
        parser = ConfigParser()
        for filename in self._config_filename:
            #loads all ini files, last one has precedence over first
            parser.read(os.path.join(self._script_dir,filename))

        #generates all global variables representing config sections
        for section,defaults in self._default_values.items():
            for option,default_value in defaults.items():
                varname = option
                if option.startswith("_"):
                    varname = option.replace("_","",1)
                    #if there is a config with same name remove it, only protected one stays
                    if varname in parser.items(section):
                        parser.remove_option(section=section,option=varname)
                    if varname in save_parser.items(section):
                        save_parser.remove_option(section=section,option=varname)
                if section != "GENERAL":
                    varname = section.lower() + "_" + varname
                #cast read string variable to type from default_values
                val = self.get(option,section=section,default=default_value)
                self._set_attribute(varname, val, default_value)
        self.save()
        self.load_additional_sections()

    def _set_attribute(self, varname, value, default):
        """ Helper function to cast value type according to default value type
         and setting the ambient global variable of variable_name"""
        if type(default) in [list, dict]:  # load as json instead
            try:
                setattr(self,varname,json.loads(value.replace("'", '"')))
            except json.decoder.JSONDecodeError:
                setattr(self,varname,type(default)(value))
        else:
            try:
                setattr(self,varname,type(default)(value))
            except Exception as e:
                print("Error setting config variable",varname,", setting default value:",str(default),"\n",e)

    def get(self,key,section="GENERAL",default=None):
        """gets config value from global config"""
        value = default
        try:
            value = self._parser.get(section,key)
        except ParserError as e:
            print("Error getting config",key,"from section",
                  section,":",e,"\nSetting default value:",default)
            if section != "GENERAL" and not self._save_parser.has_section(section):
                self._save_parser.add_section(section)
            if type(default) in [list, dict]:  # save as json instead
                try:
                    self._save_parser.set(section, key, json.dumps(value))
                    default = json.dumps(value)
                except json.decoder.JSONDecodeError:
                    self._save_parser.set(section, key, str(value))
            else:
                self._save_parser.set(section, key, str(value))
            value = default
        return str(value)

    def set(self,option,value,section="GENERAL"):
        if option in dict(self._parser.items(section)) and not option.startswith("_"):
            self._save_parser.set(section,option,value)
            self.save()
            self._load()
            return True
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


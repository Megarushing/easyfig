# easyfig
A simple yet powerful configurations automator based on python configparser and ini files



This is a simple script to automate configuration persistence
and accessibility throughout the system using python default config parser,
the only thing you need to edit is the defaults field for the default
settings desired, you may do this by inheriting this class or modifying
that field before creating an instance.
You can also provide a filename when instatiating if you desire so,
instead of the standard config.ini. If the file does not exist,
it will be created with the default settings.
Multiple file names in a list are also possible, in which case all are used to load the
settings in order, same settings take precedence on later files while
only the most precedent last file is used for saving new settings

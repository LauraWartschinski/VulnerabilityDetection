import glob
import logging
import os
import subprocess
from ConfigParser import ConfigParser

try:
    CONFIG_INI = os.path.abspath(glob.glob('mindfulness_config.ini')[0])
except:
    # try default path
    CONFIG_INI = '/opt/mindfulness/mindfulness_config.ini'


def read_config(section):
    parser = ConfigParser()
    parser.read(CONFIG_INI)
    config_params = {param[0]: param[1] for param in parser.items(section)}
    logging.info("Loaded %d parameters for section %s", len(config_params), section)
    return config_params


def remove_commas_from_string(input_string):
    return str(input_string).translate(None, ',')


def get_title_from_youtube_url(url):
    try:
        output = str(subprocess.check_output('youtube-dl --get-title %s --no-warnings' % url, stderr=subprocess.STDOUT,
                                             shell=True)).strip()
    except subprocess.CalledProcessError as ex:
        output = str(ex.output).strip()
    except OSError as ex:
        output = 'youtube-dl not found: %s' % ex
    except Exception as ex:
        output = 'Something bad happened: %s' % ex
    return remove_commas_from_string(output)


BASE_PATH = read_config('general')['path']

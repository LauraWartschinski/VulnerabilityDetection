import datetime
import os
import os.path
import urlparse
import socket
from time import localtime, strftime, time

from requests.exceptions import RequestException, ConnectionError, Timeout
import requests
import yaml

from monitoring_config_generator.exceptions import MonitoringConfigGeneratorException, HostUnreachableException
from monitoring_config_generator.yaml_tools.merger import merge_yaml_files

def is_file(parsed_uri):
    return parsed_uri.scheme in ['', 'file']


def is_host(parsed_uri):
    return parsed_uri.scheme in ['http', 'https']


def read_config(uri):
    uri_parsed = urlparse.urlparse(uri)
    if is_file(uri_parsed):
        return read_config_from_file(uri_parsed.path)
    elif is_host(uri_parsed):
        return read_config_from_host(uri)
    else:
        raise ValueError('Given url was not acceptable %s' % uri)


def read_config_from_file(path):
    yaml_config = merge_yaml_files(path)
    etag = None
    mtime = os.path.getmtime(path)
    return yaml_config, Header(etag=etag, mtime=mtime)


def read_config_from_host(url):
    try:
        response = requests.get(url)
    except socket.error as e:
        msg = "Could not open socket for '%s', error: %s" % (url, e)
        raise HostUnreachableException(msg)
    except ConnectionError as e:
        msg = "Could not establish connection for '%s', error: %s" % (url, e)
        raise HostUnreachableException(msg)
    except Timeout as e:
        msg = "Connect timed out for '%s', error: %s" % (url, e)
        raise HostUnreachableException(msg)
    except RequestException as e:
        msg = "Could not get monitoring yaml from '%s', error: %s" % (url, e)
        raise MonitoringConfigGeneratorException(msg)

    def get_from_header(field):
        return response.headers[field] if field in response.headers else None

    if response.status_code == 200:
        yaml_config = yaml.load(response.content)
        etag = get_from_header('etag')
        mtime = get_from_header('last-modified')
        mtime = datetime.datetime.strptime(mtime, '%a, %d %b %Y %H:%M:%S %Z').strftime('%s') if mtime else int(time())
    else:
        msg = "Request %s returned with status %s. I don't know how to handle that." % (url, response.status_code)
        raise MonitoringConfigGeneratorException(msg)

    return yaml_config, Header(etag=etag, mtime=mtime)


class Header(object):
    MON_CONF_GEN_COMMENT = '# Created by MonitoringConfigGenerator'
    ETAG_COMMENT = '# ETag: '
    MTIME_COMMMENT = '# MTime: '

    def __init__(self, etag=None, mtime=0):
        self.etag = etag
        self.mtime = int(mtime)

    def __nonzero__(self):
        return self.etag is None and self.mtime is 0

    def __eq__(self, other):
        return self.etag == other.etag and self.mtime == other.mtime

    def __repr__(self):
        return "Header(%s, %d)" % (self.etag, self.mtime)

    def is_newer_than(self, other):
        if self.etag != other.etag or self.etag is None:
            return cmp(self.mtime, other.mtime) > 0
        else:
            return False

    def serialize(self):
        lines = []
        time_string = strftime("%Y-%m-%d %H:%M:%S", localtime())
        lines.append("%s on %s" % (Header.MON_CONF_GEN_COMMENT, time_string))
        if self.etag:
            lines.append("%s%s" % (Header.ETAG_COMMENT, self.etag))
        if self.mtime:
            lines.append("%s%d" % (Header.MTIME_COMMMENT, self.mtime))
        return lines

    @staticmethod
    def parse(file_name):
        etag, mtime = None, 0

        def extract(comment, current_value):
            value = None
            if line.startswith(comment):
                value = line.rstrip()[len(comment):]
            return value or current_value

        try:
            with open(file_name, 'r') as config_file:
                for line in config_file.xreadlines():
                    etag = extract(Header.ETAG_COMMENT, etag)
                    mtime = extract(Header.MTIME_COMMMENT, mtime)
                    if etag and mtime:
                        break
        except IOError as e:
            # it is totally fine to not have an etag, in that case there
            # will just be no caching and the server will have to deliver the data again
            pass
        finally:
            return Header(etag=etag, mtime=mtime)

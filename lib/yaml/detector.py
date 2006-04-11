
__all__ = ['BaseDetector', 'Detector']

import re

class BaseDetector:

    yaml_detectors = {}

    def add_detector(cls, tag, regexp, first):
        if not 'yaml_detectors' in cls.__dict__:
            cls.yaml_detectors = cls.yaml_detectors.copy()
        for ch in first:
            cls.yaml_detectors.setdefault(ch, []).append((tag, regexp))
    add_detector = classmethod(add_detector)

    def detect(self, value):
        if value == u'':
            detectors = self.yaml_detectors.get(u'', [])
        else:
            detectors = self.yaml_detectors.get(value[0], [])
        detectors += self.yaml_detectors.get(None, [])
        for tag, regexp in detectors:
            if regexp.match(value):
                return tag

class Detector(BaseDetector):
    pass

Detector.add_detector(
        u'tag:yaml.org,2002:bool',
        re.compile(ur'''^(?:yes|Yes|YES|n|N|no|No|NO
                    |true|True|TRUE|false|False|FALSE
                    |on|On|ON|off|Off|OFF)$''', re.X),
        list(u'yYnNtTfFoO'))

Detector.add_detector(
        u'tag:yaml.org,2002:float',
        re.compile(ur'''^(?:[-+]?(?:[0-9][0-9_]*)?\.[0-9_]*(?:[eE][-+][0-9]+)?
                    |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*
                    |[-+]?\.(?:inf|Inf|INF)
                    |\.(?:nan|NaN|NAN))$''', re.X),
        list(u'-+0123456789.'))

Detector.add_detector(
        u'tag:yaml.org,2002:int',
        re.compile(ur'''^(?:[-+]?0b[0-1_]+
                    |[-+]?0[0-7_]+
                    |[-+]?(?:0|[1-9][0-9_]*)
                    |[-+]?0x[0-9a-fA-F_]+
                    |[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+)$''', re.X),
        list(u'-+0123456789'))

Detector.add_detector(
        u'tag:yaml.org,2002:merge',
        re.compile(ur'^(?:<<)$'),
        ['<'])

Detector.add_detector(
        u'tag:yaml.org,2002:null',
        re.compile(ur'''^(?: ~
                    |null|Null|NULL
                    | )$''', re.X),
        [u'~', u'n', u'N', u''])

Detector.add_detector(
        u'tag:yaml.org,2002:timestamp',
        re.compile(ur'''^(?:[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]
                    |[0-9][0-9][0-9][0-9] -[0-9][0-9]? -[0-9][0-9]?
                     (?:[Tt]|[ \t]+)[0-9][0-9]?
                     :[0-9][0-9] :[0-9][0-9] (?:\.[0-9]*)?
                     (?:[ \t]*(?:Z|[-+][0-9][0-9]?(?::[0-9][0-9])?))?)$''', re.X),
        list(u'0123456789'))

Detector.add_detector(
        u'tag:yaml.org,2002:value',
        re.compile(ur'^(?:=)$'),
        ['='])

# The following detector is only for documentation purposes. It cannot work
# because plain scalars cannot start with '!', '&', or '*'.
Detector.add_detector(
        u'tag:yaml.org,2002:yaml',
        re.compile(ur'^(?:!|&|\*)$'),
        list(u'!&*'))


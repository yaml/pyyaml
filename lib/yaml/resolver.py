
__all__ = ['BaseResolver', 'Resolver']

from error import *
from nodes import *

import re
import datetime

class ResolverError(YAMLError):
    pass

class timezone(datetime.tzinfo):
    def __init__(self, offset):
        maxoffset = datetime.timedelta(hours=24, microseconds=-1)
        minoffset = - maxoffset
        if not minoffset <= offset <= maxoffset:
            raise ValueError("offset must be a timedelta"
                             "strictly between -timedelta(hours=24) and "
                             "timedelta(hours=24).")
        self._offset = offset
        seconds = abs(offset).total_seconds()
        self._name = 'UTC%s%02d:%02d' % (
            '-' if offset.days < 0 else '+',
            seconds // 3600,
            seconds % 3600 // 60
        )

    def tzname(self, dt=None):
        return self._name

    def utcoffset(self, dt=None):
        return self._offset

    def dst(self, dt=None):
        return datetime.timedelta(0)

    __repr__ = __str__ = tzname

class BaseResolver(object):

    DEFAULT_SCALAR_TAG = u'tag:yaml.org,2002:str'
    DEFAULT_SEQUENCE_TAG = u'tag:yaml.org,2002:seq'
    DEFAULT_MAPPING_TAG = u'tag:yaml.org,2002:map'

    yaml_implicit_resolvers = {}
    yaml_path_resolvers = {}

    def __init__(self):
        self.resolver_exact_paths = []
        self.resolver_prefix_paths = []

    def add_implicit_resolver(cls, tag, regexp, first):
        if not 'yaml_implicit_resolvers' in cls.__dict__:
            implicit_resolvers = {}
            for key in cls.yaml_implicit_resolvers:
                implicit_resolvers[key] = cls.yaml_implicit_resolvers[key][:]
            cls.yaml_implicit_resolvers = implicit_resolvers
        if first is None:
            first = [None]
        for ch in first:
            cls.yaml_implicit_resolvers.setdefault(ch, []).append((tag, regexp))
    add_implicit_resolver = classmethod(add_implicit_resolver)

    def add_path_resolver(cls, tag, path, kind=None):
        # Note: `add_path_resolver` is experimental.  The API could be changed.
        # `new_path` is a pattern that is matched against the path from the
        # root to the node that is being considered.  `node_path` elements are
        # tuples `(node_check, index_check)`.  `node_check` is a node class:
        # `ScalarNode`, `SequenceNode`, `MappingNode` or `None`.  `None`
        # matches any kind of a node.  `index_check` could be `None`, a boolean
        # value, a string value, or a number.  `None` and `False` match against
        # any _value_ of sequence and mapping nodes.  `True` matches against
        # any _key_ of a mapping node.  A string `index_check` matches against
        # a mapping value that corresponds to a scalar key which content is
        # equal to the `index_check` value.  An integer `index_check` matches
        # against a sequence value with the index equal to `index_check`.
        if not 'yaml_path_resolvers' in cls.__dict__:
            cls.yaml_path_resolvers = cls.yaml_path_resolvers.copy()
        new_path = []
        for element in path:
            if isinstance(element, (list, tuple)):
                if len(element) == 2:
                    node_check, index_check = element
                elif len(element) == 1:
                    node_check = element[0]
                    index_check = True
                else:
                    raise ResolverError("Invalid path element: %s" % element)
            else:
                node_check = None
                index_check = element
            if node_check is str:
                node_check = ScalarNode
            elif node_check is list:
                node_check = SequenceNode
            elif node_check is dict:
                node_check = MappingNode
            elif node_check not in [ScalarNode, SequenceNode, MappingNode]  \
                    and not isinstance(node_check, basestring)  \
                    and node_check is not None:
                raise ResolverError("Invalid node checker: %s" % node_check)
            if not isinstance(index_check, (basestring, int))   \
                    and index_check is not None:
                raise ResolverError("Invalid index checker: %s" % index_check)
            new_path.append((node_check, index_check))
        if kind is str:
            kind = ScalarNode
        elif kind is list:
            kind = SequenceNode
        elif kind is dict:
            kind = MappingNode
        elif kind not in [ScalarNode, SequenceNode, MappingNode]    \
                and kind is not None:
            raise ResolverError("Invalid node kind: %s" % kind)
        cls.yaml_path_resolvers[tuple(new_path), kind] = tag
    add_path_resolver = classmethod(add_path_resolver)

    def descend_resolver(self, current_node, current_index):
        if not self.yaml_path_resolvers:
            return
        exact_paths = {}
        prefix_paths = []
        if current_node:
            depth = len(self.resolver_prefix_paths)
            for path, kind in self.resolver_prefix_paths[-1]:
                if self.check_resolver_prefix(depth, path, kind,
                        current_node, current_index):
                    if len(path) > depth:
                        prefix_paths.append((path, kind))
                    else:
                        exact_paths[kind] = self.yaml_path_resolvers[path, kind]
        else:
            for path, kind in self.yaml_path_resolvers:
                if not path:
                    exact_paths[kind] = self.yaml_path_resolvers[path, kind]
                else:
                    prefix_paths.append((path, kind))
        self.resolver_exact_paths.append(exact_paths)
        self.resolver_prefix_paths.append(prefix_paths)

    def ascend_resolver(self):
        if not self.yaml_path_resolvers:
            return
        self.resolver_exact_paths.pop()
        self.resolver_prefix_paths.pop()

    def check_resolver_prefix(self, depth, path, kind,
            current_node, current_index):
        node_check, index_check = path[depth-1]
        if isinstance(node_check, basestring):
            if current_node.tag != node_check:
                return
        elif node_check is not None:
            if not isinstance(current_node, node_check):
                return
        if index_check is True and current_index is not None:
            return
        if (index_check is False or index_check is None)    \
                and current_index is None:
            return
        if isinstance(index_check, basestring):
            if not (isinstance(current_index, ScalarNode)
                    and index_check == current_index.value):
                return
        elif isinstance(index_check, int) and not isinstance(index_check, bool):
            if index_check != current_index:
                return
        return True

    timestamp_regexp = re.compile(
            ur'''^(?P<year>[0-9][0-9][0-9][0-9])
                -(?P<month>[0-9][0-9]?)
                -(?P<day>[0-9][0-9]?)
                (?:(?:[Tt]|[ \t]+)
                (?P<hour>[0-9][0-9]?)
                :(?P<minute>[0-9][0-9])
                :(?P<second>[0-9][0-9])
                (?:\.(?P<fraction>[0-9]*))?
                (?:[ \t]*(?P<tz>Z|(?P<tz_sign>[-+])(?P<tz_hour>[0-9][0-9]?)
                (?::(?P<tz_minute>[0-9][0-9]))?))?)?$''', re.X)

    def generate_yaml_timestamp(self, value):
        match = self.timestamp_regexp.match(value)
        values = match.groupdict()
        year = int(values['year'])
        month = int(values['month'])
        day = int(values['day'])
        if not values['hour']:
            return datetime.date(year, month, day)
        hour = int(values['hour'])
        minute = int(values['minute'])
        second = int(values['second'])
        fraction = 0
        tzinfo = None
        if values['fraction']:
            fraction = values['fraction'][:6]
            while len(fraction) < 6:
                fraction += '0'
            fraction = int(fraction)
        if values['tz_sign']:
            tz_hour = int(values['tz_hour'])
            tz_minute = int(values['tz_minute'] or 0)
            delta = datetime.timedelta(hours=tz_hour, minutes=tz_minute)
            if values['tz_sign'] == '-':
                delta = -delta
            tzinfo = timezone(delta)
        elif values['tz']:
            tzinfo = timezone(datetime.timedelta(0))
        return datetime.datetime(year, month, day, hour, minute, second, fraction,
                                 tzinfo=tzinfo)

    def check_yaml_tag(self, tag, value):
        # if the timestamp is wrong. the tag:timestamp will be changed into tag:str
        if tag == u'tag:yaml.org,2002:timestamp':
            try:
                self.generate_yaml_timestamp(value)
            except:
                return False
        return True

    def resolve(self, kind, value, implicit):
        if kind is ScalarNode and implicit[0]:
            if value == u'':
                resolvers = self.yaml_implicit_resolvers.get(u'', [])
            else:
                resolvers = self.yaml_implicit_resolvers.get(value[0], [])
            resolvers += self.yaml_implicit_resolvers.get(None, [])
            for tag, regexp in resolvers:
                if regexp.match(value) and self.check_yaml_tag(tag, value):
                    return tag
            implicit = implicit[1]
        if self.yaml_path_resolvers:
            exact_paths = self.resolver_exact_paths[-1]
            if kind in exact_paths:
                return exact_paths[kind]
            if None in exact_paths:
                return exact_paths[None]
        if kind is ScalarNode:
            return self.DEFAULT_SCALAR_TAG
        elif kind is SequenceNode:
            return self.DEFAULT_SEQUENCE_TAG
        elif kind is MappingNode:
            return self.DEFAULT_MAPPING_TAG

class Resolver(BaseResolver):
    pass

Resolver.add_implicit_resolver(
        u'tag:yaml.org,2002:bool',
        re.compile(ur'''^(?:yes|Yes|YES|no|No|NO
                    |true|True|TRUE|false|False|FALSE
                    |on|On|ON|off|Off|OFF)$''', re.X),
        list(u'yYnNtTfFoO'))

Resolver.add_implicit_resolver(
        u'tag:yaml.org,2002:float',
        re.compile(ur'''^(?:[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+][0-9]+)?
                    |\.[0-9_]+(?:[eE][-+][0-9]+)?
                    |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*
                    |[-+]?\.(?:inf|Inf|INF)
                    |\.(?:nan|NaN|NAN))$''', re.X),
        list(u'-+0123456789.'))

Resolver.add_implicit_resolver(
        u'tag:yaml.org,2002:int',
        re.compile(ur'''^(?:[-+]?0b[0-1_]+
                    |[-+]?0[0-7_]+
                    |[-+]?(?:0|[1-9][0-9_]*)
                    |[-+]?0x[0-9a-fA-F_]+
                    |[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+)$''', re.X),
        list(u'-+0123456789'))

Resolver.add_implicit_resolver(
        u'tag:yaml.org,2002:merge',
        re.compile(ur'^(?:<<)$'),
        [u'<'])

Resolver.add_implicit_resolver(
        u'tag:yaml.org,2002:null',
        re.compile(ur'''^(?: ~
                    |null|Null|NULL
                    | )$''', re.X),
        [u'~', u'n', u'N', u''])

Resolver.add_implicit_resolver(
        u'tag:yaml.org,2002:timestamp',
        re.compile(ur'''^(?:[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]
                    |[0-9][0-9][0-9][0-9] -[0-9][0-9]? -[0-9][0-9]?
                     (?:[Tt]|[ \t]+)[0-9][0-9]?
                     :[0-9][0-9] :[0-9][0-9] (?:\.[0-9]*)?
                     (?:[ \t]*(?:Z|[-+][0-9][0-9]?(?::[0-9][0-9])?))?)$''', re.X),
        list(u'0123456789'))

Resolver.add_implicit_resolver(
        u'tag:yaml.org,2002:value',
        re.compile(ur'^(?:=)$'),
        [u'='])

# The following resolver is only for documentation purposes. It cannot work
# because plain scalars cannot start with '!', '&', or '*'.
Resolver.add_implicit_resolver(
        u'tag:yaml.org,2002:yaml',
        re.compile(ur'^(?:!|&|\*)$'),
        list(u'!&*'))


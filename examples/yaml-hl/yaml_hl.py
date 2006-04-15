#!/usr/bin/python

import yaml, codecs, sys, optparse



yaml.add_resolver(u'!Config', [])
yaml.add_resolver(u'!TokensConfig', [u'tokens'])
yaml.add_resolver(u'!EventsConfig', [u'events'])
yaml.add_resolver(u'!StartEndConfig', [u'tokens', None])
yaml.add_resolver(u'!StartEndConfig', [u'events', None])

class YAMLHighlight:

    def __init__(self, config):
        parameters = yaml.load_document(config)
        self.replaces = parameters['replaces']
        self.substitutions = {}
        for domain, items in [('Token', parameters['tokens']),
                    ('Event', parameters['events'])]:
            for code in items:
                name = ''.join([part.capitalize() for part in code.split('-')]+[domain])
                cls = getattr(yaml, name)
                value = items[code]
                if value:
                    if 'start' in value:
                        self.substitutions[cls, -1] = value['start']
                    if 'end' in value:
                        self.substitutions[cls, +1] = value['end']

    def highlight(self, input):
        if isinstance(input, str):
            if input.startswith(codecs.BOM_UTF16_LE):
                input = unicode(input, 'utf-16-le')
            elif input.startswith(codecs.BOM_UTF16_BE):
                input = unicode(input, 'utf-16-be')
            else:
                input = unicode(input, 'utf-8')
        tokens = yaml.parse(input, Parser=iter)
        events = yaml.parse(input)
        markers = []
        number = 0
        for token in tokens:
            number += 1
            if token.start_mark.index != token.end_mark.index:
                cls = token.__class__
                if (cls, -1) in self.substitutions:
                    markers.append([token.start_mark.index, +2, number, self.substitutions[cls, -1]])
                if (cls, +1) in self.substitutions:
                    markers.append([token.end_mark.index, -2, number, self.substitutions[cls, +1]])
        number = 0
        for event in events:
            number += 1
            cls = event.__class__
            if (cls, -1) in self.substitutions:
                markers.append([event.start_mark.index, +1, number, self.substitutions[cls, -1]])
            if (cls, +1) in self.substitutions:
                markers.append([event.end_mark.index, -1, number, self.substitutions[cls, +1]])
        markers.sort()
        markers.reverse()
        chunks = []
        position = len(input)
        for index, weight1, weight2, substitution in markers:
            if index < position:
                chunk = input[index:position]
                for substring, replacement in self.replaces:
                    chunk = chunk.replace(substring, replacement)
                chunks.append(chunk)
                position = index
            chunks.append(substitution)
        chunks.reverse()
        result = u''.join(chunks)
        return result.encode('utf-8')

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-c', '--config', dest='config', default='yaml_hl_ascii.cfg', metavar='CONFIG')
    (options, args) = parser.parse_args()
    hl = YAMLHighlight(file(options.config))
    sys.stdout.write(hl.highlight(sys.stdin.read()))


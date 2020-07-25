import os

default = 'application'

class Property(object):
    def __init__(self, environment=None):
        self.environment = environment
        if environment:
            self.environment = environment.lower()

    def name(self):
        if self.environment:
            return '{}-{}.yaml'.format(default, self.environment)
        return '{}.yaml'.format(default)

    def absoluteName(self):
        try:
            location = os.path.dirname(os.path.abspath(self.name()))
            return os.path.join(location, 'properties/{}'.format(self.name()))
        except:
            return None

import yaml

print(yaml.property('version'))
# output: 1.0
# found: properties/application.yaml

print(yaml.property('version', 'dev'))
# output: 2.0
# found: properties/application-dev.yaml

print(yaml.property('integration.python.port', 'dev'))
# output: 8080
# found: properties/application-dev.yaml

print(yaml.property('url', 'dev'))
# output: pyyaml.test.com
# not found: properties/application-dev.yaml
# found: properties/application.yaml


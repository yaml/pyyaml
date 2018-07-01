import yaml
import os

def myconstructor(loader, node):
    value = loader.construct_scalar(node)
    os.system("echo hello " + value)
    return value

yaml.Loader.add_constructor(u'!hello', myconstructor)

trusted_yaml = "mag: !hello world"

print("============ Loading trusted YAML")

data = yaml.load(trusted_yaml, Loader=yaml.Loader)
print(data)


# somewhere else in your application
untrusted_yaml = "mag: !hello evil"

print("============ Loading untrusted YAML")
try:
    safe_data = yaml.safe_load(untrusted_yaml)
    print(safe_data)
except yaml.constructor.ConstructorError as err:
    print("Could not load unsafe_yaml:")
    print(format(err))



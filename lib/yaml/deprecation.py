import warnings

class_deprecation_string = 'Instantiating or extending the unqualified {classname} class is deprecated as it will be removed in a later release. Please switch to explicitly using either Unsafe{classname} (for current behaviour) or Unsafe{classname} (for restricted functionality, more suitable for parsing suspect data)'

kwarg_deprecation_string = 'The {kwarg_name} keyword-arg is going to be removed from yaml.{source_fxn_name}, which will use the Safe{kwarg_name} exclusively. If you require the extra functionality of a more powerful (unsafe) {kwarg_name}, use yaml.unsafe_{source_fxn_name} behavior explicitly (read the docs to understand the safety implications if you are receiving yaml from an external source)'

def warn_if_nondefault(variable, sentinel, default, source_fxn_name,
        kwarg_name):
    if variable is sentinel:
        # the caller did not set the kwarg
        return default
    warnings.warn(kwarg_deprecation_string.format(
        source_fxn_name=source_fxn_name, kwarg_name=kwarg_name),
        DeprecationWarning)
    return variable

def warn_if_instantiated(classname):
    warnings.warn(class_deprecation_string.format(classname=classname),
            DeprecationWarning)

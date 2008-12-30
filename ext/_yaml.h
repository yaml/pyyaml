
#include <yaml.h>

#if PY_MAJOR_VERSION < 3

#define PyUnicode_FromString(s) PyUnicode_DecodeUTF8((s), strlen(s), 'strict')

#else

#define PyString_CheckExact PyBytes_CheckExact
#define PyString_AS_STRING  PyBytes_AS_STRING
#define PyString_GET_SIZE   PyBytes_GET_SIZE
#define PyString_FromStringAndSize  PyBytes_FromStringAndSize

#endif

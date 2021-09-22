
#include <yaml.h>

#if PY_MAJOR_VERSION < 3

#define PyUnicode_FromString(s) PyUnicode_DecodeUTF8((s), strlen(s), "strict")

#else

#ifndef PyString_CheckExact
#define PyString_CheckExact PyBytes_CheckExact
#endif
#define PyString_AS_STRING  PyBytes_AS_STRING
#define PyString_GET_SIZE   PyBytes_GET_SIZE
#define PyString_FromStringAndSize  PyBytes_FromStringAndSize

#endif

#define PyUnicode_FromYamlString(s) PyUnicode_FromString((const char *)(void *)(s))
#define PyString_AS_Yaml_STRING(s) ((yaml_char_t *)PyString_AS_STRING(s))

#ifdef _MSC_VER	/* MS Visual C++ 6.0 */
#if _MSC_VER == 1200

#define PyLong_FromUnsignedLongLong(z)	PyInt_FromLong(i)

#endif
#endif

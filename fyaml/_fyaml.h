
#include <libfyaml.h>

/* same as fy_event but cython doesn't do anonymous unions... yeah... */
/* NOTE that this must be kept in sync _manually_ */
/* ALSO all methods that take a fy_event * must be cast */
struct _fy_event {
	enum fy_event_type type;
	/* eponymous union */
	union {
		struct {
			struct fy_token *stream_start;
		} stream_start;

		struct {
			struct fy_token *stream_end;
		} stream_end;

		struct {
			struct fy_token *document_start;
			struct fy_document_state *document_state;
			bool implicit;
		} document_start;

		struct {
			struct fy_token *document_end;
			bool implicit;
		} document_end;

		struct {
			struct fy_token *anchor;
		} alias;

		struct {
			struct fy_token *anchor;
			struct fy_token *tag;
			struct fy_token *value;
			bool tag_implicit;
		} scalar;

		struct {
			struct fy_token *anchor;
			struct fy_token *tag;
			struct fy_token *sequence_start;
		} sequence_start;

		struct {
			struct fy_token *sequence_end;
		} sequence_end;

		struct {
			struct fy_token *anchor;
			struct fy_token *tag;
			struct fy_token *mapping_start;
		} mapping_start;

		struct {
			struct fy_token *mapping_end;
		} mapping_end;
	} data;
};

#ifdef _MSC_VER	/* MS Visual C++ 6.0 */
#if _MSC_VER == 1200

#define PyLong_FromUnsignedLongLong(z)	PyInt_FromLong(i)

#endif
#endif

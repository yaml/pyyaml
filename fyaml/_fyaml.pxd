
cdef extern from "_fyaml.h":

    void malloc(int l)
    void free(void *ptr)
    void memcpy(void *d, char *s, int l)
    void *memset(void *s, int c, size_t len)
    int strlen(char *s)
    int printf(const char *fmt, ...)

    int PyBytes_CheckExact(object o)
    int PyUnicode_CheckExact(object o)
    char *PyBytes_AS_STRING(object o)
    int PyBytes_GET_SIZE(object o)
    object PyBytes_FromStringAndSize(char *v, int l)
    object PyUnicode_FromString(char *u)
    object PyUnicode_DecodeUTF8(char *u, int s, char *e)
    object PyUnicode_AsUTF8String(object o)
    int PY_MAJOR_VERSION

    cdef struct fy_token:
        pass
    cdef struct fy_document_state:
        pass
    cdef struct fy_parser:
        pass
    cdef struct fy_emitter:
        pass
    cdef struct fy_document:
        pass
    cdef struct fy_node:
        pass
    cdef struct fy_node_pair:
        pass
    cdef struct fy_anchor:
        pass
    cdef struct fy_node_mapping_sort_ctx:
        pass
    cdef struct fy_token_iter:
        pass
    cdef struct fy_diag:
        pass
    cdef struct fy_path_parser:
        pass
    cdef struct fy_path_expr:
        pass
    cdef struct fy_path_exec:
        pass

    cdef struct fy_version:
        int major
        int minor
    cdef struct fy_tag:
        char* handle
        char* prefix
    cdef struct fy_mark:
        size_t input_pos
        int line
        int column

    cdef enum fy_error_type:
        FYET_DEBUG
        FYET_INFO
        FYET_NOTICE
        FYET_WARNING
        FYET_ERROR
        FYET_MAX

    cdef enum fy_error_module:
        FYEM_UNKNOWN
        FYEM_ATOM
        FYEM_SCAN
        FYEM_PARSE
        FYEM_DOC
        FYEM_BUILD
        FYEM_INTERNAL
        FYEM_SYSTEM
        FYEM_MAX

    cdef enum fy_parse_cfg_flags:
        FYPCF_QUIET                 =   1    # FY_BIT(0)
        FYPCF_COLLECT_DIAG          =   2    # FY_BIT(1)
        FYPCF_RESOLVE_DOCUMENT      =   4    # FY_BIT(2)
        FYPCF_DISABLE_MMAP_OPT      =   8    # FY_BIT(3)
        FYPCF_DISABLE_RECYCLING     =  16    # FY_BIT(4)
        FYPCF_PARSE_COMMENTS        =  32    # FY_BIT(5)
        FYPCF_DISABLE_DEPTH_LIMIT   =  64    # FY_BIT(6)
        FYPCF_DISABLE_ACCELERATORS  = 128    # FY_BIT(7)
        FYPCF_DISABLE_BUFFERING     = 256    # FY_BIT(8)
        FYPCF_DEFAULT_VERSION_AUTO	=      0 # 0 << 9
        FYPCF_DEFAULT_VERSION_1_1	=    512 # 1 << 9
        FYPCF_DEFAULT_VERSION_1_2	=   1024 # 2 << 9
        FYPCF_DEFAULT_VERSION_1_3	=   1536 # 3 << 9
        FYPCF_SLOPPY_FLOW_INDENTATION = 16384 # FY_BIT(14)
        FYPCF_JSON_AUTO             =      0 # 0 << 16
        FYPCF_JSON_NONE             =  65536 # 1 << 16
        FYPCF_JSON_FORCE            = 131072 # 2 << 16

    cdef struct fy_parse_cfg:
        char* search_path
        fy_parse_cfg_flags flags
        void* userdata
        fy_diag* diag

    cdef enum fy_event_type:
        FYET_NONE
        FYET_STREAM_START
        FYET_STREAM_END
        FYET_DOCUMENT_START
        FYET_DOCUMENT_END
        FYET_MAPPING_START
        FYET_MAPPING_END
        FYET_SEQUENCE_START
        FYET_SEQUENCE_END
        FYET_SCALAR
        FYET_ALIAS

    cdef enum fy_scalar_style:
        FYSS_ANY
        FYSS_PLAIN
        FYSS_SINGLE_QUOTED
        FYSS_DOUBLE_QUOTED
        FYSS_LITERAL
        FYSS_FOLDED
        FYSS_MAX

    cdef struct _fy_event_stream_start_s:
        fy_token* stream_start

    cdef struct _fy_event_stream_end_s:
        fy_token* stream_end

    cdef struct _fy_event_document_start_s:
        fy_token* document_start
        fy_document_state* document_state
        bint implicit

    cdef struct _fy_event_document_end_s:
        fy_token* document_end
        bint implicit

    cdef struct _fy_event_alias_s:
        fy_token* anchor

    cdef struct _fy_event_scalar_s:
        fy_token* anchor
        fy_token* tag
        fy_token* value
        bint tag_implicit

    cdef struct _fy_event_sequence_start_s:
        fy_token* anchor
        fy_token* tag
        fy_token* sequence_start

    cdef struct _fy_event_sequence_end_s:
        fy_token* sequence_end

    cdef struct _fy_event_mapping_start_s:
        fy_token* anchor
        fy_token* tag
        fy_token* mapping_start

    cdef struct _fy_event_mapping_end_s:
        fy_token* mapping_end

    cdef union _fy_event_u:
        _fy_event_stream_start_s stream_start
        _fy_event_stream_end_s stream_end
        _fy_event_document_start_s document_start
        _fy_event_document_end_s document_end
        _fy_event_alias_s alias
        _fy_event_scalar_s scalar
        _fy_event_sequence_start_s sequence_start
        _fy_event_sequence_end_s sequence_end
        _fy_event_mapping_start_s mapping_start
        _fy_event_mapping_end_s mapping_end

    cdef struct fy_event:
        fy_event_type type

    cdef struct _fy_event:
        fy_event_type type
        _fy_event_u data

    const char* fy_library_version()

    fy_error_type fy_string_to_error_type(char* str)

    char* fy_error_type_to_string(fy_error_type type)

    fy_error_module fy_string_to_error_module(char* str)

    char* fy_error_module_to_string(fy_error_module module)

    bint fy_event_is_implicit(fy_event* fye)

    bint fy_document_event_is_implicit(fy_event* fye)

    fy_parser* fy_parser_create(fy_parse_cfg* cfg)

    void fy_parser_destroy(fy_parser* fyp)

    fy_parse_cfg* fy_parser_get_cfg(fy_parser* fyp)

    fy_diag* fy_parser_get_diag(fy_parser* fyp)

    int fy_parser_set_diag(fy_parser* fyp, fy_diag* diag)

    int fy_parser_reset(fy_parser* fyp)

    int fy_parser_set_input_file(fy_parser* fyp, char* file)

    int fy_parser_set_string(fy_parser* fyp, char* str, size_t len)

    int fy_parser_set_malloc_string(fy_parser* fyp, char* str, size_t len)

    # int fy_parser_set_input_fp(fy_parser* fyp, char* name, FILE* fp)

    ctypedef ssize_t (*_fy_parser_set_input_callback_callback_ft)(void* user, void* buf, size_t count)

    int fy_parser_set_input_callback(fy_parser* fyp, void* user, _fy_parser_set_input_callback_callback_ft callback)

    fy_event* fy_parser_parse(fy_parser* fyp)

    void fy_parser_event_free(fy_parser* fyp, fy_event* fye)

    bint fy_parser_get_stream_error(fy_parser* fyp)

    fy_scalar_style fy_token_scalar_style(fy_token* fyt)

    char* fy_token_get_text(fy_token* fyt, size_t* lenp)

    char* fy_token_get_text0(fy_token* fyt)

    size_t fy_token_get_text_length(fy_token* fyt)

    size_t fy_token_get_utf8_length(fy_token* fyt)

    cdef struct fy_iter_chunk:
        char* str
        size_t len

    fy_token_iter* fy_token_iter_create(fy_token* fyt)

    void fy_token_iter_destroy(fy_token_iter* iter)

    void fy_token_iter_start(fy_token* fyt, fy_token_iter* iter)

    void fy_token_iter_finish(fy_token_iter* iter)

    fy_iter_chunk* fy_token_iter_peek_chunk(fy_token_iter* iter)

    fy_iter_chunk* fy_token_iter_chunk_next(fy_token_iter* iter, fy_iter_chunk* curr, int* errp)

    void fy_token_iter_advance(fy_token_iter* iter, size_t len)

    ssize_t fy_token_iter_read(fy_token_iter* iter, void* buf, size_t count)

    int fy_token_iter_getc(fy_token_iter* iter)

    int fy_token_iter_ungetc(fy_token_iter* iter, int c)

    int fy_token_iter_peekc(fy_token_iter* iter)

    int fy_token_iter_utf8_get(fy_token_iter* iter)

    int fy_token_iter_utf8_unget(fy_token_iter* iter, int c)

    int fy_token_iter_utf8_peek(fy_token_iter* iter)

    fy_document* fy_parse_load_document(fy_parser* fyp)

    void fy_parse_document_destroy(fy_parser* fyp, fy_document* fyd)

    int fy_document_resolve(fy_document* fyd)

    bint fy_document_has_directives(fy_document* fyd)

    bint fy_document_has_explicit_document_start(fy_document* fyd)

    bint fy_document_has_explicit_document_end(fy_document* fyd)

    fy_document* fy_node_document(fy_node* fyn)

    cdef enum fy_emitter_write_type:
        fyewt_document_indicator
        fyewt_tag_directive
        fyewt_version_directive
        fyewt_indent
        fyewt_indicator
        fyewt_whitespace
        fyewt_plain_scalar
        fyewt_single_quoted_scalar
        fyewt_double_quoted_scalar
        fyewt_literal_scalar
        fyewt_folded_scalar
        fyewt_anchor
        fyewt_tag
        fyewt_linebreak
        fyewt_alias
        fyewt_terminating_zero
        fyewt_plain_scalar_key
        fyewt_single_quoted_scalar_key
        fyewt_double_quoted_scalar_key
        fyewt_comment

    cdef enum fy_emitter_cfg_flags:
        FYECF_SORT_KEYS
        FYECF_OUTPUT_COMMENTS
        FYECF_STRIP_LABELS
        FYECF_STRIP_TAGS
        FYECF_STRIP_DOC
        FYECF_INDENT_DEFAULT
        FYECF_INDENT_1
        FYECF_INDENT_2
        FYECF_INDENT_3
        FYECF_INDENT_4
        FYECF_INDENT_5
        FYECF_INDENT_6
        FYECF_INDENT_7
        FYECF_INDENT_8
        FYECF_INDENT_9
        FYECF_WIDTH_DEFAULT
        FYECF_WIDTH_80
        FYECF_WIDTH_132
        FYECF_WIDTH_INF
        FYECF_MODE_ORIGINAL
        FYECF_MODE_BLOCK
        FYECF_MODE_FLOW
        FYECF_MODE_FLOW_ONELINE
        FYECF_MODE_JSON
        FYECF_MODE_JSON_TP
        FYECF_MODE_JSON_ONELINE
        FYECF_MODE_DEJSON
        FYECF_DOC_START_MARK_AUTO
        FYECF_DOC_START_MARK_OFF
        FYECF_DOC_START_MARK_ON
        FYECF_DOC_END_MARK_AUTO
        FYECF_DOC_END_MARK_OFF
        FYECF_DOC_END_MARK_ON
        FYECF_VERSION_DIR_AUTO
        FYECF_VERSION_DIR_OFF
        FYECF_VERSION_DIR_ON
        FYECF_TAG_DIR_AUTO
        FYECF_TAG_DIR_OFF
        FYECF_TAG_DIR_ON
        FYECF_DEFAULT

    cdef enum:
        FYECF_INDENT_SHIFT
        FYECF_INDENT_MASK
        FYECF_WIDTH_SHIFT
        FYECF_WIDTH_MASK

    ctypedef int (*_fy_emitter_cfg_output_ft)(fy_emitter* emit, fy_emitter_write_type type, const char* str, int len, void* userdata)

    cdef struct fy_emitter_cfg:
        fy_emitter_cfg_flags flags
        _fy_emitter_cfg_output_ft output
        void* userdata
        fy_diag* diag

    fy_emitter* fy_emitter_create(fy_emitter_cfg* cfg)

    void fy_emitter_destroy(fy_emitter* emit)

    fy_emitter_cfg* fy_emitter_get_cfg(fy_emitter* emit)

    fy_diag* fy_emitter_get_diag(fy_emitter* emit)

    int fy_emitter_set_diag(fy_emitter* emit, fy_diag* diag)

    int fy_emit_event(fy_emitter* emit, fy_event* fye)

    int fy_emit_document(fy_emitter* emit, fy_document* fyd)

    int fy_emit_document_start(fy_emitter* emit, fy_document* fyd, fy_node* fyn)

    int fy_emit_document_end(fy_emitter* emit)

    int fy_emit_node(fy_emitter* emit, fy_node* fyn)

    int fy_emit_root_node(fy_emitter* emit, fy_node* fyn)

    int fy_emit_explicit_document_end(fy_emitter* emit)

    # int fy_emit_document_to_fp(fy_document* fyd, fy_emitter_cfg_flags flags, FILE* fp)

    int fy_emit_document_to_file(fy_document* fyd, fy_emitter_cfg_flags flags, char* filename)

    int fy_emit_document_to_buffer(fy_document* fyd, fy_emitter_cfg_flags flags, char* buf, int size)

    char* fy_emit_document_to_string(fy_document* fyd, fy_emitter_cfg_flags flags)

    int fy_emit_node_to_buffer(fy_node* fyn, fy_emitter_cfg_flags flags, char* buf, int size)

    char* fy_emit_node_to_string(fy_node* fyn, fy_emitter_cfg_flags flags)

    fy_node* fy_node_copy(fy_document* fyd, fy_node* fyn_from)

    int fy_node_insert(fy_node* fyn_to, fy_node* fyn_from)

    int fy_document_insert_at(fy_document* fyd, char* path, size_t pathlen, fy_node* fyn)

    cdef enum fy_node_type:
        FYNT_SCALAR
        FYNT_SEQUENCE
        FYNT_MAPPING

    cdef enum fy_node_style:
        FYNS_ANY
        FYNS_FLOW
        FYNS_BLOCK
        FYNS_PLAIN
        FYNS_SINGLE_QUOTED
        FYNS_DOUBLE_QUOTED
        FYNS_LITERAL
        FYNS_FOLDED
        FYNS_ALIAS

    cdef enum fy_node_walk_flags:
        FYNWF_DONT_FOLLOW
        FYNWF_FOLLOW
        FYNWF_PTR_YAML
        FYNWF_PTR_JSON
        FYNWF_PTR_RELJSON
        FYNWF_URI_ENCODED
        FYNWF_MAXDEPTH_DEFAULT
        FYNWF_MARKER_DEFAULT
        FYNWF_PTR_DEFAULT

    fy_node_style fy_node_style_from_scalar_style(fy_scalar_style sstyle)

    ctypedef int (*fy_node_mapping_sort_fn)(fy_node_pair* fynp_a, fy_node_pair* fynp_b, void* arg)

    ctypedef int (*fy_node_scalar_compare_fn)(fy_node* fyn_a, fy_node* fyn_b, void* arg)

    bint fy_node_compare(fy_node* fyn1, fy_node* fyn2)

    bint fy_node_compare_user(fy_node* fyn1, fy_node* fyn2, fy_node_mapping_sort_fn sort_fn, void* sort_fn_arg, fy_node_scalar_compare_fn cmp_fn, void* cmp_fn_arg)

    bint fy_node_compare_string(fy_node* fyn, char* str, size_t len)

    fy_document* fy_document_create(fy_parse_cfg* cfg)

    void fy_document_destroy(fy_document* fyd)

    fy_parse_cfg* fy_document_get_cfg(fy_document* fyd)

    fy_diag* fy_document_get_diag(fy_document* fyd)

    int fy_document_set_diag(fy_document* fyd, fy_diag* diag)

    int fy_document_set_parent(fy_document* fyd, fy_document* fyd_child)

    fy_document* fy_document_build_from_string(fy_parse_cfg* cfg, char* str, size_t len)

    fy_document* fy_document_build_from_malloc_string(fy_parse_cfg* cfg, char* str, size_t len)

    fy_document* fy_document_build_from_file(fy_parse_cfg* cfg, char* file)

    # fy_document* fy_document_build_from_fp(fy_parse_cfg* cfg, FILE* fp)

    # fy_document* fy_document_vbuildf(fy_parse_cfg* cfg, char* fmt, va_list ap)

    fy_document* fy_document_buildf(fy_parse_cfg* cfg, char* fmt)

    fy_node* fy_document_root(fy_document* fyd)

    int fy_document_set_root(fy_document* fyd, fy_node* fyn)

    fy_node_type fy_node_get_type(fy_node* fyn)

    fy_node_style fy_node_get_style(fy_node* fyn)

    bint fy_node_is_scalar(fy_node* fyn)

    bint fy_node_is_sequence(fy_node* fyn)

    bint fy_node_is_mapping(fy_node* fyn)

    bint fy_node_is_alias(fy_node* fyn)

    bint fy_node_is_attached(fy_node* fyn)

    fy_token* fy_node_get_tag_token(fy_node* fyn)

    fy_token* fy_node_get_scalar_token(fy_node* fyn)

    fy_node* fy_node_resolve_alias(fy_node* fyn)

    fy_node* fy_node_dereference(fy_node* fyn)

    int fy_node_free(fy_node* fyn)

    fy_node* fy_node_build_from_string(fy_document* fyd, char* str, size_t len)

    fy_node* fy_node_build_from_malloc_string(fy_document* fyd, char* str, size_t len)

    fy_node* fy_node_build_from_file(fy_document* fyd, char* file)

    # fy_node* fy_node_build_from_fp(fy_document* fyd, FILE* fp)

    # fy_node* fy_node_vbuildf(fy_document* fyd, char* fmt, va_list ap)

    fy_node* fy_node_buildf(fy_document* fyd, char* fmt)

    fy_node* fy_node_by_path(fy_node* fyn, char* path, size_t len, fy_node_walk_flags flags)

    char* fy_node_get_path(fy_node* fyn)

    fy_node* fy_node_get_parent(fy_node* fyn)

    char* fy_node_get_parent_address(fy_node* fyn)

    char* fy_node_get_path_relative_to(fy_node* fyn_parent, fy_node* fyn)

    char* fy_node_get_short_path(fy_node* fyn)

    char* fy_node_get_reference(fy_node* fyn)

    fy_node* fy_node_create_reference(fy_node* fyn)

    char* fy_node_get_relative_reference(fy_node* fyn_base, fy_node* fyn)

    fy_node* fy_node_create_relative_reference(fy_node* fyn_base, fy_node* fyn)

    fy_node* fy_node_create_scalar(fy_document* fyd, char* data, size_t size)

    fy_node* fy_node_create_scalar_copy(fy_document* fyd, char* data, size_t size)

    # fy_node* fy_node_create_vscalarf(fy_document* fyd, char* fmt, va_list ap)

    fy_node* fy_node_create_scalarf(fy_document* fyd, char* fmt)

    fy_node* fy_node_create_sequence(fy_document* fyd)

    fy_node* fy_node_create_mapping(fy_document* fyd)

    int fy_node_set_tag(fy_node* fyn, char* data, size_t len)

    char* fy_node_get_tag(fy_node* fyn, size_t* lenp)

    char* fy_node_get_scalar(fy_node* fyn, size_t* lenp)

    char* fy_node_get_scalar0(fy_node* fyn)

    size_t fy_node_get_scalar_length(fy_node* fyn)

    size_t fy_node_get_scalar_utf8_length(fy_node* fyn)

    fy_node* fy_node_sequence_iterate(fy_node* fyn, void** prevp)

    fy_node* fy_node_sequence_reverse_iterate(fy_node* fyn, void** prevp)

    int fy_node_sequence_item_count(fy_node* fyn)

    bint fy_node_sequence_is_empty(fy_node* fyn)

    fy_node* fy_node_sequence_get_by_index(fy_node* fyn, int index)

    int fy_node_sequence_append(fy_node* fyn_seq, fy_node* fyn)

    int fy_node_sequence_prepend(fy_node* fyn_seq, fy_node* fyn)

    int fy_node_sequence_insert_before(fy_node* fyn_seq, fy_node* fyn_mark, fy_node* fyn)

    int fy_node_sequence_insert_after(fy_node* fyn_seq, fy_node* fyn_mark, fy_node* fyn)

    fy_node* fy_node_sequence_remove(fy_node* fyn_seq, fy_node* fyn)

    fy_node_pair* fy_node_mapping_iterate(fy_node* fyn, void** prevp)

    fy_node_pair* fy_node_mapping_reverse_iterate(fy_node* fyn, void** prevp)

    int fy_node_mapping_item_count(fy_node* fyn)

    bint fy_node_mapping_is_empty(fy_node* fyn)

    fy_node_pair* fy_node_mapping_get_by_index(fy_node* fyn, int index)

    fy_node* fy_node_mapping_lookup_by_string(fy_node* fyn, char* key, size_t len)

    fy_node_pair* fy_node_mapping_lookup_pair_by_simple_key(fy_node* fyn, char* key, size_t len)

    fy_node* fy_node_mapping_lookup_value_by_simple_key(fy_node* fyn, char* key, size_t len)

    char* fy_node_mapping_lookup_scalar_by_simple_key(fy_node* fyn, size_t* lenp, char* key, size_t keylen)

    char* fy_node_mapping_lookup_scalar0_by_simple_key(fy_node* fyn, char* key, size_t keylen)

    fy_node_pair* fy_node_mapping_lookup_pair(fy_node* fyn, fy_node* fyn_key)

    fy_node* fy_node_mapping_lookup_value_by_key(fy_node* fyn, fy_node* fyn_key)

    int fy_node_mapping_get_pair_index(fy_node* fyn, fy_node_pair* fynp)

    fy_node* fy_node_pair_key(fy_node_pair* fynp)

    fy_node* fy_node_pair_value(fy_node_pair* fynp)

    int fy_node_pair_set_key(fy_node_pair* fynp, fy_node* fyn)

    int fy_node_pair_set_value(fy_node_pair* fynp, fy_node* fyn)

    int fy_node_mapping_append(fy_node* fyn_map, fy_node* fyn_key, fy_node* fyn_value)

    int fy_node_mapping_prepend(fy_node* fyn_map, fy_node* fyn_key, fy_node* fyn_value)

    int fy_node_mapping_remove(fy_node* fyn_map, fy_node_pair* fynp)

    fy_node* fy_node_mapping_remove_by_key(fy_node* fyn_map, fy_node* fyn_key)

    int fy_node_sort(fy_node* fyn, fy_node_mapping_sort_fn key_cmp, void* arg)

    # int fy_node_vscanf(fy_node* fyn, char* fmt, va_list ap)

    int fy_node_scanf(fy_node* fyn, char* fmt)

    # int fy_document_vscanf(fy_document* fyd, char* fmt, va_list ap)

    int fy_document_scanf(fy_document* fyd, char* fmt)

    fy_token* fy_document_tag_directive_iterate(fy_document* fyd, void** prevp)

    fy_token* fy_document_tag_directive_lookup(fy_document* fyd, char* handle)

    char* fy_tag_directive_token_handle(fy_token* fyt, size_t* lenp)

    char* fy_tag_directive_token_prefix(fy_token* fyt, size_t* lenp)

    int fy_document_tag_directive_add(fy_document* fyd, char* handle, char* prefix)

    int fy_document_tag_directive_remove(fy_document* fyd, char* handle)

    fy_anchor* fy_document_lookup_anchor(fy_document* fyd, char* anchor, size_t len)

    fy_anchor* fy_document_lookup_anchor_by_token(fy_document* fyd, fy_token* anchor)

    fy_anchor* fy_document_lookup_anchor_by_node(fy_document* fyd, fy_node* fyn)

    char* fy_anchor_get_text(fy_anchor* fya, size_t* lenp)

    fy_node* fy_anchor_node(fy_anchor* fya)

    fy_anchor* fy_document_anchor_iterate(fy_document* fyd, void** prevp)

    int fy_document_set_anchor(fy_document* fyd, fy_node* fyn, char* text, size_t len)

    int fy_node_set_anchor(fy_node* fyn, char* text, size_t len)

    int fy_node_set_anchor_copy(fy_node* fyn, char* text, size_t len)

    # int fy_node_set_vanchorf(fy_node* fyn, char* fmt, va_list ap)

    int fy_node_set_anchorf(fy_node* fyn, char* fmt)

    int fy_node_remove_anchor(fy_node* fyn)

    fy_anchor* fy_node_get_anchor(fy_node* fyn)

    fy_anchor* fy_node_get_nearest_anchor(fy_node* fyn)

    fy_node* fy_node_get_nearest_child_of(fy_node* fyn_base, fy_node* fyn)

    fy_node* fy_node_create_alias(fy_document* fyd, char* alias, size_t len)

    fy_node* fy_node_create_alias_copy(fy_document* fyd, char* alias, size_t len)

    void* fy_node_get_meta(fy_node* fyn)

    int fy_node_set_meta(fy_node* fyn, void* meta)

    void fy_node_clear_meta(fy_node* fyn)

    ctypedef void (*fy_node_meta_clear_fn)(fy_node* fyn, void* meta, void* user)

    int fy_document_register_meta(fy_document* fyd, fy_node_meta_clear_fn clear_fn, void* user)

    void fy_document_unregister_meta(fy_document* fyd)

    bint fy_node_set_marker(fy_node* fyn, unsigned int marker)

    bint fy_node_clear_marker(fy_node* fyn, unsigned int marker)

    bint fy_node_is_marker_set(fy_node* fyn, unsigned int marker)

    # void fy_node_vreport(fy_node* fyn, fy_error_type type, char* fmt, va_list ap)

    void fy_node_report(fy_node* fyn, fy_error_type type, char* fmt)

    # void fy_node_override_vreport(fy_node* fyn, fy_error_type type, char* file, int line, int column, char* fmt, va_list ap)

    void fy_node_override_report(fy_node* fyn, fy_error_type type, char* file, int line, int column, char* fmt)

    ctypedef void (*fy_diag_output_fn)(fy_diag* diag, void* user, char* buf, size_t len)

    cdef struct fy_diag_cfg:
        void* fp        # was FILE*
        fy_diag_output_fn output_fn
        void* user
        fy_error_type level
        unsigned int module_mask
        bint colorize
        bint show_source
        bint show_position
        bint show_type
        bint show_module
        int source_width
        int position_width
        int type_width
        int module_width

    fy_diag* fy_diag_create(fy_diag_cfg* cfg)

    void fy_diag_destroy(fy_diag* diag)

    fy_diag_cfg* fy_diag_get_cfg(fy_diag* diag)

    void fy_diag_set_cfg(fy_diag* diag, fy_diag_cfg* cfg)

    void fy_diag_set_level(fy_diag* diag, fy_error_type level)

    void fy_diag_set_colorize(fy_diag* diag, bint colorize)

    fy_diag* fy_diag_ref(fy_diag* diag)

    void fy_diag_unref(fy_diag* diag)

    bint fy_diag_got_error(fy_diag* diag)

    void fy_diag_reset_error(fy_diag* diag)

    void fy_diag_cfg_default(fy_diag_cfg* cfg)

    void fy_diag_cfg_from_parser_flags(fy_diag_cfg* cfg, fy_parse_cfg_flags pflags)

    # int fy_diag_vprintf(fy_diag* diag, char* fmt, va_list ap)

    int fy_diag_printf(fy_diag* diag, char* fmt, ...)

    cdef struct fy_diag_ctx:
        fy_error_type level
        fy_error_module module
        char* source_func
        char* source_file
        int source_line
        char* file
        int line
        int column

    # int fy_vdiag(fy_diag* diag, fy_diag_ctx* fydc, char* fmt, va_list ap)

    int fy_diagf(fy_diag* diag, fy_diag_ctx* fydc, char* fmt)

    # void fy_diag_node_vreport(fy_diag* diag, fy_node* fyn, fy_error_type type, char* fmt, va_list ap)

    void fy_diag_node_report(fy_diag* diag, fy_node* fyn, fy_error_type type, char* fmt)

    # void fy_diag_node_override_vreport(fy_diag* diag, fy_node* fyn, fy_error_type type, char* file, int line, int column, char* fmt, va_list ap)

    void fy_diag_node_override_report(fy_diag* diag, fy_node* fyn, fy_error_type type, char* file, int line, int column, char* fmt)

    cdef enum fy_path_parse_cfg_flags:
        FYPPCF_QUIET
        FYPPCF_DISABLE_RECYCLING
        FYPPCF_DISABLE_ACCELERATORS

    cdef struct fy_path_parse_cfg:
        fy_path_parse_cfg_flags flags
        void* userdata
        fy_diag* diag

    fy_path_parser* fy_path_parser_create(fy_path_parse_cfg* cfg)

    void fy_path_parser_destroy(fy_path_parser* fypp)

    int fy_path_parser_reset(fy_path_parser* fypp)

    fy_path_expr* fy_path_parse_expr_from_string(fy_path_parser* fypp, char* str, size_t len)

    fy_path_expr* fy_path_expr_build_from_string(fy_path_parse_cfg* pcfg, char* str, size_t len)

    void fy_path_expr_free(fy_path_expr* expr)

    void fy_path_expr_dump(fy_path_expr* expr, fy_diag* diag, fy_error_type errlevel, int level, char* banner)

    cdef enum fy_path_exec_cfg_flags:
        FYPXCF_QUIET
        FYPXCF_DISABLE_RECYCLING
        FYPXCF_DISABLE_ACCELERATORS

    cdef struct fy_path_exec_cfg:
        fy_path_exec_cfg_flags flags
        void* userdata
        fy_diag* diag

    fy_path_exec* fy_path_exec_create(fy_path_exec_cfg* xcfg)

    void fy_path_exec_destroy(fy_path_exec* fypx)

    int fy_path_exec_reset(fy_path_exec* fypx)

    int fy_path_exec_execute(fy_path_exec* fypx, fy_path_expr* expr, fy_node* fyn_start)

    fy_node* fy_path_exec_results_iterate(fy_path_exec* fypx, void** prevp)

    cdef enum fy_token_type:
        FYTT_NONE
        FYTT_STREAM_START
        FYTT_STREAM_END
        FYTT_VERSION_DIRECTIVE
        FYTT_TAG_DIRECTIVE
        FYTT_DOCUMENT_START
        FYTT_DOCUMENT_END
        FYTT_BLOCK_SEQUENCE_START
        FYTT_BLOCK_MAPPING_START
        FYTT_BLOCK_END
        FYTT_FLOW_SEQUENCE_START
        FYTT_FLOW_SEQUENCE_END
        FYTT_FLOW_MAPPING_START
        FYTT_FLOW_MAPPING_END
        FYTT_BLOCK_ENTRY
        FYTT_FLOW_ENTRY
        FYTT_KEY
        FYTT_VALUE
        FYTT_ALIAS
        FYTT_ANCHOR
        FYTT_TAG
        FYTT_SCALAR
        FYTT_INPUT_MARKER
        FYTT_PE_SLASH
        FYTT_PE_ROOT
        FYTT_PE_THIS
        FYTT_PE_PARENT
        FYTT_PE_MAP_KEY
        FYTT_PE_SEQ_INDEX
        FYTT_PE_SEQ_SLICE
        FYTT_PE_SCALAR_FILTER
        FYTT_PE_COLLECTION_FILTER
        FYTT_PE_SEQ_FILTER
        FYTT_PE_MAP_FILTER
        FYTT_PE_EVERY_CHILD
        FYTT_PE_EVERY_CHILD_R
        FYTT_PE_ALIAS
        FYTT_PE_SIBLING
        FYTT_PE_COMMA
        FYTT_PE_BARBAR
        FYTT_PE_AMPAMP
        FYTT_PE_LPAREN
        FYTT_PE_RPAREN

    bint fy_token_type_is_valid(fy_token_type type)

    bint fy_token_type_is_yaml(fy_token_type type)

    bint fy_token_type_is_content(fy_token_type type)

    bint fy_token_type_is_path_expr(fy_token_type type)

    fy_token_type fy_token_get_type(fy_token* fyt)

    fy_mark* fy_token_start_mark(fy_token* fyt)

    fy_mark* fy_token_end_mark(fy_token* fyt)

    fy_token* fy_scan(fy_parser* fyp)

    void fy_scan_token_free(fy_parser* fyp, fy_token* fyt)

    char* fy_tag_directive_token_prefix0(fy_token* fyt)

    char* fy_tag_directive_token_handle0(fy_token* fyt)

    char* fy_tag_token_handle(fy_token* fyt, size_t* lenp)

    char* fy_tag_token_suffix(fy_token* fyt, size_t* lenp)

    char* fy_tag_token_handle0(fy_token* fyt)

    char* fy_tag_token_suffix0(fy_token* fyt)

    fy_version* fy_version_directive_token_version(fy_token* fyt)

    fy_scalar_style fy_scalar_token_get_style(fy_token* fyt)

    fy_tag* fy_tag_token_tag(fy_token* fyt)

    fy_tag* fy_tag_directive_token_tag(fy_token* fyt)

    fy_token* fy_event_get_token(fy_event* fye)

    fy_token* fy_event_get_anchor_token(fy_event* fye)

    fy_token* fy_event_get_tag_token(fy_event* fye)

    fy_mark* fy_event_start_mark(fy_event* fye)

    fy_mark* fy_event_end_mark(fy_event* fye)

    fy_node_style fy_event_get_node_style(fy_event* fye)

    fy_version* fy_document_start_event_version(fy_event* fye)

    fy_version* fy_document_state_version(fy_document_state* fyds)

    fy_mark* fy_document_state_start_mark(fy_document_state* fyds)

    fy_mark* fy_document_state_end_mark(fy_document_state* fyds)

    bint fy_document_state_version_explicit(fy_document_state* fyds)

    bint fy_document_state_tags_explicit(fy_document_state* fyds)

    bint fy_document_state_start_implicit(fy_document_state* fyds)

    bint fy_document_state_end_implicit(fy_document_state* fyds)

    fy_tag* fy_document_state_tag_directive_iterate(fy_document_state* fyds, void** prevp)

    bint fy_document_state_tag_is_default(fy_document_state* fyds, fy_tag* tag)

    fy_document_state* fy_parser_get_document_state(fy_parser* fyp)

    fy_document_state* fy_document_get_document_state(fy_document* fyd)

    fy_document_state* fy_emitter_get_document_state(fy_emitter* emit)

    fy_event* fy_emit_event_create(fy_emitter* emit, fy_event_type type, ...)

    # fy_event* fy_emit_event_vcreate(fy_emitter* emit, fy_event_type type, va_list ap)

    void fy_emit_event_free(fy_emitter* emit, fy_event* fye)

    fy_event* fy_parse_event_create(fy_parser* fyp, fy_event_type type)

    # fy_event* fy_parse_event_vcreate(fy_parser* fyp, fy_event_type type, va_list ap)

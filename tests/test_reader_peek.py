import io

import yaml
import yaml.reader


class TestReaderPeekBeyondBuffer:
    """Tests for Reader.peek() when index exceeds available data.

    Regression test for https://github.com/yaml/pyyaml/issues/904
    """

    def test_peek_beyond_end_returns_null(self):
        """peek() past end of a string stream should return '\\0', not raise IndexError."""
        reader = yaml.reader.Reader('abc')
        assert reader.peek(4) == '\0'

    def test_peek_at_null_terminator(self):
        """peek() at the exact position of the null terminator should return '\\0'."""
        reader = yaml.reader.Reader('abc')
        # buffer is 'abc\0', so index 3 is the '\0'
        assert reader.peek(3) == '\0'

    def test_peek_far_beyond_end(self):
        """peek() with a very large index should return '\\0'."""
        reader = yaml.reader.Reader('abc')
        assert reader.peek(100) == '\0'

    def test_peek_within_range(self):
        """peek() within range should still return the correct character."""
        reader = yaml.reader.Reader('abc')
        assert reader.peek(0) == 'a'
        assert reader.peek(1) == 'b'
        assert reader.peek(2) == 'c'

    def test_peek_empty_string(self):
        """peek() on an empty string should return '\\0'."""
        reader = yaml.reader.Reader('')
        assert reader.peek(0) == '\0'
        assert reader.peek(1) == '\0'

    def test_peek_beyond_end_bytes(self):
        """peek() past end of a bytes stream should return '\\0'."""
        reader = yaml.reader.Reader(b'abc')
        assert reader.peek(4) == '\0'

    def test_peek_beyond_end_file_stream(self):
        """peek() past end of a file-like stream should return '\\0'."""
        reader = yaml.reader.Reader(io.StringIO('abc'))
        assert reader.peek(4) == '\0'

    def test_loader_peek_beyond_end(self):
        """Original reproducer from issue #904."""
        obj = yaml.loader.Loader('abc')
        ret = obj.peek(4)
        assert ret == '\0'

import io

import yaml


def test_emit_tag_directive_with_percent_encoded_prefix_from_bytes():
    events = list(yaml.parse(io.BytesIO(b"%TAG ! tag:%002:\n---")))

    output = yaml.emit(events)

    assert output == "%TAG ! tag:%002:\n---\n...\n"
    assert list(yaml.parse(output))[1].tags == events[1].tags

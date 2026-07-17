from pyshef import parse_shef


def test_parse_dot_a_single_message():
    text = ".A ABCD 240717 Z DH1200/PPH 1.25/TAH 72"
    frame = parse_shef(text)
    assert len(frame) == 2
    assert list(frame["parameter"]) == ["PPH", "TAH"]
    assert list(frame["value"]) == ["1.25", "72"]
    assert set(frame["format"]) == {"A"}


def test_parse_dot_b_block_values_map_to_header_parameters():
    text = "\n".join(
        [
            ".B RIVER 240717 Z DH1200/PPH/TAH",
            "ABCD 1.1/70",
            "EFGH 0.5/69",
            ".END",
        ]
    )
    frame = parse_shef(text)
    assert len(frame) == 4
    assert list(frame["station"]) == ["ABCD", "ABCD", "EFGH", "EFGH"]
    assert list(frame["parameter"]) == ["PPH", "TAH", "PPH", "TAH"]


def test_parse_dot_e_series_values_track_sequence():
    text = ".E ABCD 240717 Z DH1200/DIH1/PPH/0.1/0.2/0.3"
    frame = parse_shef(text)
    assert len(frame) == 3
    assert list(frame["parameter"]) == ["PPH", "PPH", "PPH"]
    assert list(frame["value"]) == ["0.1", "0.2", "0.3"]
    assert list(frame["sequence"]) == [0, 1, 2]

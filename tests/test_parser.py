from pyshef import parse_shef


def test_parse_dot_a_single_message():
    text = ".A ABCD 240717 Z DH1200/PPH 1.25/TAH 72"
    frame = parse_shef(text)
    assert len(frame) == 2
    assert list(frame["parameter"]) == ["PPH", "TAH"]
    assert list(frame["value"]) == ["1.25", "72"]
    assert all(isinstance(v, str) for v in frame["value"])
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


def test_parse_dot_er_with_e_numbered_continuations():
    text = "\n".join(
        [
            "000",
            "FGUS55 KSTR 171541",
            "RVFMCT",
            "",
            "RIVER FORECAST",
            "NATIONAL WEATHER SERVICE",
            "COLORADO BASIN RIVER FORECAST CENTER SALT LAKE CITY UT",
            "1540  Fri Jul 17, 2026",
            "",
            ".ER BCTU1 0717 Z DH13/DC07171540/QRIFEZZ/DIH+01/",
            ".E1  0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 /",
            ".E2  0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 /",
            ".E3  0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 /",
            ".E4  0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 /",
            ".E5  0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 / 0.026 /",
            ".E6  0.026 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 /",
            ".E7  0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 /",
            ".E8  0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 /",
            ".E9  0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 /",
            ".E10  0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 /",
            ".E11  0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 / 0.025 /",
            ".ER DELU1 0717 Z DH13/DC07171540/QTIFEZZ/DIH+01/",
            ".E1  0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 /",
            ".E2  0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 /",
            ".E3  0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 /",
            ".E4  0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 /",
            ".E5  0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 /",
            ".E6  0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 /",
            ".E7  0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 /",
            ".E8  0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 /",
            ".E9  0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 /",
            ".E10  0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 /",
            ".E11  0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 / 0.000 /",
            "",
            "$$",
        ]
    )
    frame = parse_shef(text)
    assert len(frame) == 176
    assert set(frame["station"]) == {"BCTU1", "DELU1"}
    assert set(frame.loc[frame["station"] == "BCTU1", "parameter"]) == {"QRIFEZZ"}
    assert set(frame.loc[frame["station"] == "DELU1", "parameter"]) == {"QTIFEZZ"}
    assert list(frame.loc[frame["station"] == "BCTU1", "sequence"]) == list(range(88))
    assert list(frame.loc[frame["station"] == "DELU1", "sequence"]) == list(range(88))

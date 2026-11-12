import numpy as np
from equipop.categorical import categories_to_binary, parse_treat_spec


def test_parse_and_build(capsys):
    spec = parse_treat_spec("food: restaurant, cafe; pub")
    assert spec == {"food": ["restaurant", "cafe"], "pub": ["pub"]}
    cat = np.array(["restaurant", "cafe", "pub", "school", "pub"])
    pop, tr = categories_to_binary(cat, "food: restaurant, cafe; pub",
                                   pop_values=["restaurant", "cafe",
                                               "pub"])
    assert pop.tolist() == [True, True, True, False, True]
    assert tr["food"].tolist() == [1, 1, 0, 0, 0]
    assert tr["pub"].tolist() == [0, 0, 1, 0, 1]
    pop2, tr2 = categories_to_binary(cat, "ghost")
    assert "ZERO rows" in capsys.readouterr().out


def test_counts_without_a_population_are_refused():
    """Was a printed HINT until 1.37.1; now a refusal.

    Counts with no population mean N counts ROWS while T sums PEOPLE,
    so shares come out above 1. A hint that scrolls past the top of the
    Results window is not a guard - the external review of 1.36 found
    this reaching users as a plausible-looking number.
    """
    import pytest

    from equipop.stata_bridge import knn_to_rows
    rng = np.random.default_rng(3)
    x = rng.uniform(0, 2000, 200); y = rng.uniform(0, 2000, 200)
    counts = rng.integers(1, 30, 200).astype(float)   # looks like counts
    with pytest.raises(ValueError) as exc:
        knn_to_rows(x, y, [10], treat={"grp": counts},
                    treat_are_counts=True)
    assert "no population" in str(exc.value)


# ----------------------------------------------------- BACKLOG 467
def test_labels_write_a_number_as_a_person_does():
    """BROKEN WITH: astype(str) - 1.0 reads "1.0" and a missing number
    reads "nan", a type of its own."""
    import numpy as np
    from equipop.categorical import labels, known
    assert list(labels(np.array([1.0, 2.0, 2.5, np.nan]))) == \
        ["1", "2", "2.5", ""]
    assert list(labels(np.array([3, 1, 2]))) == ["3", "1", "2"]
    assert list(labels(np.array([" cafe ", "", "bar"]))) == \
        ["cafe", "", "bar"]
    # value by value, as a GIS attribute list arrives
    assert list(labels(np.array([1, 2.0, None, float("nan")],
                                dtype=object))) == ["1", "2", "", ""]
    assert list(labels(np.array(["1", "010", None, "3a"],
                                dtype=object))) == ["1", "010", "", "3a"]
    assert known(np.array([3.0, 1.0, np.nan, 1.0])) == ["1", "3"]
    assert known(np.array(["b", "", "a", "b"])) == ["a", "b"]


def test_a_missing_number_is_in_no_group_not_even_the_rest():
    """A number column with a hole in it (how Pro hands a numeric type
    field over). The row with no type was "nan" and fell in 'other'.
    BROKEN WITH: "nan" for a missing number in _labels."""
    import numpy as np
    col = np.array([1.0, 2.0, np.nan, 3.0])
    pop, treats = categories_to_binary(col, {"one": ["1"]},
                                       rest_group="other",
                                       rest_in_population=None)
    assert list(treats["one"]) == [1.0, 0.0, 0.0, 0.0]
    assert list(treats["other"]) == [0.0, 1.0, 0.0, 1.0]
    assert pop.all()        # still a row of the population


def test_what_is_typed_meets_the_column_in_the_columns_form():
    """Against NUMBERS: 1, 1.0, 01 and 1,0 are the number one.
    Against TEXT: exactly what is written - "010" is not "10"."""
    import numpy as np
    from equipop.categorical import unknown, matcher
    numbers = np.array([1.0, 2.0, 10.0])
    assert unknown(["1", "1.0", "01", "1,0", "'2'", "10"], numbers) == []
    assert unknown(["4", "x", "nan", ""], numbers) == ["4", "x", "nan"]
    text = np.array(["1", "010", "3a"])
    assert unknown(["1", "010", "3a"], text) == []
    assert unknown(["10", "1.0", "3A"], text) == ["10", "1.0", "3A"]
    assert matcher(numbers)("1.0") == "1"
    assert matcher(text)("1.0") == "1.0"
    # and the engine itself matches the same way
    pop, treats = categories_to_binary(numbers, {"g": ["1.0", "10"]},
                                       pop_values=["1", "2", "10.0"])
    assert pop.all() and list(treats["g"]) == [1.0, 0.0, 1.0]


def test_the_refusal_names_field_values_and_box():
    from equipop.doors.rungs import not_in_field
    said = not_in_field(["castle"], "fclass", ["bar", "cafe"], "Box 1c")
    assert "Box 1c" in said and "castle" in said and "'fclass'" in said
    assert "bar, cafe" in said
    many = not_in_field([str(i) for i in range(20)], "f",
                        [f"v{i:02d}" for i in range(30)], "Box 2c")
    assert "20 type(s)" in many and "30 different value(s)" in many
    assert many.count("...") == 2

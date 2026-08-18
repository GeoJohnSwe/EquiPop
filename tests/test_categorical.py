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

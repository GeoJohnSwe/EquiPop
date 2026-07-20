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


def test_counts_hint_fires(capsys):
    from equipop.stata_bridge import knn_to_rows
    rng = np.random.default_rng(3)
    x = rng.uniform(0, 2000, 200); y = rng.uniform(0, 2000, 200)
    counts = rng.integers(1, 30, 200).astype(float)   # looks like counts
    knn_to_rows(x, y, [10], treat={"grp": counts})
    assert "HINT" in capsys.readouterr().out

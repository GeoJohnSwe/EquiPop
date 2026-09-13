"""
selfrule.py - is the origin its own neighbour? (BACKLOG 290).

THE PROBLEM. EquiPop grows a neighbourhood outward from each origin
until it holds k people, and it has always started counting AT THE
ORIGIN CELL. Your own cell's people are your nearest neighbours, and
they include you.

For an accessibility question that is right: people standing at the
clinic can reach the clinic. For a composition question it puts the
origin's own value on both sides of the comparison, and for a spatial
weights matrix W it is not merely unhelpful but wrong by convention -
SAR, SDM and SLX all require w_ii = 0, and `autocorr.build_weights()`
has always excluded self while the counting machines have always
included it. TWO NEIGHBOURHOOD DEFINITIONS IN ONE PACKAGE, both called
"the neighbourhood". That is what this module ends.

MEASURED, NOT ARGUED. On CaliData2010 - John's own five-county Los
Angeles blocks, the data behind Osth, Clark and Malmberg (2015) - the
package reproduces the published spatial isolation at k=100 to within
0.001: African Americans 0.2752 against Figure 4's ~0.28, Asians
0.3325 against ~0.33. Re-running with the origin block excluded:

    group              include   exclude    shift
    African American    0.2765    0.2394   -13.4%
    Asian               0.3335    0.3024    -9.3%
    White               0.6323    0.6267    -0.9%

THE SHIFT IS NOT UNIFORM AND THAT IS THE POINT. Minority members live
disproportionately in blocks where their group is concentrated, so
their own block is a large part of their measured isolation. For a
63% majority the neighbourhood is White either way. Self-inclusion
therefore INFLATES MINORITY ISOLATION RELATIVE TO MAJORITY, and the
size of the inflation depends on how many people a unit holds.

It also bends the SCALE PROFILE, which is the more serious finding.
Across k = 100, 200, 400, 800 on the same data:

    African American, include   0.2765 -> 0.2525   (falls 0.0240)
    African American, exclude   0.2394 -> 0.2357   (falls 0.0037)

Six times less decline. Over that range the origin block shrinks from
roughly all of the neighbourhood to about a seventh of it, so most of
the slope at small k is THE ORIGIN BLOCK BEING DILUTED rather than the
surrounding composition changing. Mean block population in that
extract is 113 people and 35.6% of blocks hold 100 or more, so at
k=100 the "hundred nearest neighbours" IS the origin block and nothing
else for over a third of the region.

None of this touches the macroscale conclusions of the 2015 paper. By
k=6,400 and certainly by 51,200 the origin block is negligible and the
decline there is real. What it qualifies is the steep microscale end,
and the reading of k=100 as "a local neighbourhood" when for a third
of blocks it is one block.

WHY THE DEFAULT DOES NOT CHANGE, ruled by John, 1.47: every number in
the published literature - his 2015 paper included - was computed with
self included. A silent flip would break the correspondence between
this software and the papers that describe it. `include` stays, and
anyone who wants w_ii = 0 asks for it.

THE THIRD RULE THAT WAS CONSIDERED AND DROPPED. An intermediate rule
was designed and tested: remove ONE AVERAGE RESIDENT of the origin
cell, n' = n - 1 and t' = t - t/n. It has attractive properties - it
preserves the origin cell's own balance exactly (10 people of whom 1
is treated give 0.1000, not 1/9 = 0.1111), it IS the expectation of
suppressing a random individual (0.0999 over 200,000 draws), and the
same formula collapses correctly on individual-level rows where n=1
and the row simply vanishes. It was dropped because it does nothing.
On the LA blocks it moved isolation from 0.2765 to 0.2764. Removing
one person from a unit of 113 is noise; the contamination is your
CELL-MATES, not you. Kept here because the next session to reinvent
it should find the measurement rather than repeat the work.

WHAT EXCLUSION INTERACTS WITH:

  - SELF-POTENTIAL (selfpot.py, BACKLOG 95) has nothing to act on when
    the origin cell contributes no mass. It is not an error to pass
    both; the self-potential simply has no effect, and a run says so.
  - An ISOLATED origin - no other populated cell within reach - counts
    nobody. N_k comes back 0 and every share is undefined rather than
    invented. That is a real answer to "who is around me, not counting
    me", and it is why the column is not silently filled.
  - N_local and <var>_local are facts about THE CELL, not about the
    neighbourhood, so they are unchanged by this rule.
"""

INCLUDE = "include"
EXCLUDE = "exclude"

RULES = (INCLUDE, EXCLUDE)

#: What EquiPop does unless told otherwise.
#:
#: RULED BY JOHN, 1.47: include. Not because it is the better answer
#: for every question - for a regression it is the worse one - but
#: because it is the PUBLISHED one. Changing it would silently
#: invalidate the correspondence between this package and Osth, Clark
#: and Malmberg (2015), and a user who reproduced Figure 4 last year
#: would get different numbers with no message telling them why.
DEFAULT = INCLUDE

#: The rule a spatial weights matrix needs. `autocorr.build_weights()`
#: has always done this; it is named here so the two paths can be
#: shown to agree rather than merely asserted to.
WEIGHTS_RULE = EXCLUDE

CHOICES = {
    INCLUDE: (
        "Include the origin - your own cell's people are your nearest "
        "neighbours, and they include you. This is what EquiPop has "
        "always done and what every published EquiPop result used. "
        "Right for accessibility questions: people at the clinic can "
        "reach the clinic. It puts the origin's own composition inside "
        "its own neighbourhood, which inflates measured isolation, "
        "most for concentrated minorities and least for the majority."),
    EXCLUDE: (
        "Exclude the origin cell - count who is around you, NOT "
        "counting you or anyone sharing your cell. This is the "
        "w_ii = 0 convention that spatial regression requires (SAR, "
        "SDM, SLX) and what EquiPop's own weights builder has always "
        "used. Choose it for composition and regression work. On "
        "coarse units it changes results substantially: on US census "
        "blocks averaging 113 people, isolation at k=100 fell 13.4% "
        "for African Americans and 0.9% for Whites."),
}


def resolve(rule):
    """Normalise and check a rule name. None means the default."""
    if rule is None:
        return DEFAULT
    r = str(rule).strip().lower()
    # The two spellings people actually reach for. i==j and i!=j is
    # John's own wording for this and appears in the Tartu slides;
    # "self"/"drop_self" is what the first draft of the option used.
    aliases = {"i=j": INCLUDE, "i==j": INCLUDE, "self": INCLUDE,
               "included": INCLUDE, "with_self": INCLUDE,
               "i!=j": EXCLUDE, "i<>j": EXCLUDE, "ine j": EXCLUDE,
               "i ne j": EXCLUDE, "excluded": EXCLUDE,
               "drop_self": EXCLUDE, "no_self": EXCLUDE,
               "without_self": EXCLUDE, "drop_cell": EXCLUDE}
    r = aliases.get(r, r)
    if r not in RULES:
        raise ValueError(
            f"[selfrule] '{rule}' is not one of {', '.join(RULES)}. "
            "This decides whether the origin cell counts as its own "
            "neighbour - see the manual. Nothing was computed.")
    return r


def excludes_self(rule) -> bool:
    """True when the origin cell must contribute nothing."""
    return resolve(rule) == EXCLUDE


def label(rule) -> str:
    """The short phrase that goes in a manifest or a column note."""
    return ("origin cell included (i=j)" if resolve(rule) == INCLUDE
            else "origin cell excluded (i!=j)")


def message(rule, self_potential=None) -> str:
    """What a run prints, so the choice is never invisible.

    THIS IS NOT DECORATION. The means barely move - on Gridby the
    neighbourhood share was identical to three decimals under both
    rules at every k - so a user CANNOT TELL FROM THE NUMBERS which
    rule produced them. If the run does not say, the result becomes
    unreproducible the moment it is copied into a paper.
    """
    r = resolve(rule)
    if r == INCLUDE:
        return ("[self] origin cell INCLUDED in its own neighbourhood "
                "(i=j), as in every published EquiPop result.")
    out = ["[self] origin cell EXCLUDED from its own neighbourhood "
           "(i!=j) - the w_ii = 0 convention. Results are NOT "
           "comparable with runs made under the default."]
    if self_potential:
        out.append("[self] self-potential has no effect under this "
                   "rule: the origin contributes no people for it to "
                   "place. It was not ignored silently.")
    return "\n".join(out)

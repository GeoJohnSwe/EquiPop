*! equipop_knn v1.35  -  ALIAS. The command is now called -equipop-.
*!
*! Kept working so that do-files written against v1.0-v1.34 keep
*! running unchanged. It forwards everything, untouched, to equipop.
*! John's ruling, 1.34 session: the name changed because radius runs
*! exist, and asking for a radius under a _knn name reads oddly.
*!
*! Everything - syntax, options, output columns - is documented in
*! equipop.ado. There is no behaviour here.

program define equipop_knn
    version 17
    display as text "note: equipop_knn is now called -equipop-. " ///
        "The old name still works."
    equipop `0'
end

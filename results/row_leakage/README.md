# row_leakage

What a shared head's row carries about the client that decided it. The merge is
coverage weighted, so a class held by one client has a row equal to that client's
displacement with no dilution. For a linear layer with a bias the ratio of the
row displacement to the bias displacement is a weighted mean of that client's
features (Phong et al., IEEE TIFS 2018, O1). This measures whether the ratio
points at the class, and whether it points at a record.

A low `hit_at_1` is the result worth reporting: the row would then carry a class
direction and not a training example.

Produced by `jobs/row_leakage.py`, submitted with `jobs/row_leakage.sh`.

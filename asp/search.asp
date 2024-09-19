edge_type(1..edge_types).
solution_index(1..2).
one_or_two(1..2).

s1_side_points_towards(Loc, 1, north) :- is_interior_location(Loc).
s1_side_points_towards(Loc, 1, H) :- edge_side1_points_towards(Loc, H).
s1_side_points_towards(Loc, S, H2) :-
    s1_side_points_towards(Loc, S - 1, H1);
    piece_side(S);
    step_clockwise(H1, H2).

positive_heading(north; east).
s1_positive_side(s1_loc(Loc), S) :- s1_side_points_towards(Loc, S, H); positive_heading(H).

s1_complementing(edge_of(Loc1, S1), edge_of(Loc2, S2)) :-
    adjacent_on(Loc1, Loc2, H1);
    positive_heading(H1);
    opposite_heading(H1, H2);
    s1_side_points_towards(Loc1, S1, H1);
    s1_side_points_towards(Loc2, S2, H2).

% Remove some symmetries by fully specifying one edge between two perimeter pieces and mostly specifying an
% edge to an interior piece (they may or may not be of the same kind).
has_edge(s1_loc(location(1, 1)), edge_descriptor(1, inny), 3).
{has_edge(s1_loc(location(1, 2)), edge_descriptor(E, inny), 3) : one_or_two(E)} = 1.
{has_edge(Piece, D, S) : is_descriptor(D)} = 1 :- s1_positive_side(Piece, S); not is_smooth_side(Piece, S).
has_edge(s1_loc(Loc2), D2, S2) :-
    has_edge(s1_loc(Loc1), D1, S1);
    s1_complementing(edge_of(Loc1, S1), edge_of(Loc2, S2));
    complementary(D1, D2).
:- #count{Piece, S : has_edge(Piece, edge_descriptor(E, inny), S)} < min_usage_count; edge_type(E).

in_location(s1_loc(Loc), Loc, 1) :- is_location(Loc).

#maximize{1,PE1,PE2 : joined(PE1, PE2, _)}.

#show has_edge/3.

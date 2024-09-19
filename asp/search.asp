interior_edge_type(1..int_edge_types).
exterior_edge_type(int_edge_types + 1..int_edge_types + ext_edge_types).
edge_type(E) :- interior_edge_type(E).
edge_type(E) :- exterior_edge_type(E).
solution_index(1..2).
one_or_two(1..2).

s1_side_points_towards(Loc, 1, north) :- is_interior_location(Loc).
s1_side_points_towards(Loc, 1, H) :- edge_side1_points_towards(Loc, H).
s1_side_points_towards(Loc, S, H2) :-
    s1_side_points_towards(Loc, S - 1, H1);
    piece_side(S);
    step_clockwise(H1, H2).

positive_heading(north; east).

s1_complementing(edge_of(Loc1, S1), edge_of(Loc2, S2)) :-
    adjacent_on(Loc1, Loc2, H1);
    positive_heading(H1);
    opposite_heading(H1, H2);
    s1_side_points_towards(Loc1, S1, H1);
    s1_side_points_towards(Loc2, S2, H2).
interior_side(edge_of(Loc1, S)) :-
    s1_complementing(edge_of(Loc1, S), edge_of(_, _));
    is_interior_location(Loc1).
interior_side(edge_of(Loc1, S)) :-
    s1_complementing(edge_of(Loc1, S), edge_of(Loc2, _));
    is_interior_location(Loc2).
exterior_side(edge_of(Loc1, S)) :-
    s1_complementing(edge_of(Loc1, S), edge_of(Loc2, _));
    not is_interior_location(Loc1);
    not is_interior_location(Loc2).

% Remove some symmetries by specifying one interior edge and one exterior edge.
has_edge(s1_loc(location(1, 2)), edge_descriptor(1, inny), 3).
has_edge(s1_loc(location(1, 1)), edge_descriptor(int_edge_types + 1, inny), 3).
{has_edge(s1_loc(Loc), edge_descriptor(E, P), S) : interior_edge_type(E), polarity(P)} = 1 :-
    interior_side(edge_of(Loc, S)).
{has_edge(s1_loc(Loc), edge_descriptor(E, P), S) : exterior_edge_type(E), polarity(P)} = 1 :-
    exterior_side(edge_of(Loc, S)).
has_edge(s1_loc(Loc2), D2, S2) :-
    has_edge(s1_loc(Loc1), D1, S1);
    s1_complementing(edge_of(Loc1, S1), edge_of(Loc2, S2));
    complementary(D1, D2).
:- #count{Piece, S : has_edge(Piece, edge_descriptor(E, inny), S)} < min_usage_count; edge_type(E).

in_location(s1_loc(Loc), Loc, 1) :- is_location(Loc).

#maximize{1,PE1,PE2 : joined(PE1, PE2, _)}.

#show has_edge/3.

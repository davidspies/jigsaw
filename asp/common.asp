% Shared rules for search and solve.

is_location(location(1..5, 1..5)).
is_interior_location(location(2..4, 2..4)).
is_edge_location(location((1; 5), 2..4)).
is_edge_location(location(2..4, (1; 5))).
is_corner_location(location((1; 5), (1; 5))).
is_puzzle_piece(s1_loc(Loc)) :- is_location(Loc).
is_interior_piece(s1_loc(Loc)) :- is_interior_location(Loc).
is_edge_piece(s1_loc(Loc)) :- is_edge_location(Loc).
is_corner_piece(s1_loc(Loc)) :- is_corner_location(Loc).

heading(north; east; south; west).
step_clockwise(north, east; east, south; south, west; west, north).
opposite_heading(north, south; east, west; south, north; west, east).
piece_side(1..4). % Arranged clockwise.
polarity(inny; outy).

is_smooth_side(P, 1) :- is_edge_piece(P).
is_smooth_side(P, 1..2) :- is_corner_piece(P).

is_descriptor(edge_descriptor(E, P)) :- edge_type(E); polarity(P).
complementary(edge_descriptor(E, P1), edge_descriptor(E, P2)) :- edge_type(E); polarity(P1); polarity(P2); P1 != P2.

adjacent_on(location(X, Y), location(X + 1, Y), east) :- is_location(location(X, Y)); is_location(location(X + 1, Y)).
adjacent_on(location(X, Y), location(X, Y + 1), north) :- is_location(location(X, Y)); is_location(location(X, Y + 1)).
adjacent_on(location(X, Y), location(X - 1, Y), west) :- is_location(location(X, Y)); is_location(location(X - 1, Y)).
adjacent_on(location(X, Y), location(X, Y - 1), south) :- is_location(location(X, Y)); is_location(location(X, Y - 1)).

edge_side1_points_towards(location(X, 1), south) :- is_location(location(X, 1)); X < 5.
edge_side1_points_towards(location(1, Y), west) :- is_location(location(1, Y)); Y > 1.
edge_side1_points_towards(location(X, 5), north) :- is_location(location(X, 5)); X > 1.
edge_side1_points_towards(location(5, Y), east) :- is_location(location(5, Y)); Y < 5.

% Break rotational symmetry by fixing the (1, 1) corner.
in_location(s1_loc(location(1, 1)), location(1, 1), I) :- solution_index(I).
{in_location(Piece, Loc, I) : is_corner_location(Loc)} = 1 :- is_corner_piece(Piece); solution_index(I); I != 1.
{in_location(Piece, Loc, I) : is_edge_location(Loc)} = 1 :- is_edge_piece(Piece); solution_index(I); I != 1.
{in_location(Piece, Loc, I) : is_interior_location(Loc)} = 1 :- is_interior_piece(Piece); solution_index(I); I != 1.
:- #count{Piece : in_location(Piece, Loc, I)} > 1; is_location(Loc); solution_index(I); I != 1.
side_points_towards(Piece, 1, north, 1) :- is_interior_piece(Piece).
{side_points_towards(Piece, 1, H, I) : heading(H)} = 1 :- is_interior_piece(Piece); solution_index(I); I != 1.

side_points_towards(Piece, 1, H, I) :- edge_side1_points_towards(Loc, H); in_location(Piece, Loc, I).
side_points_towards(Piece, S, H2, I) :- side_points_towards(Piece, S - 1, H1, I); piece_side(S); step_clockwise(H1, H2).

adjacent_by(Piece1, Piece2, H, I) :-
    in_location(Piece1, Loc1, I);
    in_location(Piece2, Loc2, I);
    adjacent_on(Loc1, Loc2, H).

joined(side_of(Piece1, S1), side_of(Piece2, S2), I) :-
    adjacent_by(Piece1, Piece2, H1, I);
    side_points_towards(Piece1, S1, H1, I);
    side_points_towards(Piece2, S2, H2, I);
    opposite_heading(H1, H2).

fits_together(side_of(Piece1, S1), side_of(Piece2, S2)) :-
    has_edge(Piece1, D1, S1);
    has_edge(Piece2, D2, S2);
    complementary(D1, D2).

:- joined(PE1, PE2, I); not fits_together(PE1, PE2); I != 1.

#show in_location/3.
#show side_points_towards/4.

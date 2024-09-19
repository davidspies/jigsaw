% Use with search to ensure no two pieces are the same.

is_orientation(0..3).
same_orientation(1, 1; 2, 2; 3, 3; 4, 4; 5, 1; 6, 2; 7, 3).
is_oriented_piece(oriented(Piece, N)) :- is_interior_piece(Piece); is_orientation(N).
has_oriented_edge(oriented(Piece, N), D, S2) :-
    is_oriented_piece(oriented(Piece, N));
    has_edge(Piece, D, S1);
    same_orientation(S1 + N, S2).
same_edge(OPiece1, OPiece2, S) :- has_oriented_edge(OPiece1, D, S); has_oriented_edge(OPiece2, D, S); OPiece1 < OPiece2.
:- #count{S : same_edge(OPiece1, OPiece2, S)} >= 4; is_oriented_piece(OPiece1); is_oriented_piece(OPiece2).

same_edge(Piece1, Piece2, S) :- has_edge(Piece1, D, S), has_edge(Piece2, D, S); Piece1 < Piece2.
:- #count{S : same_edge(Piece1, Piece2, S)} >= 3; is_edge_piece(Piece1); is_edge_piece(Piece2).
:- #count{S : same_edge(Piece1, Piece2, S)} >= 2; is_corner_piece(Piece1); is_corner_piece(Piece2).

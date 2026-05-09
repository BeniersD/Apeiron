def isAtom (a : Nat) : Prop :=
  a ≠ 0 ∧ ∀ b : Nat, 0 < b → b < a → False

theorem atomicity_one : isAtom 1 := by
  constructor
  · decide
  · intro b hpos hlt
    have hb0 : b = 0 := Nat.eq_zero_of_not_pos hlt
    rw [hb0] at hpos
    exact Nat.lt_irrefl 0 hpos
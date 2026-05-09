def isAtomBool (a : Nat) : Bool :=
  a != 0 && List.all (List.range a) (fun b => !(1 < b && b < a && a % b == 0))

theorem atomicity_test : isAtomBool 2 = true := by
  native_decide

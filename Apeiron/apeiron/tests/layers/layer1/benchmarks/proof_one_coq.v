From Stdlib Require Import Arith.Arith.
From Stdlib Require Import Bool.
From Stdlib Require Import List.
Import ListNotations.

Fixpoint check_divisors (n d : nat) : bool :=
  match d with
  | 0 => true
  | S d' =>
      if (1 <? d) && (d <? n) && (n mod d =? 0) then false
      else check_divisors n d'
  end.

Definition is_atomic_bool_bool (n : nat) : bool :=
  (negb (n =? 0)) && check_divisors n (n-1).

Theorem atomicity_test : is_atomic_bool_bool 1 = true.
Proof.
  vm_compute. reflexivity.
Qed.

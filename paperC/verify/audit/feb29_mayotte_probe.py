"""Verifier probe: 29 February birth dates raise DateError; Mayotte two-child amount.
Run from the repository root: python3.12 paperC/verify/audit/feb29_mayotte_probe.py"""
import os, sys, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.argv = ["x", ROOT, tempfile.mkdtemp()]
sys.path.insert(0, os.path.join(ROOT, "paperC", "verify"))
import spotcheck as s
from catala_runtime import *
from generated import Allocations_familiales as AF
def ee(i,b):
    return AF.EnfantEntree(d_identifiant=Integer(i),d_remuneration_mensuelle=Money("0"),d_date_de_naissance=s.date(b),d_prise_en_charge=s.prise("EffectiveEtPermanente"),d_a_deja_ouvert_droit_aux_allocations_familiales=Bool(True),d_beneficie_titre_personnel_aide_personnelle_logement=Bool(False))
for b in ["2016-02-29","2008-02-29","2004-02-29"]:
    print(b, s.call_interface([ee(0,"2013-01-01"),ee(1,b)],"30000.00","Métropole","vrai","faux","faux")[:2])
print("mayotte 2 kids", s.call_interface([ee(0,"2013-01-01"),ee(1,"2013-01-02")],"30000.00","Mayotte","vrai","faux","faux")[:2])

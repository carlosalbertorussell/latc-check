import sys,os
B=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","catala_family_benefits")
sys.path.insert(0,os.path.join(B,"runtime","catala")); sys.path.insert(0,B)
from catala_runtime import Array, Bool, Date, Integer, Money, Unit, catala_set_lang, Lang
from generated import Allocations_familiales as AF
from generated import France
catala_set_lang(Lang.Fr)
def col(n): return France.Collectivite(getattr(France.Collectivite.Code,n),Unit())
def pec(n): return AF.PriseEnCharge(getattr(AF.PriseEnCharge.Code,n),Unit())
def d(s): y,m,dd=map(int,s.split('-')); return Date(y,m,dd)
def ee(i,b,rem="0.00",p="EffectiveEtPermanente",deja=True,apl=False):
    return AF.EnfantEntree(d_identifiant=Integer(i),d_remuneration_mensuelle=Money(rem),d_date_de_naissance=d(b),d_prise_en_charge=pec(p),d_a_deja_ouvert_droit_aux_allocations_familiales=Bool(deja),d_beneficie_titre_personnel_aide_personnelle_logement=Bool(apl))
def amt(births,res="Metropole",ress="30000.00",dc="2020-05-01",ep=True,t1=False,av=False,**kw):
    try:
        o=AF.interface_allocations_familiales(AF.InterfaceAllocationsFamilialesIn(i_date_courante_in=d(dc),i_enfants_in=Array([ee(i,b,**kw) for i,b in enumerate(births)]),i_ressources_menage_in=Money(ress),i_residence_in=col(res),i_personne_charge_effective_permanente_est_parent_in=Bool(ep),i_personne_charge_effective_permanente_remplit_titre_I_in=Bool(t1),i_avait_enfant_a_charge_avant_1er_janvier_2012_in=Bool(av)))
        return o.i_montant_verse
    except Exception as e: return "ERR %s: %s"%(type(e).__name__,str(e)[:150])
print("2007,2009:",amt(["2007-01-01","2009-01-01"]))
print("2007,2009,2000-08-01 (a19_20):",amt(["2007-01-01","2009-01-01","2000-08-01"]))
print("2007,2009,2003-01-01 (a16_19):",amt(["2007-01-01","2009-01-01","2003-01-01"]))
print("Mayotte 1 child 2013:",amt(["2013-01-01"],res="Mayotte"))
print("Mayotte 2 children 2013,2015:",amt(["2013-01-01","2015-01-01"],res="Mayotte"))
print("Mayotte 3 children:",amt(["2013-01-01","2015-01-01","2016-01-01"],res="Mayotte"))
print("Mayotte 1 child avant2012:",amt(["2013-01-01"],res="Mayotte",av=True))
print("Feb29 2008 birth:",amt(["2008-02-29","2009-01-01"]))
print("Feb29 2004 birth:",amt(["2004-02-29","2009-01-01"]))
print("Guadeloupe only child 2005 (15y):",amt(["2005-01-01"],res="Guadeloupe"))
print("Guadeloupe 1999+2005:",amt(["1999-01-01","2005-01-01"],res="Guadeloupe"))
print("est_parent F titre F:",amt(["2007-01-01","2009-01-01"],ep=False,t1=False))
def osco(n): return AF.SituationObligationScolaire(getattr(AF.SituationObligationScolaire.Code,n),Unit())
def pf(res,rem,b="2003-01-01",ob="Apres",apl=False):
    o=AF.prestations_familiales(AF.PrestationsFamilialesIn(date_courante_in=d("2020-05-01"),residence_in=col(res)))
    e=AF.Enfant(identifiant=Integer(1),obligation_scolaire=osco(ob),remuneration_mensuelle=Money(rem),date_de_naissance=d(b),prise_en_charge=pec("EffectiveEtPermanente"),a_deja_ouvert_droit_aux_allocations_familiales=Bool(True),beneficie_titre_personnel_aide_personnelle_logement=Bool(apl))
    return o.droit_ouvert(e)
for r,v in [("Metropole","943.02"),("Metropole","943.03"),("Mayotte","711.49"),("Mayotte","711.50"),("Guyane","943.02"),("Guyane","943.03"),("SaintPierreEtMiquelon","943.03")]:
    print(r,v,pf(r,v))
print("b=2000-05-01 Apres:",pf("Metropole","0.00",b="2000-05-01"),"b=2000-05-02:",pf("Metropole","0.00",b="2000-05-02"))
print("Avant with 1999 birth:",pf("Metropole","5000.00",b="1999-01-01",ob="Avant"))
print("1999,2005,2007:",amt(["1999-01-01","2005-01-01","2007-01-01"]))
print("2005,2007:",amt(["2005-01-01","2007-01-01"]))
def amt2(kids,res="Metropole",ress="30000.00"):
    o=AF.interface_allocations_familiales(AF.InterfaceAllocationsFamilialesIn(i_date_courante_in=d("2020-05-01"),i_enfants_in=Array([ee(i,*k) for i,k in enumerate(kids)]),i_ressources_menage_in=Money(ress),i_residence_in=col(res),i_personne_charge_effective_permanente_est_parent_in=Bool(True),i_personne_charge_effective_permanente_remplit_titre_I_in=Bool(False),i_avait_enfant_a_charge_avant_1er_janvier_2012_in=Bool(False)))
    return o.i_montant_verse
E="EffectiveEtPermanente"
print("2003,2005(apl),2009:",amt2([("2003-01-01","0.00",E,True,False),("2005-01-01","0.00",E,True,True),("2009-01-01","0.00",E,True,False)]))
print("2003,2005,2009 no apl:",amt2([("2003-01-01","0.00",E,True,False),("2005-01-01","0.00",E,True,False),("2009-01-01","0.00",E,True,False)]))
print("2003,2009 only:",amt2([("2003-01-01","0.00",E,True,False),("2009-01-01","0.00",E,True,False)]))
print("2007,2009,1995(apl):",amt2([("2007-01-01","0.00",E,True,False),("2009-01-01","0.00",E,True,False),("1995-01-01","0.00",E,True,True)]))

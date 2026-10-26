"""Automatisk retting av FY1-07-klima-og-straalingsbalanse.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1_utstraling', 'utstraling(288) skal gi ca. 390 W/m²', 'naer(utstraling(288), 5.67e-8 * 288**4) and naer(utstraling(100), 5.67)'),
    ('1_wien', 'wien(5778) skal gi ca. 5.02e-7 m (502 nm)', 'naer(wien(5778), 2.898e-3 / 5778) and naer(wien(288), 2.898e-3 / 288)'),
    ('2', 'likevektstemperatur(1361, 0.30) skal gi ca. 254.6 K', 'naer(likevektstemperatur(1361, 0.30), (1361 * 0.7 / 4 / 5.67e-8)**0.25) and naer(likevektstemperatur(1361, 0.30), 254.6, rel=1e-3)'),
    ('3_funksjon', 'overflatetemperatur(1361, 0.30, 0.78) skal gi ca. 288 K', 'naer(overflatetemperatur(1361, 0.30, 0.78), (1361 * 0.7 / 4 / 5.67e-8)**0.25 * (2 / 1.22)**0.25)'),
    ('3_ingen', 'overflatetemperatur med epsilon = 0 skal gi likevektstemperaturen', 'naer(overflatetemperatur(1361, 0.30, 0), (1361 * 0.7 / 4 / 5.67e-8)**0.25)'),
    ('3_epsilon', 'epsilon_15 skal gi 15 °C (288.15 K) i modellen', 'naer(2 - 2 * ((1361 * 0.7 / 4 / 5.67e-8)**0.25 / 288.15)**4, epsilon_15, rel=2e-3)'),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse

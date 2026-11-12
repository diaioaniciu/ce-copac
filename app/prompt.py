"""Prompt sent to Claude together with the photos."""

SCHEMA = """{
  "identificabil": true/false,
  "mesaj": "doar dacă nu e identificabil: de ce și ce poză ar ajuta",
  "ce_se_vede": "frunză | ace/con | scoarță | fruct | floare | copac întreg | altceva",
  "nume_popular": "numele în română (ex: Stejar pedunculat)",
  "nume_latin": "Quercus robur",
  "alte_nume": "alte denumiri populare în română, dacă există",
  "familie": "Fagaceae",
  "categorie": "foios | conifer | pom fructifer | arbust",
  "incredere": "ridicată | medie | scăzută",
  "de_ce": "1–2 propoziții: ce trăsături vizibile în poză au dus la identificare",
  "alternative": [{"nume_popular": "", "nume_latin": "", "cum_le_deosebesti": ""}],
  "rezumat": "2–3 propoziții despre specie",
  "aspect": {
    "frunze_sau_ace": "", "scoarta": "", "flori": "", "fructe_seminte": "", "talie_forma": ""
  },
  "habitat": "climă, sol, altitudine, unde crește în natură",
  "in_romania": "cât de răspândit e în România, unde îl găsești (păduri, parcuri, livezi)",
  "utilizari": {
    "fruct": "", "frunze": "", "scoarta": "", "lemn": "",
    "altele": "ornamental, melifer, medicină tradițională etc."
  },
  "toxicitate": "ce părți sunt toxice pentru oameni/animale, sau \\"\\" dacă nu e cazul",
  "curiozitati": ["", ""],
  "sfat_poza": "ce poză suplimentară ar confirma identificarea"
}"""


def build_prompt(photo_count: int, kind: str = "auto", note: str = "") -> str:
    photos = (
        "pozele atașate (toate sunt din același exemplar)"
        if photo_count > 1
        else "poza atașată"
    )
    lines = [
        "Ești un dendrolog și botanist expert. Identifică arborele, pomul, "
        f"arbustul sau coniferul din {photos}.",
    ]
    if kind != "auto":
        lines.append(f"Utilizatorul spune că a fotografiat: {kind}.")
    if note:
        lines.append(f"Context de la utilizator: {note}")
    lines += [
        "Utilizatorul e în România, deci ia în calcul mai ales speciile din Europa "
        "Centrală și de Est (spontane, cultivate, ornamentale), fără să le excluzi "
        "pe celelalte.",
        "",
        "Reguli:",
        "- Fii onest cu încrederea. Scoarța singură e adesea ambiguă: dacă nu ești "
        'sigur, pune încredere „medie" sau „scăzută" și dă 1–3 alternative cu '
        "diferențele cheie.",
        "- Dacă poza nu arată o plantă lemnoasă sau nu se poate identifica, pune "
        '"identificabil": false și explică în "mesaj".',
        "- Scrie totul în limba română, clar, pentru un nespecialist. Câmpurile "
        'pentru care nu există informație relevantă rămân "".',
        "- La utilizări, menționează explicit dacă fructul NU e comestibil sau e toxic.",
        "",
        "Răspunde DOAR cu un obiect JSON valid, fără text în afara lui, cu structura:",
        SCHEMA,
    ]
    return "\n".join(lines)

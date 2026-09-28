# Sublinieri

Citate de carte pe care le-am postat pe Facebook de-a lungul anilor, și cele noi de acum încolo.

Pagina: https://ducu.github.io/sublinieri/

## Cum e făcut

- `entries/` — câte un fișier `.md` pentru fiecare citat. Asta e singura parte care se schimbă de obicei.
- `photos/` — pozele cu pagini de carte, numite după intrarea căreia îi aparțin.
- `template.html` — designul paginii (stilurile, lightbox-ul, navigarea pe ani). Aici `build.py` pune intrările și navigarea.
- `build.py` — generează `_site/index.html` din intrări. Numărătoarea pe ani, ordinea și anii din meniu se calculează singure.
- `.github/workflows/pages.yml` — la fiecare push pe `main` rulează `build.py` și publică pe GitHub Pages.

## Cum adaugi un citat

Creezi un fișier nou în `entries/`, de exemplu `entries/2026-10-03-umberto-eco.md`:

```
---
date: 2026-10-03
source: Umberto Eco — Numărul zero, p. 42
intro: Un rând opțional, spus de mine înainte de citat.
note: Un rând opțional, spus de mine după citat.
photos: 2026-10-03-umberto-eco-1.jpg
---

Primul paragraf al citatului.

Al doilea paragraf.
```

- `date` și `source` sunt obligatorii; restul sunt opționale.
- Paragrafele se despart printr-un rând gol. Un singur Enter în interiorul unui paragraf devine rând nou.
- Citatele lungi se pliază singure după ~100 de cuvinte („arată tot”). Ca să alegi tu unde se pliază, pune pe un rând separat `<!-- more -->`.
- `kind: note` pentru o notă proprie în loc de citat; `style: dialogue` pentru dialoguri (fiecare replică pe paragraful ei).
- Două intrări din aceeași zi apar în ordinea alfabetică a numelor de fișier.
- Pozele merg în `photos/` ca `.jpg`, **fără metadate EXIF** (repo-ul e public, iar pozele de pe telefon au GPS). `build.py` refuză pozele care încă le au.

Din telefon: pe GitHub, *Add file → Create new file* în `entries/`, lipești textul, *Commit*. Pagina se actualizează în ~1 minut.

## Local

```
python3 build.py
open _site/index.html
```

# Le GOAT de l'EDT 🎓

Bot qui envoie l'emploi du temps de la semaine sur Discord — un salon par
groupe (GrA / GrB / GrC / CM Communs) — sous forme d'image.

## Structure

```
edt_bot.py                      → orchestration (fetch, envoi, cache, garde-fous)
edt_parsing.py                  → parsing iCal Hyperplanning (fuseau Paris via pytz)
style_grid.py                   → génération de l'image (grille hebdomadaire)
fonts/                          → police Poppins (même DA que les autres bots)
.github/workflows/edt.yml
requirements.txt
```

Les anciens `edt_bot_final.py`, `edt_bot_ultimate.py` et les workflows
`edt.yml`/`edt_final.yml` (versions L2) ont été remplacés par cet ensemble
unique, mis à jour pour le L3.

## Sources

- **CM Communs** : flux combiné `Edt_ST_L3___INFORMATIQUE`, filtré aux
  événements sans préfixe `GrX` (CM partagés + les 2 options, qui n'ont pas
  de préfixe de groupe).
- **GrA / GrB / GrC** : flux dédiés à chaque groupe, fusionnés avec les 2
  flux d'option (Architecture avancée, Prog. C++) — les options concernent
  des étudiants de tous les groupes, donc diffusées dans les 3 salons de
  groupe en plus de CM Communs.
- Les créneaux simultanés (ex : les 2 options en parallèle) sont placés
  côte à côte sur l'image plutôt que superposés.

## Comportement

- Un seul envoi par semaine : **dimanche 18h (heure de Paris)**, pour la
  semaine **suivante**. Fiable toute l'année (deux crons été/hiver + garde-fou
  horaire dans le script, voir `TARGET_HOUR`/`TOLERANCE_MIN`).
- Si **aucun** salon n'a de cours cette semaine-là (vacances), un seul
  message "pas de cours" est envoyé sur CM Communs, et la semaine est
  mémorisée (`edt_cache.json`) pour ne pas re-notifier les jours suivants.

## Tester une semaine précise (`TEST_MONDAY`)

Le mode normal envoie toujours la semaine *suivante*. Si celle-ci ET la
semaine encore après sont vides (vacances), il n'y a rien à voir tant qu'on
n'a pas de vraie semaine de cours sous la main. `TEST_MONDAY` force le rendu
d'une semaine arbitraire (n'importe quelle date de cette semaine-là, la
fonction retombe automatiquement sur le lundi) :

```bash
TEST_MONDAY=2026-09-07 FORCE_RUN=1 WEBHOOK_CM=... python edt_bot.py
```

Un test avec `TEST_MONDAY` :
- ignore le garde-fou jour/horaire (comme `FORCE_RUN`) ;
- ignore le cache de "semaine vide" (n'écrit jamais dans `edt_cache.json`),
  donc ne perturbe jamais le comportement normal des prochains runs.

Via GitHub Actions : `Actions → EDT Bot → Run workflow`, champ
**test_monday** (laisser vide pour le comportement normal).

## Configuration (secrets GitHub)

```
WEBHOOK_CM, WEBHOOK_GRA, WEBHOOK_GRB, WEBHOOK_GRC   → un webhook par salon
ROLE_CM, ROLE_GRA, ROLE_GRB, ROLE_GRC               → (optionnel) rôle à ping
```

# creative-digital-media

Grafiche e calendario dei post di [@creative__digital](https://www.instagram.com/creative__digital/).

- `posts/`: le grafiche 1080 x 1350, nome `AAAA-MM-GG_NN_tema_slide.png`.
- `calendario.json`: orario (fuso Europe/Rome), immagini, caption e approvazione di ogni post.
- `pubblicati.json`: registro dei post già pubblicati, aggiornato in automatico.
- `.github/workflows/pubblica.yml`: ogni 10 minuti pubblica i post approvati arrivati all'orario (finestra di 2 ore, poi il post viene saltato).
- `.github/workflows/rinnova-token.yml`: il 1 e il 15 di ogni mese rinnova il token di Instagram.

## Secret richiesti (Settings → Secrets and variables → Actions)

- `INSTAGRAM_ACCESS_TOKEN`: token dell'API Instagram di creative__digital.
- `GH_PAT`: token GitHub con permesso di scrivere i secret di questo repository, serve solo al rinnovo automatico.

## Pubblicare a mano un post

Actions → Pubblica su Instagram → Run workflow, con l'id del post (per esempio `cd-001`). Con "Prova" spuntato mostra cosa farebbe senza pubblicare.

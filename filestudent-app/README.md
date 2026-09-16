# FileStudent

Boite a outils desktop pour etudiants, inspiree d'iLovePDF et iLoveIMG.
Convertir, fusionner, compresser, ameliorer et proteger ses fichiers PDF et
images, sans envoyer aucun fichier sur un serveur externe, sans compte et
sans abonnement.

Projet realise dans le cadre d'un seminaire ESGI. Equipe Logiciel : Nathan,
Julien.

## Telecharger

**[Derniere version pour Windows](https://github.com/evomerse/FileStudent/releases/latest)**

L'executable est regenere automatiquement a chaque mise a jour du code
(voir `.github/workflows/build-windows.yml`) : le lien ci-dessus pointe
toujours vers la version la plus recente, environ 190 Mo. Windows peut
afficher un avertissement SmartScreen ("Editeur inconnu") au premier
lancement : c'est normal pour un executable non signe, cliquez sur
"Informations complementaires" puis "Executer quand meme".

Linux/macOS : voir [Construire l'executable](#construire-lexecutable)
plus bas.

## Modules

Treize onglets de traitement, chacun avec sa zone de depot de fichiers et
ses options (le quatorzieme, "Menu contextuel Windows", est decrit plus
bas) :

- **Conversion** : image <-> PDF, image <-> image (PNG, JPG, WEBP, BMP,
  TIFF, GIF), PDF -> DOCX et PDF -> Markdown (toujours disponibles), DOCX
  -> PDF (fidele avec LibreOffice, sinon rendu texte simplifie), PPTX/XLSX
  -> PDF (necessitent LibreOffice).
- **Fusion** : assemble plusieurs PDF et/ou images en un seul PDF, dans
  l'ordre de depot.
- **Diviser un PDF** : extraire des pages, en supprimer, reorganiser
  toutes les pages dans un nouvel ordre, ou separer chaque page en fichier
  independant.
- **Reduction de taille** : recompresse les images embarquees d'un PDF ou
  reencode une image, qualite reglable.
- **Rotation, filigrane, numerotation** : pivote les pages d'un PDF, les
  rogne (marge en %), ajoute un filigrane texte et/ou numerote les pages.
- **Reparer PDF** : recupere un PDF legerement corrompu ou mal forme
  (xref/trailer casse) que certains lecteurs refusent d'ouvrir.
- **Comparer PDF** : affiche les vraies differences de texte (lignes
  ajoutees/supprimees) entre deux versions d'un document.
- **Censurer PDF** : recherche un texte et le supprime reellement du
  document (pas seulement un cache visuel par-dessus).
- **Securite PDF** : protege un PDF par mot de passe, ou le deverrouille.
- **Archive .tar.gz** : cree ou extrait une archive, niveau de compression
  reglable.
- **Amelioration d'image** : filtres (nettete, contraste, luminosite,
  niveaux de gris, reduction de bruit), recadrage, redimensionnement
  (prereglages ou dimensions exactes), rotation, filigrane, upscaling
  algorithmique (Lanczos, sans modele d'IA).
- **Detection de texte IA** : heuristiques statistiques indicatives (pas un
  modele entraine), score par paragraphe avec avertissement explicite.
  Formats geres : PDF, DOCX, TXT.
- **Comparaison de documents** : similarite locale entre plusieurs
  documents deposes (empreintes de groupes de mots, detection de plagiat),
  a distinguer de "Comparer PDF" qui affiche les differences de contenu.

Chaque traitement termine propose "Ouvrir le dossier" et "Ouvrir le
fichier" pour retrouver le resultat immediatement.

## Hors perimetre (assume)

Deux categories de fonctions d'iLovePDF/iLoveIMG sont volontairement
laissees de cote :

- **Contradictoires avec le principe "vos documents ne quittent jamais
  votre ordinateur"** : resume par IA et traduction demanderaient soit un
  modele local de plusieurs Go, soit d'envoyer le contenu a un service en
  ligne.
- **Necessitent un editeur graphique dedie, pas juste un module de plus** :
  edition de PDF (texte/formes/annotations), formulaires PDF, signature
  electronique, editeur de photos avec stickers, createur de flux de
  travail, numerisation, HTML vers PDF/image, PDF vers PDF/A, OCR
  (dependance externe, Tesseract), suppression d'arriere-plan et flou de
  visage (modeles d'IA a telecharger), generateur de memes, formats
  d'image marginaux pour un usage etudiant (PSD, RAW, SVG, HEIC).

L'upscaling par IA reelle (Real-ESRGAN) est en backlog, remplace ici par
un upscaling algorithmique.

## Installation

Python 3.10 ou plus recent est requis.

```bash
python -m venv .venv
source .venv/bin/activate      # Windows : .venv\Scripts\activate
pip install -e ".[dev]"
```

## Lancer l'application

```bash
python -m filestudent
```

## Auto-diagnostic

Verifie que les 17 traitements fonctionnent reellement sur la machine en
cours (utile pour confirmer qu'un executable construit avec PyInstaller
tourne correctement), sans ouvrir l'interface :

```bash
python -m filestudent --selftest
```

## Lancer les tests et le lint

```bash
ruff check .
pytest
```

## Construire l'executable

Voir `build.bat` (Windows) ou `build.sh` (Linux/macOS). Le resultat est
volumineux (environ 190 Mo) : la conversion PDF -> Word embarque des
bibliotheques de traitement d'image (OpenCV, NumPy).

## Menu contextuel dans l'explorateur Windows (ticket APP-23)

Une fois `FileStudent.exe` construit, ouvrez-le et allez dans l'onglet
**Menu contextuel Windows** (le dernier), puis cliquez sur "Installer le
clic droit dans l'explorateur". Aucune commande a taper : l'application
ecrit elle-meme les cles necessaires. Le bouton "Desinstaller" du meme
onglet retire tout.

Cela ajoute des entrees prefixees "FileStudent - " au clic droit sur un
fichier, sur un dossier, et sur le bureau (fond d'un dossier), pour
traiter un fichier sans ouvrir la fenetre principale. Ce sont des entrees
directes, pas un sous-menu en cascade : ce mecanisme s'est avere peu
fiable en pratique (l'entree principale s'affichait mais restait vide au
survol sur certaines configurations Windows).

- Sur un fichier : Convertir en PDF, Convertir en Word, Convertir en
  image, Convertir en Markdown, Reduire la taille, Ameliorer l'image,
  Diviser en pages, Reparer le PDF, Censurer un texte (demande le texte),
  Ajouter un filigrane (demande le texte), Proteger par mot de passe
  (demande le mot de passe), Detecter texte IA, Ouvrir dans FileStudent.
- Sur un dossier : Compresser en .tar.gz, Ouvrir.
- Sur le fond d'un dossier ou du bureau : Ouvrir FileStudent.

"Comparer PDF" et "Diviser (reorganiser les pages)" ne sont pas proposes
au clic droit : la reorganisation et la comparaison ont besoin d'une
saisie plus riche (un ordre de pages, ou deux fichiers pris ensemble) que
ce que le clic droit peut transmettre simplement ; utilisez l'application
pour ces deux cas.

N'a pas besoin des droits administrateur : tout est ecrit dans
`HKEY_CURRENT_USER`, valable pour l'utilisateur Windows courant
uniquement. Chaque personne qui veut ce clic droit doit cliquer sur
"Installer" depuis son propre compte, avec sa propre copie de
`FileStudent.exe` a l'endroit ou elle compte la garder (l'installation
enregistre le chemin exact de l'executable a cet instant).

### Alternative en ligne de commande

Les scripts `install-context-menu.ps1` et `uninstall-context-menu.ps1` a
la racine du depot font exactement la meme chose que le bouton, utiles
pour un deploiement scripte sur plusieurs machines :

```powershell
powershell -ExecutionPolicy Bypass -File install-context-menu.ps1
```

Pour retirer le menu :

```powershell
powershell -ExecutionPolicy Bypass -File uninstall-context-menu.ps1
```

**A savoir sur Windows 11** : le nouveau menu contextuel n'affiche par
defaut que quelques entrees. Les elements ajoutes par des applications
tierces, dont FileStudent, apparaissent sous "Afficher plus d'options" (ou
Maj + clic droit), sauf si vous avez remis le menu contextuel classique.

Ces deux scripts PowerShell n'ont pas pu etre executes pendant le
developpement (environnement Linux, sans Windows disponible) : leur
contenu a ete relu avec attention, mais testez-les et signalez tout
probleme.

## Dependance optionnelle : LibreOffice

PowerPoint et Excel vers PDF, ainsi qu'une conversion Word vers PDF
fidele a la mise en page, necessitent LibreOffice installe sur la
machine (detecte automatiquement sur le PATH ou aux emplacements Windows
courants). En son absence :

- Word vers PDF fonctionne quand meme, avec un rendu texte simplifie
  (sans images ni tableaux).
- PowerPoint et Excel vers PDF affichent un message clair invitant a
  installer LibreOffice, sans faire planter l'application.

Telechargement : https://www.libreoffice.org/download/

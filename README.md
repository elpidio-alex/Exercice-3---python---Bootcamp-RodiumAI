# Exercice 3 (Python) : Utiliser le SDK RodiumAi

Script Python interactif, écrit avec le SDK officiel `rodiumai`, qui enchaîne trois actions avec l'API RodiumAi : chat, génération d'image et génération de vidéo.
À la fin de chaque étape, l'utilisateur choisit de revenir en arrière, de rester sur l'étape pour la refaire ou de passer à la suivante.

Projet réalisé dans le cadre du bootcamp RodiumAi, Module 03 : *Utiliser les API IA avec RodiumAi*. Il refait le script de l'exercice 2 (requêtes HTTP avec `requests`), cette fois avec le SDK.

---

## Sommaire

1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Lancement](#lancement)
5. [Exemple de déroulement](#exemple-de-déroulement)
6. [Fonctionnement](#fonctionnement)
7. [Gestion des erreurs](#gestion-des-erreurs)
8. [Notes sur le SDK](#notes-sur-le-sdk)
9. [Sécurité](#sécurité)
10. [Structure du dépôt](#structure-du-dépôt)

---

## Prérequis

- **Python 3.14.5** (version utilisée pour développer et tester le script)
- Un compte RodiumAi avec des crédits RODI
- Une clé API RodiumAi, au format `rd_sk_...` (Dashboard → Clés API)

## Installation

Cloner le dépôt, puis installer les dépendances dans un environnement virtuel (commandes pour Windows PowerShell) :

```powershell
git clone https://github.com/elpidio-alex/Exercice-3---python---Bootcamp-RodiumAI.git
cd exercice-3-python
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si PowerShell bloque l'activation de l'environnement virtuel, exécuter d'abord `Set-ExecutionPolicy -Scope Process Bypass` : ce réglage ne s'applique qu'à la fenêtre en cours.

Dépendances (`requirements.txt`) :

| Bibliothèque | Rôle |
|---|---|
| `rodiumai` (version 0.3 ou plus, testé avec 0.3.1) | SDK officiel de l'API RodiumAi |
| `python-dotenv` | Chargement de la clé API depuis le fichier `.env` |
| `httpx` | Téléchargement du média lorsque l'API renvoie une URL (déjà requis par le SDK) |

## Configuration

1. Copier le fichier d'exemple :

```powershell
   Copy-Item .env.example .env
```

2. Ouvrir `.env` et remplacer la valeur par sa propre clé API :

```
   RODIUMAI_API_KEY=rd_sk_votre_cle
```

Le SDK lit la clé dans la variable d'environnement `RODIUMAI_API_KEY`. Le script charge d'abord le fichier `.env` avec `python-dotenv`. Si la clé est introuvable, il s'arrête avec un message explicite.

## Lancement

```powershell
py .\main.py
```

Le script crée dans le dossier courant les fichiers `image.png` (étape 2) et `video.mp4` (étape 3).

## Exemple de déroulement

```
=== Étape 1 : Chat ===
Votre question : Dis-moi à quoi sert une EIN ? Réponds en 3 phrases
[réponse du modèle]
Coût : ...
Rester sur cette étape (r) ou passer à la suivante (s) ? s

=== Étape 2 : Image ===
Décrivez l'image : Flyer pour un concert à Lomé, style affiche
Fichier enregistré : ...\image.png
Revenir en arrière (b), rester (r) ou passer à la suivante (s) ? s

=== Étape 3 : Vidéo ===
Décrivez la vidéo : Vagues au coucher du soleil, cinématique
Fichier enregistré : ...\video.mp4
Revenir en arrière (b), rester (r) ou quitter (q) ? q
```

## Fonctionnement

| Étape | Ce que fait le script | Appel du SDK | Modèle |
|---|---|---|---|
| 1. Chat | Demande une question, l'envoie au modèle, affiche la réponse et le coût | `client.chat(...)` | `anthropic/claude-sonnet-4-6` |
| 2. Image | Demande une description, génère l'image, décode `b64_json` et enregistre le PNG | `client.images(...)` | `google/gemini-3.1-flash-image` |
| 3. Vidéo | Demande une description, génère une courte vidéo et enregistre le MP4 | `client.videos(...)` | `google/veo-3.1-lite` |

Les modèles sont définis en haut de `main.py` (`MODELE_CHAT`, `MODELE_IMAGE`, `MODELE_VIDEO`), au format `fournisseur/modèle`.

**Navigation entre les étapes :**

| Étape | Choix proposés |
|---|---|
| 1 | rester (`r`) ou passer à la suivante (`s`) |
| 2 | revenir en arrière (`b`), rester (`r`) ou passer à la suivante (`s`) |
| 3 | revenir en arrière (`b`), rester (`r`) ou quitter (`q`) |

L'étape est répétée tant que l'utilisateur choisit de rester. Une saisie invalide est redemandée.

**Points d'attention :**

- La vidéo est **facturée à la seconde générée** : le script demande une durée courte (4 s) et applique un timeout de **150 secondes** (2 min 30).
- Le coût est affiché via `cost_rodi` lorsque l'API le renvoie. À défaut, le script affiche les tokens consommés ou renvoie vers les Journaux d'usage du Dashboard RodiumAi.

## Gestion des erreurs

Le SDK lève des exceptions typées, toutes dérivées de `RodiumAIError`. Le script les intercepte, affiche le code HTTP et l'`error_code`, puis redonne la main à l'utilisateur :

```
Erreur HTTP 403 (error_code : model_not_allowed)
Détail : ...
```

Principaux codes de l'API : `401 invalid_api_key`, `402 insufficient_balance`, `403 permission_denied`, `404 model_not_found`, `429 rate_limit_exceeded`, `500/503` (incident serveur), `timeout`.

## Notes sur le SDK

- Le SDK est **asynchrone** : le script utilise `asyncio`.
- Avec `rodiumai` 0.3.1, le modèle est passé **directement dans l'appel** (`client.chat(..., model=...)`). Le constructeur fluent `client.model(...).chat(...)` n'applique pas le modèle choisi pour le chat et utilise le modèle par défaut (`openai/gpt-4o`), ce qui provoque une erreur 403 si le compte n'y a pas accès.
- Le SDK ne lit pas le fichier `.env` : c'est pourquoi `python-dotenv` charge le fichier avant la création du client.

## Sécurité

- La clé API n'est jamais écrite dans le code.
- Le vrai fichier `.env` est listé dans `.gitignore` et n'est donc jamais publié.
- Le fichier `.env.example` contient uniquement `RODIUMAI_API_KEY=rd_sk_votre_cle`.
- En cas de fuite de la clé : la révoquer dans le Dashboard et en créer une nouvelle.

## Structure du dépôt

```
exercice-3-python/
|-- README.md
|-- .env.example
|-- .gitignore
|-- requirements.txt
`-- main.py
```
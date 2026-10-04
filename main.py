"""
Date : 01/10/2026
Auteurs : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com
But : Script en python pour l'exercice 3 du Bootcamp RodiumAI.
    - Étape 1 : Chat avec un modèle de langage
    - Étape 2 : Génération d'image
    - Étape 3 : Génération de vidéo
"""

import asyncio
import base64
import os
import sys

import httpx
from dotenv import load_dotenv
from rodiumai import RodiumAI, RodiumAIError

# --- Configuration -----------------------------------------------------------
# Le SDK lit RODIUMAI_API_KEY dans l'environnement : on charge le .env avant.
load_dotenv()

MODELE_CHAT = "anthropic/claude-sonnet-4-6"
MODELE_IMAGE = "google/gemini-3.1-flash-image"
MODELE_VIDEO = "google/veo-3.1-lite"
DUREE_VIDEO_S = 4        # durée courte : la vidéo est facturée à la seconde
TIMEOUT_VIDEO = 150      # 2 min 30, comme à l'exercice 2

if not os.getenv("RODIUMAI_API_KEY"):
    sys.exit("Erreur : RODIUMAI_API_KEY introuvable. "
             "Copiez .env.example en .env et renseignez votre clé.")
if "REMPLACER" in MODELE_IMAGE:
    sys.exit("Erreur : renseignez MODELE_IMAGE dans main.py.")


# --- Fonctions utilitaires ---------------------------------------------------
def afficher_erreur(e):
    """Affiche un message clair avec le code HTTP et l'error_code."""
    statut = e.code if e.code else "n/a"
    print(f"Erreur HTTP {statut} (error_code : {e.error_code})")
    if e.message:
        print(f"Détail : {e.message}")


def afficher_cout(rep):
    """Affiche cost_rodi s'il existe, sinon les tokens ou un renvoi au dashboard."""
    cout = getattr(rep, "cost_rodi", None)
    if cout is not None:
        print(f"Coût : {cout} RODI")
        return
    usage = getattr(rep, "usage", None)
    if usage is not None:
        print("Coût : cost_rodi absent de la réponse "
              f"(tokens : {usage.prompt_tokens} en entrée, "
              f"{usage.completion_tokens} en sortie)")
    else:
        print("Coût : non fourni par la réponse (voir les Journaux d'usage du Dashboard)")


async def enregistrer_media(element, fichier):
    """Enregistre un média reçu en base64 (b64_json) ou via une URL https."""
    try:
        if element.b64_json:
            contenu = base64.b64decode(element.b64_json)
        elif element.url and element.url.startswith("http"):
            async with httpx.AsyncClient(timeout=120) as http:
                reponse = await http.get(element.url)
                reponse.raise_for_status()
                contenu = reponse.content
        else:
            print("Erreur : la réponse ne contient ni b64_json ni URL téléchargeable.")
            return False
    except (httpx.HTTPError, ValueError) as e:
        print(f"Erreur lors de l'enregistrement du fichier : {e}")
        return False

    with open(fichier, "wb") as f:
        f.write(contenu)
    print(f"Fichier enregistré : {os.path.abspath(fichier)}")
    return True


# --- Les trois étapes --------------------------------------------------------
async def etape_chat(client):
    print("\n=== Étape 1 : Chat ===")
    question = input("Votre question : ").strip()
    if not question:
        print("Question vide.")
        return
    try:
        rep = await client.chat(question, model=MODELE_CHAT, max_tokens=1000, timeout=60)
    except RodiumAIError as e:
        afficher_erreur(e)
        return
    print(rep.choices[0].message.content)
    afficher_cout(rep)


async def etape_image(client):
    print("\n=== Étape 2 : Image ===")
    description = input("Décrivez l'image : ").strip()
    if not description:
        print("Description vide.")
        return
    try:
        rep = await client.images(model=MODELE_IMAGE, prompt=description, timeout=120)
    except RodiumAIError as e:
        afficher_erreur(e)
        return
    if not rep.data:
        print("Erreur : la réponse ne contient aucune image.")
        return
    await enregistrer_media(rep.data[0], "image.png")
    afficher_cout(rep)


async def etape_video(client):
    print("\n=== Étape 3 : Vidéo ===")
    print(f"Attention : facturée à la seconde générée ({DUREE_VIDEO_S} s demandées).")
    description = input("Décrivez la vidéo : ").strip()
    if not description:
        print("Description vide.")
        return
    print("Génération en cours (cela peut prendre plusieurs minutes)...")
    try:
        rep = await client.videos(
            model=MODELE_VIDEO,
            prompt=description,
            duration_seconds=DUREE_VIDEO_S,
            aspect_ratio="9:16",
            timeout=TIMEOUT_VIDEO,
        )
    except RodiumAIError as e:
        afficher_erreur(e)
        return
    if not rep.data:
        print("Erreur : la réponse ne contient aucune vidéo.")
        return
    await enregistrer_media(rep.data[0], "video.mp4")
    afficher_cout(rep)


# --- Navigation entre les étapes ---------------------------------------------
def demander_choix(index, total):
    """Propose les choix adaptés à l'étape et renvoie 'b', 'r', 's' ou 'q'.
    - étape 1 : pas de retour en arrière
    - dernière étape : pas de 'suivante', on propose de quitter"""
    premiere = index == 0
    derniere = index == total - 1

    options, valides = [], set()
    if not premiere:
        options.append("Revenir en arrière (b)")
        valides.add("b")
    options.append("rester sur cette étape (r)" if premiere else "rester (r)")
    valides.add("r")
    if derniere:
        options.append("quitter (q)")
        valides.add("q")
    else:
        options.append("passer à la suivante (s)")
        valides.add("s")

    if len(options) == 2:
        invite = f"{options[0]} ou {options[1]} ? "
    else:
        invite = f"{options[0]}, {options[1]} ou {options[2]} ? "
    invite = invite[0].upper() + invite[1:]

    while True:
        choix = input(invite).strip().lower()
        if choix in valides:
            return choix
        print(f"Choix invalide. Tapez l'une de ces lettres : {', '.join(sorted(valides))}.")


# --- Boucle principale -------------------------------------------------------
async def main():
    client = RodiumAI()  # lit RODIUMAI_API_KEY dans l'environnement
    etapes = [etape_chat, etape_image, etape_video]
    index = 0
    while True:
        await etapes[index](client)
        choix = demander_choix(index, len(etapes))
        if choix == "b":
            index -= 1
        elif choix == "s":
            index += 1
        elif choix == "q":
            print("Au revoir.")
            break
        # choix == "r" : on reste, l'étape est répétée


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrompu par l'utilisateur.")
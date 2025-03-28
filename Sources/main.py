# Projet : Idle Museum
# Auteurs : Edgar DROUNAU et Achille COURTET

# Si à un moment vous avez lancé une boucle while True par exemple et qu'elle ne s'arrête jamais parce que c'est un thread même quand vous fermez la fenêtre, mettez "taskkill /F /IM python.exe /T" dans votre cmd


# Le jeu fais tourner en permanance des threads permettants de calculer régulièrement l'argent gagné/perdu grâce au musée, au trading etc.
# Le reste des évenements sont ponctuels et sont donc traités dans les fonctions à part appelée quand l'utilisateur la sollicite.
# Les commentaires seront enlevés au final car temporaires

import subprocess
import random
import time
from datetime import datetime
import threading
import json
import os
import tkinter as tk
import sys
import subprocess
import importlib
import math
import sqlite3
import unicodedata
import tkinter as ttk

os.environ['PYTHONMALLOC'] = 'malloc'  # Réduit la fragmentation mémoire

# Définition nom du jeu et noms des devs
game_title = "Idle Museum"
devs = ["Drouni", "Rachid"]
compositeur = "halxrd"

# Vérification et installation des modules
REQUIREMENTS_FILE = "requirements.txt"
def check_and_install_modules():
    with open(REQUIREMENTS_FILE, 'r') as file:
        modules = file.read().splitlines()

    for module in modules:
        module_name = module.split('==')[0]
        try:
            importlib.import_module(module_name)
            print(f"{module_name} est déjà installé.")
        except ImportError:
            print(f"Installation de {module_name}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", module, "--user"])
            print(f"{module_name} a été installé avec succès.")

# Définition des oeuvres de l'utilisateurs et des oeuvres du musée
conn = sqlite3.connect('../Data/data.db')
cursor = conn.cursor()

# Requête pour récupérer toutes les œuvres
cursor.execute("SELECT titre, artiste, annee, description, prix FROM oeuvres")
resultats = cursor.fetchall()

# Création du dictionnaire
oeuvres = {}
for titre, artiste, annee, description, prix in resultats:
    oeuvres[titre] = {
        "artiste": artiste,
        "année": annee,
        "description": description,
        "prix": prix
    }
conn.close() # à compléter par Jules en bdd sql sachant que là ya bcp de très connus, il en faudrait des moins cher pour commencer genre 10/100 $. Objetcif 150 oeuvres dans la bdd.

oeuvres = dict(sorted(oeuvres.items(), key=lambda item: item[1]["prix"])) # classer les oeuvres par ordre croissant de prix
mes_oeuvres = {} # L'user commence avec des oeuvres guez QUE JULES AJOUTERA car un vieux lui a tout céder de ses oeuvres, ce qui va lui permettre de gagner sa première thune du jeu (TOUJOURS EN DOLLARS $)
musee = {} # L'user n'a aucune oeuvre dans son musée au départ mais a déja des places pour 3 tableaux.
musee_lvl = 1 # chaque niveau en plus lui permet d'ajouter 3 tableau supplémentaire dans son musée.
salaires_tot = 0 # le salaire total que l'user payera pour ses employés (musée, traders, douaniers corrompus ?, dealers ?, etc.)
drogue = 0 # à étudier, PAUL TU PEUX TRAVAILLER DESSUS SI TU VEUX, je n'y suis pas encore penché.
username = "user1"
running = True
check_modules = True
check = True
check1 = True
firstrun = True
QG = False
visiteurs = 5

#gestion argent
money_tot = 100 # pour test, sinon !!! 0 ? VERSION FINAL !!!
reseau_state = False # atteindre un certain niveau (musee_lvl) pour le débloquer
trading_state = False # atteindre un certain niveau (musee_lvl) pour le débloquer
trading_tot = 1000 # total de l'argent mis en jeu dans le système de trading ; 0 au début
trading_gains = 0 # ce que l'user a gagné/perdu grâce au trading ; 0 au début.
trading_financements = 1000 # ce que l'user a déposé dans le trading.
trading_mode = "low_risk"
modes_dispo = {"low_risk" : {"pertes" : 0.99, "gains" : 1.01},
                "med_risk" : {"pertes" : 0.95, "gains" : 1.03},
                "high_risk" : {"pertes" : 0.90, "gains" : 1.06}}
musee_employes = 0 # chaque employé augmente les revenus du musée de 50%, avec nombre limite d'employés cohérent avec la taille du musée (musee_lvl)
nb_traders_lvl1 = 0 # chaque traders lvl1 fait augmenter la probabilité de gains de low_risk
nb_traders_lvl2 = 0 # chaque traders lvl2 fait augmenter la probabilité de gains de med_risk
nb_traders_lvl3 = 0 # chaque traders lvl3 fait augmenter la probabilité de gains de high_risk
concordance_musee_lvl_prix_amelioration = {1: 10, 2: 100, 3: 200, 4: 500, 5: 1000, 6: 2000, 7: 5000, 8: 10000, 9: 20000, 10: 50000, 11: 100000, 12: 200000, 13: 500000, 14: 1000000, 15: 2000000, 16: 5000000, 17: 10000000, 18: 20000000, 19: 50000000, 20: 100000000, 21: 200000000, 22: 500000000, 23: 1000000000, 24: 2000000000, 25: 5000000000, 26: 10000000000, 27: 20000000000, 28: 50000000000, 29: 100000000000, 30: 200000000000, 31: 500000000000, 32: 1000000000000, 33: 2000000000000, 34: 5000000000000, 35: 10000000000000, 36: 20000000000000, 37: 50000000000000, 38: 100000000000000, 39: 200000000000000, 40: 500000000000000}
confiance_cartel = 0.5
confiance_police = 0.5
a1 = 0
boost_revenus = 1

# transformable en concordance par la suite mais là, en gros, pour le niveau 1 l'amélioration coûte 10$, pour le niveau 2 l'amélioration coûte 100$, etc. car plus de frais pour la surveillance (oeuvres plus cheres) etc. etc.

## thread nb visiteurs en temps donné
def update_visiteurs():
    global visiteurs
    while running:
        if musee == {}:
            visiteurs = 0
        musee_gains = 0
        for oeuvre in musee:
            musee_gains += musee[oeuvre]['prix']
        tempo = int(musee_gains * (2*(math.sqrt(math.sqrt(math.sqrt(math.sqrt(musee_gains * 0.5)))))))
        if tempo >= (((0.5 + musee_lvl)**2)**2)**2:
            tempo == (1 + musee_lvl)**8
        if tempo >= 5:
            visiteurs = tempo + (int(random.uniform(0.94,1.06) * tempo))
        time.sleep(random.uniform(2,5))
            
    print("Thread update_visiteurs arrêté")

## Charger la progression
try:
    if os.path.exists("ping.json"):
        with open("ping.json", "r") as fichier:
            data = json.load(fichier)
            last_ping_time = datetime.fromisoformat(data["date"])
            money_tot = data["money_tot"]
            oeuvres = data["oeuvres"]
            modes_dispo = data["modes_dispo"]
            mes_oeuvres = data["mes_oeuvres"]
            musee = data["musee"]
            salaires_tot = data["salaires_tot"]
            reseau_state = data["reseau_state"]
            trading_state = data["trading_state"]
            trading_tot = data["trading_tot"]
            trading_gains = data["trading_gains"]
            trading_financements = data["trading_financements"]
            trading_mode = data["trading_mode"]
            musee_lvl = data["musee_lvl"]
            musee_employes = data["musee_employes"]
            drogue = data["drogue"]
            username = data["username"]
            nb_traders_lvl1 = data["nb_traders_lvl1"]
            nb_traders_lvl2 = data["nb_traders_lvl2"]
            nb_traders_lvl3 = data["nb_traders_lvl3"]
            confiance_cartel = data["confiance_cartel"]
            confiance_police = data["confiance_police"]
            event_history = data["reseau_events"]
            active_events = data["active_events"]
            active_jose_event = data["active_jose_event"]
            event_queue = data["event_queue"]
            message_history = data["message_history"]
            boost_revenus = data["boost_revenus"]
            QG = data["QG"]
except:
    if os.path.exists("ping.json"):
        with open("ping.json", "r") as fichier:
            data = json.load(fichier)
            last_ping_time = datetime.strptime(data["date"], "%Y-%m-%dT%H:%M:%S.%f")
            money_tot = data["money_tot"]
            oeuvres = data["oeuvres"]
            modes_dispo = data["modes_dispo"]
            mes_oeuvres = data["mes_oeuvres"]
            musee = data["musee"]
            salaires_tot = data["salaires_tot"]
            reseau_state = data["reseau_state"]
            trading_state = data["trading_state"]
            trading_tot = data["trading_tot"]
            trading_gains = data["trading_gains"]
            trading_financements = data["trading_financements"]
            trading_mode = data["trading_mode"]
            musee_lvl = data["musee_lvl"]
            musee_employes = data["musee_employes"]
            drogue = data["drogue"]
            username = data["username"]
            nb_traders_lvl1 = data["nb_traders_lvl1"]
            nb_traders_lvl2 = data["nb_traders_lvl2"]
            nb_traders_lvl3 = data["nb_traders_lvl3"]
            confiance_cartel = data["confiance_cartel"]
            confiance_police = data["confiance_police"]
            event_history = data["reseau_events"]
            active_events = data["active_events"]
            active_jose_event = data["active_jose_event"]
            event_queue = data["event_queue"]
            message_history = data["message_history"]
            boost_revenus = data["boost_revenus"]
            QG = data["QG"]

## Calcul des gains afk
def calculate_time_afk():
    global last_ping_time
    if 'last_ping_time' in globals():
        time_away = datetime.now() - last_ping_time
        return time_away.total_seconds()
    return 0

time_afk = calculate_time_afk()
if time_afk != 0 and time_afk > 60:
    musee_gains = 0
    if musee != {}:
        for oeuvre in musee:
            musee_gains += musee[oeuvre]['prix']*0.0005
        if (musee_gains * (1.5 ** musee_employes) - salaires_tot) < 0:
            gains_afk = round(((- 10 * (math.sqrt( - musee_gains * (1.5 ** musee_employes) + salaires_tot))) / 5), 3)  # ou / 6
        else:
            gains_afk = round(((10 * (math.sqrt(musee_gains * (1.5 ** musee_employes) - salaires_tot))) / 5), 3)  # ou / 6
        money_tot += gains_afk
    else:
        gains_afk = 0



## section du menu : permet de débloquer trading et réseau à un certain musee_lvl
class menu:

    def unlock_trading(musee_lvl):
        global trading_state
        if musee_lvl >= 10:
            trading_state = True
            return trading_state #Lance un dialogue qui présente le module
        else :
            return None
    
    def unlock_reseau(musee_lvl):
        global reseau_state
        if musee_lvl >= 15:
            reseau_state = True
            return True
        return False

## section "Mes oeuvres"
class mesoeuvres:

    def achat(self, nom_oeuvre):
        global money_tot, oeuvres
        if oeuvres[nom_oeuvre]["prix"] > money_tot:
            return "Vous n'avez pas assez d'argent pour acheter cette oeuvre"
        else:
            details = oeuvres.pop(nom_oeuvre)
            mes_oeuvres[nom_oeuvre] = details
            money_tot -= details["prix"]
            return mes_oeuvres


    def place_musee(nom_oeuvre):
        global mes_oeuvres, musee, musee_lvl
        if len(musee) >= 2 * musee_lvl:
            return "Le musée est déjà plein"
        details = mes_oeuvres.pop(nom_oeuvre)
        musee[nom_oeuvre] = details
        return musee

    def __init__(self):
        self.acheteurs_profiles = {
            'collector': {'min_offer': 0.8, 'max_offer': 1.2, 'success_chance': 0.6},
            'investor': {'min_offer': 0.7, 'max_offer': 1.1, 'success_chance': 0.4},
            'tourist': {'min_offer': 0.9, 'max_offer': 1.0, 'success_chance': 0.8}
        }

    def get_cheapest_oeuvre(self):
        return next(iter(oeuvres.items())) if oeuvres else None

    def negocier_prix(self, oeuvre_name, buyer_type):
        profile = self.acheteurs_profiles[buyer_type]
        original_price = oeuvres[oeuvre_name]['prix']
        offered_price = original_price * random.uniform(profile['min_offer'], profile['max_offer'])
        success = random.random() < profile['success_chance']
        return round(offered_price, 2), success


## section "Mon musée"
class monmusee:

    def retire_musee(nom_oeuvre):
        details = musee.pop(nom_oeuvre)
        mes_oeuvres[nom_oeuvre] = details
        return mes_oeuvres

    def embaucher_employe():
        global musee_employes, musee_lvl, salaires_tot, money_tot
        if money_tot <= 50 * (musee_employes + 1):
            return "Vous n'avez pas assez d'argent pour embaucher un employé."
        if musee_employes >= musee_lvl:
            return "Vous avez déjà autant d'employés que vous pouvez avoir pour cette taille de musée."
        musee_employes += 1
        salaires_tot += 2.5 * musee_employes # OU 2.5 ** musee_employes A MODIFIER DANS UPDATE_MONEY_TOT AUSSI
        return musee_employes, salaires_tot

    def agrandir_musee():
        global musee_lvl, concordance_musee_lvl_prix_amelioration, money_tot
        if money_tot < concordance_musee_lvl_prix_amelioration[musee_lvl + 1]:
            return "Vous n'avez pas assez d'argent pour agrandir le musée."
        musee_lvl += 1
        money_tot -= concordance_musee_lvl_prix_amelioration[musee_lvl]
        menu.unlock_trading(musee_lvl)
        menu.unlock_reseau(musee_lvl)
        return musee_lvl, money_tot



## section "Algo Trading"
class algotrade:

    def deposer(self, montant):
        """Dépose de l'argent dans le trading."""
        global trading_tot, trading_gains, money_tot
        if type(montant) != int and type(montant) != float:
            return "Veuillez entrer une valeur numérique"
        montant = round(montant, 2)
        if montant > money_tot:
            return "Veuillez choisir un montant inférieur ou égal à votre argent total"
        elif montant < 0:
            return "Veuillez choisir un montant positif"
        else:
            trading_tot += montant
            money_tot -= montant
            return trading_tot, money_tot

    def change_trading_mode(mode):
        """Change le mode de trading."""
        global trading_mode
        if mode not in ["low_risk", "med_risk", "high_risk"]:
            return "Mode de trading invalide"
        else:
            trading_mode = mode
            return trading_mode

    def recup(self, montant):
        """Retire de l'argent du trading."""
        global trading_tot, trading_gains, money_tot
        if type(montant) != int and type(montant) != float:
            return "Veuillez entrer une valeur numérique"
        montant = round(montant, 2)
        if montant > trading_tot:
            return "Veuillez choisir un montant inférieur ou égal à votre total de trading"
        elif montant < 0:
            return "Veuillez choisir un montant positif"
        else:
            trading_tot -= montant
            money_tot += montant
            return trading_tot, money_tot

    def traders1(self):
        """Embauche un trader niveau 1."""
        global salaires_tot, trading_mode, nb_traders_lvl1, money_tot
        if money_tot < 1000:
            return "Vous n'avez pas assez d'argent pour embaucher un trader niveau 1"
        elif nb_traders_lvl1 >= 20:
            return "Vous avez déjà embauché 20 traders niveau 1. En embaucher plus serai une perte d'argent."
        else:
            nb_traders_lvl1 += 1
            salaires_tot += 2.5
            modes_dispo["low_risk"]["gains"] += 0.003 / nb_traders_lvl1
            modes_dispo["low_risk"]["pertes"] += 0.001 / nb_traders_lvl1
            return modes_dispo, salaires_tot, nb_traders_lvl1

    def traders2(self):
        """Embauche un trader niveau 2."""
        global salaires_tot, trading_mode, nb_traders_lvl2, money_tot
        if money_tot < 100000:
            return "Vous n'avez pas assez d'argent pour embaucher un trader niveau 2"
        elif nb_traders_lvl2 >= 20:
            return "Vous avez déjà embauché 20 traders niveau 2. En embaucher plus serai une perte d'argent."
        else:
            nb_traders_lvl2 += 1
            salaires_tot += 500
            modes_dispo["med_risk"]["gains"] += 0.012 / nb_traders_lvl2
            modes_dispo["med_risk"]["pertes"] += 0.002 / nb_traders_lvl2
            return modes_dispo, salaires_tot, nb_traders_lvl2

    def traders3(self):
        """Embauche un trader niveau 3."""
        global salaires_tot, trading_mode, nb_traders_lvl3, money_tot
        if money_tot < 10000000:
            return "Vous n'avez pas assez d'argent pour embaucher un trader niveau 3"
        elif nb_traders_lvl3 >= 20:
            return "Vous avez déjà embauché 20 traders niveau 3. En embaucher plus serai une perte d'argent."
        else:
            nb_traders_lvl3 += 1
            salaires_tot += 50000
            modes_dispo["high_risk"]["gains"] += 0.018 / nb_traders_lvl3
            modes_dispo["high_risk"]["pertes"] += 0.005 / nb_traders_lvl3
            return modes_dispo, salaires_tot, nb_traders_lvl3



## section "réseau"
class reseau:
    def __init__(self):
        self.event_queue = []
        self.message_history = []
        self.jose_events = {
            "introduction": {
                "message": "José: Salut... On m'a dit que tu savais garder des secrets.\nLe cartel a besoin d'un endroit discret. Intéressé par un partenariat ?",
                "choices": [
                    {
                        "text": "Accepter", 
                        "effects": {"confiance_cartel": 0.3, "confiance_police": -0.15}
                    },
                    {
                        "text": "Refuser", 
                        "effects": {"confiance_cartel": -0.45}
                    }
                ]
            },
            "convoi_special": {
                "message": "José: On a besoin de stocker des marchandises sensibles dans ton musée 48h.\n20% de bonus si tu coopères.",
                "choices": [
                    {
                        "text": "Accepter le convoi",
                        "effects": {"confiance_cartel": 0.15, "confiance_police": -0.2, "revenus": 0.2}
                    },
                    {
                        "text": "Refuser catégoriquement", 
                        "effects": {"confiance_cartel": -0.1, "confiance_police": 0.15}
                    }
                ],
                "conditions": {"musee_lvl": 5},
                "probability": 0.15
            },
            "blanchiment_argent": {
                "message": "José: On pourrait blanchir 30% de tes gains via des acquisitions...\nIntéressé ?",
                "choices": [
                    {
                        "text": "Accepter le blanchiment (+30% revenus)", 
                        "effects": {"confiance_cartel": 0.2, "confiance_police": -0.1, "revenus": 0.3}
                    },
                    {
                        "text": "Refuser (risque de représailles)", 
                        "effects": {"confiance_cartel": -0.2}
                    }
                ],
                "conditions": {"confiance_cartel_min": 0.4},
                "probability": 0.10
            },
            "corruption_douaniers": {
                "message": "José: Des douaniers sont prêts à fermer les yeux sur certaines œuvres...\nPour 20% de leur valeur.",
                "choices": [
                    {
                        "text": "Corrompre les douaniers", 
                        "effects": {"confiance_cartel": 0.1, "confiance_police": -0.2, "money_tot": -0.2}
                    },
                    {
                        "text": "Respecter la loi", 
                        "effects": {"confiance_police": 0.2}
                    }
                ],
                "conditions": {"musee_lvl": 3},
                "probability": 0.25
            },
            "crise_otages": {
                "message": "José: Un rival nous menace ! Ton musée est pris en otage.\nComment réagis-tu ?",
                "choices": [
                    {
                        "text": "Payer la rançon (50% de l'argent)", 
                        "effects": {"confiance_cartel": 0.25, "money_tot": -0.5}
                    },
                    {
                        "text": "Négocier avec la police", 
                        "effects": {"confiance_police": 0.3, "confiance_cartel": -0.3}
                    }
                ],
                "conditions": {"confiance_cartel_min": 0.7},
                "probability": 0.10
            },
            "partenariat_cartel": {
                "message": "José: Le cartel veut faire de ton musée son QG officiel.\nAvantages garantis !",
                "choices": [
                    {
                        "text": "Accepter le partenariat", 
                        "effects": {"revenus": 0.5, "confiance_police": -0.1, "confiance_cartel": 0.3}
                    },
                    {
                        "text": "Garder son indépendance", 
                        "effects": {"confiance_cartel": -0.2}
                    }
                ],
                "conditions": {"musee_lvl": 10, "QG": True},
                "probability": 0.05
            },
            "inspection_surprise": {
                "message": "José: Les flics débarquent ! Ils veulent tout contrôler...",
                "choices": [
                    {
                        "text": "Soudoyer les inspecteurs (50 000$)", 
                        "effects": {"confiance_police": -0.2, "money_tot": -0.5, "confiance_cartel": 0}
                    },
                    {
                        "text": "Coopérer avec l'enquête", 
                        "effects": {"confiance_police": 0.3, "confiance_cartel": -0.2}
                    }
                ],
                "probability": 0.20
            },
            "parrainage_culturel": {
                "message": "José: Le cartel finance une nouvelle aile pour toi.\n3 places supplémentaires !",
                "choices": [
                    {
                        "text": "Accepter le financement", 
                        "effects": {"musee_slots": 3, "confiance_cartel": 0.2, "confiance_police": -0.05}
                    },
                    {
                        "text": "Refuser par principe", 
                        "effects": {"confiance_cartel": -0.2}
                    }
                ],
                "conditions": {"oeuvres_exposees": 10},
                "probability": 0.15
            }
        }
        self.events = self.jose_events
        self.active_jose_event = None
        self.active_events = {}
        self.event_history = []
        self.drogue_price = 5000
        self.probability_multiplier = 1.0
        self.introduction_done = False
        self.active_event = None
        self.load_conversation()  # Charger l'historique existant
    
    def add_event_to_queue(self, event_name):
        self.event_queue.append(event_name)
        
    def process_event_queue(self):
        while self.event_queue:
            event = self.event_queue.pop(0)
            self.trigger_event(event)

    def load_conversation(self):
        try:
            with open('conversations.json', 'r') as f:
                self.message_history = json.load(f)
        except FileNotFoundError:
            self.message_history = []

    def get_active_events_descriptions(self):
        return [self.events[event_name]["description"] for event_name in self.active_events]

    def check_conditions(self, event_name):
        event = self.events[event_name]
        conditions = event.get("conditions", {})
        
        for cond, value in conditions.items():
            if cond == "musee_lvl" and musee_lvl < value:
                return False
            if cond == "reseau_state" and not reseau_state:
                return False
            if cond == "confiance_cartel_min" and confiance_cartel < value:
                return False
        return True

    def check_random_events(self):
        if random.random() < 0.3:  # 30% de chance d'événement
            self.trigger_event("convoi_special")

    def trigger_event(self, event_name):
        if event_name in self.jose_events:
            self.active_jose_event = event_name

    """def trigger_event(self, event_name):
        if self.check_conditions(event_name) and random.random() < self.events[event_name]["probability"] * self.probability_multiplier:
            self.active_events[event_name] = {
                "start_time": time.time(),
                "duration": self.events[event_name].get("duration", 172800)
            }
            self.event_history.append((time.strftime("%Y-%m-%d %H:%M"), self.events[event_name]["description"]))
            return self.events[event_name]
        return None"""

    def apply_effect(self, effect):
        if isinstance(effect, dict):
            for key, value in effect.items():
                if key == "confiance_cartel":
                    global confiance_cartel
                    confiance_cartel = max(0, min(1, confiance_cartel + value))
                elif key == "confiance_police":
                    global confiance_police
                    confiance_police = max(0, min(1, confiance_police + value))

    def update_events(self):
        current_time = time.time()
        expired_events = []
        
        for event_name, details in self.active_events.items():
            if current_time > details["start_time"] + details["duration"]:
                expired_events.append(event_name)
                if "expiration_effect" in self.events[event_name]:
                    self.apply_effect(self.events[event_name]["expiration_effect"])
        
        for event in expired_events:
            del self.active_events[event]

    def achat_drogue(self, quantity):
        global money_tot, drogue, confiance_cartel
        total_cost = quantity * self.drogue_price
        
        if money_tot >= total_cost:
            money_tot -= total_cost
            drogue += quantity
            confiance_cartel = min(1, confiance_cartel + 0.02 * quantity)
            return True
        return False

    def negocier_avec_police(self):
        global confiance_police, confiance_cartel
        if confiance_police < 0.5:
            confiance_police += 0.15
            confiance_cartel -= 0.1
            return True
        return False

    def save_conversation(self):
        with open('conversations.json', 'w') as f:
            json.dump(self.message_history, f)

    def load_conversation(self):
        try:
            with open('conversations.json', 'r') as f:
                self.message_history = json.load(f)
        except FileNotFoundError:
            self.message_history = []


## def update pour l'actualisation permanante de l'argent gagné avec les expositions
def update_money_tot():
    global money_tot, salaires_tot, nb_traders_lvl1, nb_traders_lvl2, nb_traders_lvl3, musee_employes, modes_dispo, running
    while running:
        musee_gains = 0
        for oeuvre in musee:
            musee_gains += musee[oeuvre]['prix']*0.0005
        if (musee_gains * (1.5 ** musee_employes) - salaires_tot) < 0:
            money_tot = round((money_tot - 10 * (math.sqrt( - musee_gains * (1.5 ** musee_employes) + salaires_tot))), 3)
        else:
            money_tot = round((money_tot + 10 * (math.sqrt(musee_gains * (1.5 ** musee_employes) - salaires_tot))), 3)

        if money_tot > 1000000000000000:
            money_tot = 1000000000000000
            print("Désormais, le surplus de votre argent ne vous sert plus à rien. Vous décidez donc de distribuer vos gains à une association d'art.")

        if money_tot < 0:
            money_tot = 0
            gains = musee_gains * (1.5 ** musee_employes) - salaires_tot

            while gains < 0:
                if nb_traders_lvl3 > 0:
                    modes_dispo["high_risk"]["gains"] -= 0.018 / nb_traders_lvl3
                    modes_dispo["high_risk"]["pertes"] -= 0.005 / nb_traders_lvl3
                    nb_traders_lvl3 -= 1
                    salaires_tot -= 50000
                elif nb_traders_lvl2 > 0:
                    modes_dispo["med_risk"]["gains"] -= 0.012 / nb_traders_lvl2
                    modes_dispo["med_risk"]["pertes"] -= 0.002 / nb_traders_lvl2
                    nb_traders_lvl2 -= 1
                    salaires_tot -= 500
                elif nb_traders_lvl1 > 0:
                    modes_dispo["low_risk"]["gains"] += 0.003 / nb_traders_lvl1
                    modes_dispo["low_risk"]["pertes"] += 0.001 / nb_traders_lvl1
                    nb_traders_lvl1 -= 1
                    salaires_tot -= 2.5
                elif musee_employes > 0:
                    salaires_tot -= 2.5 * musee_employes # MODIFIABLE ICI
                    musee_employes -= 1

                gains = musee_gains * (1.5 ** musee_employes) - salaires_tot

            print(f"Vous devez vous endetter pour continuer à payer les salaires de vos traders et de vos employés. Au lieu de vous endetter, vous décidez de virer le surplus de traders/employés. Il vous reste {musee_employes} employés dans votre musée, {nb_traders_lvl1} de traders low risk, {nb_traders_lvl2} de traders medium risk et {nb_traders_lvl3} de traders high risk")

        print(f"money tot : {money_tot}")
        time.sleep(0.1)

    print("Thread update_money_tot arrêté")


## def update pour l'actualisation permanante du trading
def update_trading():
    global trading_tot, trading_financements, trading_gains, trading_mode, modes_dispo
    while running:
        g_p = round(random.uniform(modes_dispo[trading_mode]["pertes"], modes_dispo[trading_mode]["gains"]), 3) # gains/pertes OU round(..., 4)
        trading_tot = round((trading_tot * g_p), 2)
        trading_gains = trading_tot - trading_financements
        """print(f"trading : {trading_tot, trading_financements, trading_gains, trading_mode}")"""
        time.sleep(2)
    print("Thread update_trading arrêté")


## Ping pour garder la progression
def ping(app_instance):
    while running:
        nom_fichier = "ping.json"
        now =  datetime.now().isoformat() # Récupérer la date et l'heure actuelles en ISO
        contenu = {"date" : now, "username" : username, "modes_dispo" : modes_dispo, "money_tot" : money_tot, "oeuvres" : oeuvres, "mes_oeuvres" : mes_oeuvres, "musee" : musee, "musee_lvl" : musee_lvl, "salaires_tot" : salaires_tot, "drogue" : drogue, "reseau_state" : reseau_state, "trading_state" : trading_state, "trading_tot" : trading_tot, "trading_gains" : trading_gains, "trading_financements" : trading_financements, "trading_mode" : trading_mode, "musee_employes" : musee_employes, "nb_traders_lvl1" : nb_traders_lvl1, "nb_traders_lvl2" : nb_traders_lvl2, "nb_traders_lvl3" : nb_traders_lvl3, "confiance_cartel": confiance_cartel, "confiance_police": confiance_police, "reseau_events": app_instance.reseau.event_history[-50:], "active_events": app_instance.reseau.active_events, "active_jose_event": app_instance.reseau.active_jose_event, "event_queue": app_instance.reseau.event_queue, "message_history": app_instance.reseau.message_history, "boost_revenus": boost_revenus, "QG": QG}
        # Ouvrir le fichier en mode écriture (ou le créer s'il n'existe pas)
        with open(nom_fichier, "w") as fichier:
            json.dump(contenu, fichier, indent=4)

        """print("ping effectué")"""

        time.sleep(30)
    print("Thread ping arrêté")

## Ping de fin pour garder la progression
def ping_fin(app_instance):
    nom_fichier = "ping.json"
    now =  datetime.now().isoformat() # Récupérer la date et l'heure actuelles en ISO
    contenu = {"date" : now, "username" : username, "modes_dispo" : modes_dispo, "money_tot" : money_tot, "oeuvres" : oeuvres, "mes_oeuvres" : mes_oeuvres, "musee" : musee, "musee_lvl" : musee_lvl, "salaires_tot" : salaires_tot, "drogue" : drogue, "reseau_state" : reseau_state, "trading_state" : trading_state, "trading_tot" : trading_tot, "trading_gains" : trading_gains, "trading_financements" : trading_financements, "trading_mode" : trading_mode, "musee_employes" : musee_employes, "nb_traders_lvl1" : nb_traders_lvl1, "nb_traders_lvl2" : nb_traders_lvl2, "nb_traders_lvl3" : nb_traders_lvl3, "confiance_cartel": confiance_cartel, "confiance_police": confiance_police, "reseau_events": app_instance.reseau.event_history[-50:], "active_events": app_instance.reseau.active_events, "active_jose_event": app_instance.reseau.active_jose_event, "event_queue": app_instance.reseau.event_queue, "message_history": app_instance.reseau.message_history, "boost_revenus": boost_revenus, "QG": QG}
    # Ouvrir le fichier en mode écriture (ou le créer s'il n'existe pas)
    with open(nom_fichier, "w") as fichier:
        json.dump(contenu, fichier, indent=4)

    print("ping de fin effectué")

mes_oeuvres_instance = mesoeuvres()
mon_musee_instance = monmusee()
algo_trade_instance = algotrade()
reseau_instance = reseau()

# bouton "placer au musée" servant d'exemple pour ensuite le relier à l'interface
"""mes_oeuvres_instance.achat("La Nuit étoilée")
mes_oeuvres_instance.place_musee("La Nuit étoilée")"""

class PhoneInterface(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg='#0d1a26')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Configuration du canvas de discussion
        self.chat_canvas = tk.Canvas(self, bg="#0d1a26", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.chat_canvas.yview)
        self.chat_frame = tk.Frame(self.chat_canvas, bg="#0d1a26")
        
        self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        self.chat_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Zone de réponse
        self.response_frame = tk.Frame(self, bg="#1a1a1a", padx=10, pady=10)
        
        # Disposition
        self.scrollbar.pack(side="right", fill="y")
        self.chat_canvas.pack(side="top", fill="both", expand=True)
        self.response_frame.pack(side="bottom", fill="x")
        
        self.bind("<Configure>", self.update_scrollregion)

    def update_scrollregion(self, event=None):
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
    
    def add_message(self, text, is_jose=True):
        bubble_frame = tk.Frame(self.chat_frame, bg="#0d1a26")
        bubble_color = "#2d527d" if is_jose else "#1d3b5c"
        
        bubble = tk.Frame(bubble_frame, bg=bubble_color, padx=12, pady=8)
        tk.Label(bubble, 
                text=text,
                wraplength=300,
                fg="white",
                bg=bubble_color,
                font=("Arial", 11),
                justify="left" if is_jose else "right").pack()
        
        bubble.pack(side="left" if is_jose else "right", fill="x", expand=True)
        bubble_frame.pack(fill="x", pady=4)
        self.chat_canvas.yview_moveto(1.0)
        self.chat_history.append((text, is_jose))

    def add_message(self, text, is_jose=True):
        bubble_frame = tk.Frame(self.chat_frame, bg='#0d1a26')
        bubble = tk.Frame(bubble_frame, bg='#2d527d' if is_jose else '#1d3b5c', padx=10, pady=5)
        label = tk.Label(bubble, 
                        text=text,
                        wraplength=300,
                        fg='white',
                        bg=bubble['bg'],
                        justify='left' if is_jose else 'right')
        label.pack()
        bubble.pack(fill='x', expand=True)
        bubble_frame.pack(fill='x', pady=5)
        self.chat_canvas.yview_moveto(1.0)

    def show_responses(self, responses):
        for widget in self.response_frame.winfo_children():
            widget.destroy()
            
        for i, response in enumerate(responses):
            btn = tk.Button(self.response_frame,
                           text=response,
                           command=lambda r=i: self.handle_response(r),
                           bg='#3498db',
                           fg='white')
            btn.pack(side='left', padx=5)

    def handle_response(self, response_index):
        if self.master.reseau.active_jose_event:
            event = self.master.reseau.jose_events[self.master.reseau.active_jose_event]
            choice = event["choices"][response_index]
            
            # Appliquer les effets
            for effect, value in choice["effects"].items():
                if effect == "confiance_cartel":
                    global confiance_cartel
                    confiance_cartel = max(0, min(1, confiance_cartel + value))
                elif effect == "confiance_police":
                    global confiance_police
                    confiance_police = max(0, min(1, confiance_police + value))
            
            # Ajouter la réponse du joueur
            self.add_message(f"Vous: {choice['text']}", is_jose=False)
            
            # Ajouter la réponse de José
            if event["choices"][0]["effects"]["confiance_cartel"] >= 0:
                self.add_message("José: Bon choix, on va bien travailler ensemble.", is_jose=True)
            else:
                self.add_message("José: Tu vas le regretter...", is_jose=True)
            
            self.master.reseau.active_jose_event = None
            self.master.update_ui()

class PhoneFrame(tk.Frame):
    def __init__(self, parent, app_instance):
        super().__init__(parent, bg='#0d1a26')
        self.app_instance = app_instance  # Store the reference to the app instance
        self.chat_history = []
        
        # Configuration du défilement
        self.canvas = tk.Canvas(self, bg='#0d1a1a', highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.chat_frame = tk.Frame(self.canvas, bg='#0d1a1a')
        
        self.canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Zone de réponse
        self.response_frame = tk.Frame(self, bg='#1a1a1a')
        
        # Disposition
        self.scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='top', fill='both', expand=True)
        self.response_frame.pack(side='bottom', fill='x')

        # Trust level labels
        self.trust_label = tk.Label(self, text="", bg='#1a1a1a', fg='white')
        self.trust_label.pack(side='bottom', fill='x')

        self.after(100, self.check_new_messages)

        self.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def check_new_messages(self):
        if hasattr(self.master, 'reseau'):
            reseau = self.master.reseau
            current_count = len(self.chat_history)
            new_count = len(reseau.message_history)
            
            if new_count > current_count:
                new_messages = reseau.message_history[current_count:new_count]
                for msg, is_jose in new_messages:
                    self.add_message(msg, is_jose)
        self.after(1000, self.check_new_messages)

    def update_trust_levels(self):
        self.trust_label.config(text=f"Confiance Cartel: {confiance_cartel:.2f} | Confiance Police: {confiance_police:.2f}")

    def add_message(self, text, is_jose=True):
        bubble_color = '#2d527d' if is_jose else '#1d3b5c'
        msg_frame = tk.Frame(self.chat_frame, bg='#0d1a1a', padx=10, pady=5)
        
        bubble = tk.Frame(msg_frame, bg=bubble_color, padx=12, pady=8)
        tk.Label(bubble, 
                text=text,
                wraplength=300,
                fg='white',
                bg=bubble_color,
                font=('Arial', 11),
                justify='left' if is_jose else 'right').pack()
        
        bubble.pack(side='left' if is_jose else 'right', fill='x', expand=True)
        msg_frame.pack(fill='x', pady=5)
        self.canvas.yview_moveto(1.0)
        self.chat_history.append((text, is_jose))

    def show_responses(self, responses):
        """Display response options for the user to choose from."""
        for widget in self.response_frame.winfo_children():
            widget.destroy()  # Clear previous response buttons
        
        for idx, response in enumerate(responses):
            btn = tk.Button(self.response_frame,
                           text=response,
                           command=lambda r=idx: self.handle_response(r),
                           bg="#3498db",
                           fg="white",
                           activebackground="#2980b9",
                           font=("Arial", 10),
                           padx=15,
                           pady=8)
            btn.pack(side="left", padx=5)

    def handle_response(self, response_index):
        if self.app_instance.reseau.active_jose_event:
            event = self.app_instance.reseau.jose_events[self.app_instance.reseau.active_jose_event]
            
            # Check if the response_index is valid
            if response_index < 0 or response_index >= len(event["choices"]):
                print(f"Erreur: L'index de réponse {response_index} est hors limites.")
                return  # Exit the method if the index is invalid
            
            choice = event["choices"][response_index]
            
            # Appliquer les effets
            for effect, value in choice["effects"].items():
                if effect == "confiance_cartel":
                    global confiance_cartel
                    confiance_cartel = max(0, min(1, confiance_cartel + value))
                elif effect == "confiance_police":
                    global confiance_police
                    confiance_police = max(0, min(1, confiance_police + value))
            
            # Ajouter la réponse du joueur
            self.add_message(f"Vous: {choice['text']}", is_jose=False)
            
            # Ajouter la réponse de José
            if event["choices"][0]["effects"]["confiance_cartel"] >= 0:
                self.add_message("José: Bon choix, on va bien travailler ensemble.", is_jose=True)
            else:
                self.add_message("José: Tu vas le regretter...", is_jose=True)
            
            # Clear response buttons
            for widget in self.response_frame.winfo_children():
                widget.destroy()
            
            # Update trust levels
            self.update_trust_levels()
            
            # Check for game over conditions
            self.check_game_over_conditions()
            
            self.app_instance.reseau.active_jose_event = None
            self.app_instance.update_ui()
            self.app_instance.reseau.check_random_events()

    def check_game_over_conditions(self):
        global confiance_cartel, confiance_police
        
        if confiance_cartel <= 0:
            self.show_alert("Game Over", "Vous avez perdu ! Le cartel ne vous fait plus confiance.", is_error=True)
            self.reset_game()  # Call a method to reset or exit the game
        elif confiance_police < 0.2:
            if random.random() < 0.5:  # 50% chance of being caught
                self.show_alert("Prison", "Vous avez été attrapé par la police et envoyé en prison.", is_error=True)
                self.reset_game()  # Call a method to reset or exit the game

    def reset_game(self):
        global money_tot, confiance_cartel, confiance_police, mes_oeuvres, musee, musee_lvl
        # Reset game variables to initial state
        money_tot = 100  # or whatever your starting amount is
        confiance_cartel = 0.5
        confiance_police = 0.5
        mes_oeuvres = {}
        musee = {}
        musee_lvl = 1
        # Optionally, you can reload the UI or reset other game states
        self.page_oeuvres()  # Reload the main page or any other page
    
class CustomAlert(tk.Toplevel):
    def __init__(self, parent, title, message, is_error=False, duree_base=1500):
        super().__init__(parent)
        self.parent = parent
        self.is_error = is_error
        self.duree_base = duree_base  # Temps de base initial
        self.scroll_speed = 2
        self.frame_delay = 20
        self.title_text = f"[{title}]"
        self.message_text = message
        self.animation_id = None
        self.has_scrolled = False

        # CONFIGURATION DE LA HAUTEUR DE L'ALERTE (40px)
        self.alert_height = 40

        # CONFIGURATION DE LA LARGEUR DE L'ALERTE (largeur parent)
        self.alert_width = parent.winfo_width()

        # Configuration visuelle
        self.border_size = 2
        self.configure(bg='#404040', highlightthickness=0)
        self.overrideredirect(True)

        # Positionnement initial
        parent.update_idletasks()
        start_x = parent.winfo_x() + 8
        initial_y = parent.winfo_y() - parent.winfo_height()
        self.target_y = parent.winfo_y() + int(parent.winfo_height() * (8/24))

        self.geometry(f"{self.alert_width}x{self.alert_height}+{start_x}+{initial_y}")
        self.attributes('-alpha', 0.0)

        # Structure de l'alerte
        self.setup_ui()
        self.after(10, lambda: self.animate_entrance(initial_y, self.target_y))

        # Rester dans la fenêtre Tkinter
        self.parent = parent
        self.offset_x = 8  # Marge horizontale fixe par rapport à la fenêtre parent
        self.bind_to_parent_movement()

    def bind_to_parent_movement(self):
        """Active le suivi des mouvements de la fenêtre parent"""
        def update_position(event):
            # Calculer la nouvelle position
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_height = self.parent.winfo_height()

            new_x = parent_x + self.offset_x
            new_y = parent_y + int(parent_height * (8/24))

            # Appliquer la nouvelle position
            self.geometry(f"+{new_x}+{new_y}")

            # Mettre à jour la taille si nécessaire
            new_width = self.parent.winfo_width()
            if new_width != self.alert_width:
                self.alert_width = new_width
                self.canvas.config(width=new_width)
                self.set_initial_positions()

        # Surveiller les mouvements et redimensionnements du parent
        self.parent.bind('<Configure>', update_position)
        self.bind('<Destroy>', lambda e: self.parent.unbind('<Configure>'))

    def setup_ui(self):
        # Cadre principal avec bordures
        self.main_frame = tk.Frame(self, bg='#808080', height=self.alert_height)
        self.main_frame.pack(fill='both', expand=True)

        # Bordures haut/bas
        tk.Frame(self.main_frame,
               height=self.border_size,
               bg='#606060').pack(fill='x', side='top')
        tk.Frame(self.main_frame,
               height=self.border_size,
               bg='#606060').pack(fill='x', side='bottom')

        # Canvas pour contenu défilant
        # Marge verticale externe de 3px (pady=3)
        self.canvas = tk.Canvas(self.main_frame,
                              bg='#808080',
                              height=self.alert_height-(self.border_size*2),
                              width=self.alert_width,
                              highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, padx=10, pady=0)

        # Création des éléments texte
        self.title_color = '#ff5555' if self.is_error else '#2ecc71'
        # Position Y à 20px pour centrage vertical (marge interne)
        self.title_id = self.canvas.create_text(0, 17.5,
                                              text=self.title_text,
                                              anchor='w',
                                              font=("Arial", 11, "bold"),
                                              fill=self.title_color)

        self.msg_id = self.canvas.create_text(0, 17.5,
                                            text=self.message_text,
                                            anchor='w',
                                            font=("Arial", 11),
                                            fill='white')

        # Initialisation positions
        self.set_initial_positions()
        self.after(1500, self.start_scroll_delayed)  # Attente de 1.5s avant défilement

    def set_initial_positions(self):
        # Calcul des dimensions
        title_bbox = self.canvas.bbox(self.title_id)
        msg_bbox = self.canvas.bbox(self.msg_id)

        self.title_width = title_bbox[2] - title_bbox[0]
        self.msg_width = msg_bbox[2] - msg_bbox[0]
        self.total_width = self.title_width + self.msg_width + 10

        # Détermine si le défilement est nécessaire
        self.need_scroll = self.total_width > (self.alert_width - 20)

        # Si le texte tient sur un seul écran, on passe duree_base à 0
        if not self.need_scroll:
            self.duree_base = 0  # Pas de délai si le texte tient sur un écran

        if self.need_scroll:
            self.initial_x = 0  # Début à gauche de la fenêtre
        else:
            self.initial_x = (self.alert_width - self.total_width) // 2

        # Positionnement initial
        self.canvas.coords(self.title_id, self.initial_x, 17.5)
        self.canvas.coords(self.msg_id, self.initial_x + self.title_width + 10, 17.5)

    def start_scroll_delayed(self):
        if self.need_scroll:
            self.start_scroll()
        else:
            # Si duree_base est 0, on passe directement à l'animation de sortie
            self.after(self.duree_base, self.animate_exit)

    def start_scroll(self):
        current_x = self.canvas.coords(self.title_id)[0]
        new_x = current_x - self.scroll_speed

        # Met à jour les positions
        self.canvas.coords(self.title_id, new_x, 17.5)
        self.canvas.coords(self.msg_id, new_x + self.title_width + 10, 17.5)

        # Déclenche le timer quand le texte est entièrement visible
        if not self.has_scrolled:
            text_end = new_x + self.total_width
            if text_end <= self.alert_width - 10:  # 10px de marge droite
                self.has_scrolled = True
                self.after(self.duree_base, self.animate_exit)

        # Continue le défilement
        if new_x + self.total_width > 0:
            self.animation_id = self.after(self.frame_delay, self.start_scroll)
        else:
            self.reset_position()

    def reset_position(self):
        self.canvas.coords(self.title_id, self.alert_width, 20)
        self.canvas.coords(self.msg_id, self.alert_width + self.title_width + 10, 20)
        self.start_scroll()

    def elastic_ease_out(self, t):
        return math.sin(-13 * (t + 1) * math.pi/2) * math.pow(2, -10 * t * 1.5) + 1

    def animate_entrance(self, start_y, target_y):
        total_steps = 25
        t = 0

        def move():
            nonlocal t
            current_y = start_y - (start_y - target_y) * self.elastic_ease_out(t)
            alpha = min(0.85, t * 2)

            self.geometry(f"+{self.winfo_x()}+{int(current_y)}")
            self.attributes('-alpha', alpha)

            if t < 1:
                t += 1 / total_steps
                self.after(10, move)
            else:
                self.attributes('-alpha', 0.85)

        move()

    def animate_exit(self, step=0):
        if self.animation_id:
            self.after_cancel(self.animation_id)

        total_steps = 15
        current_y = self.winfo_y() - 8
        alpha = 0.85 - (0.85 * (step / total_steps))

        self.geometry(f"+{self.winfo_x()}+{int(current_y)}")
        self.attributes('-alpha', max(0, alpha))

        if step < total_steps:
            self.after(30, lambda: self.animate_exit(step + 1))
        else:
            self.destroy()

class Jeu:
    def __init__(self, root):
        self.root = root
        self.root.title(game_title)
        self.root.geometry("800x600")
        self.root.minsize(850, 650)
        self.root.configure(bg='#2c3e50')

        self.image_references = []
        self.money_sound = None  # Initialisation explicite
        self.change_sound = None

        self.reseau = reseau()
        root.bind("<<NetworkEvent>>", lambda e: self.update_reseau_ui())

        self.setup_splash_screen()
        self.root.after(100, self.init_setup)

        self.trading_history = [trading_tot]
        self.max_visible_points = 30
        self.update_interval = 2000

        self.check_network_events()

    def check_network_events(self):
        if self.reseau.event_queue:
            event_name = self.reseau.event_queue.pop(0)
            self.root.after(0, lambda: self.trigger_jose_event(event_name))
        self.root.after(1000, self.check_network_events)

    def silent_initialization(self):
        """Utilise l'œuvre la moins chère pour initialiser les composants"""
        global money_tot, oeuvre, mes_oeuvres, firstrun
        if firstrun == False:
            return
    
        firstrun = False

        try:
            nom_oeuvre, details = next(iter(oeuvres.items()))
            prix = details["prix"]
            # Vérifier si l'œuvre existe toujours
        
            self.show_alert("Info", "Heureux de vous voir parmi nous !")
            print("initialisation terminée")

        except Exception as e:
            print(f"Initialisation silencieuse échouée: {str(e)}")
        
    def update_phone_display(self, event):
        if hasattr(self, 'phone_frame'):
            last_msg = self.reseau.message_history[-1]
            self.phone_frame.add_message(last_msg[1], is_jose=(last_msg[0] == 'jose'))

    def on_resize(self, event):
        """Met à jour les dimensions des éléments en fonction de la nouvelle taille de la fenêtre."""
        new_width = event.width
        new_height = event.height

        # Mettre à jour les dimensions du cadre de contenu
        self.content_frame.config(width=new_width * 0.9, height=new_height * 0.75)

        # Mettre à jour d'autres éléments ici si nécessaire
        # Par exemple, redimensionner les images ou ajuster les positions des widgets

    def show_alert(self, title, message, is_error=False, duree_anim=1500):
        if self.root.winfo_exists():
            CustomAlert(self.root, title, message, is_error, duree_anim)

    def setup_splash_screen(self):
        """Affiche un écran de chargement pendant l'installation des modules"""
        self.splash_frame = tk.Frame(self.root, bg='#34495e')
        self.splash_frame.place(x=0, y=0, relwidth=1, relheight=1)

        tk.Label(self.splash_frame, text=game_title, font=("Arial", 20, "bold"), fg='white', bg='#34495e').pack(pady=20)
        tk.Label(self.splash_frame, text=f"Développé par : {', '.join(devs)}", font=("Arial", 12), fg='white', bg='#34495e').pack()
        tk.Label(self.splash_frame, text=f"Musique par : {compositeur}", font=("Arial", 12), fg='white', bg='#34495e').pack()

        self.loading_label = tk.Label(self.splash_frame, text="Vérification des modules...", font=("Arial", 12), fg='white', bg='#34495e')
        self.loading_label.pack()

    def init_setup(self):
        """Lance l'installation des modules en arrière-plan"""
        threading.Thread(target=self.install_and_load_ui, daemon=True).start()

    def install_and_load_ui(self):
        """Processus d'installation et chargement de l'UI principale"""
        try:
            # Vérifier et installer les modules
            check_and_install_modules()

            # Importer les modules après installation
            global pygame, plt, FigureCanvasTkAgg, Image, ImageTk
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import matplotlib.pyplot as plt
            from PIL import Image, ImageTk
            import pygame

            # Charger l'UI principale dans le thread principal
            self.root.after(0, self.load_main_ui)

        except Exception as e:
            # Afficher une erreur si l'installation échoue
            self.root.after(0, self.show_error, str(e))

    def load_main_ui(self):
        """Charge l'interface principale après l'installation des modules"""
        # Nettoyer l'écran de chargement
        self.splash_frame.destroy()

        # Initialiser les composants UI
        self.load_background_image()
        self.init_sounds()
        self.play_background_music()

        # Créer la couche de superposition
        self.overlay = tk.Frame(self.root, bg='#2c3e50')
        self.overlay.place(x=0, y=0, relwidth=1, relheight=1)

        # Configurer l'interface utilisateur
        self.setup_ui()
        self.check_afk_gains()
        self.update_ui()

    def show_error(self, error_msg):
        """Affiche une erreur critique"""
        self.splash_frame.destroy()
        tk.Label(self.root, text="Erreur critique", font=("Arial", 24), fg='red').pack()
        tk.Label(self.root, text=error_msg, wraplength=400).pack()

    def init_sounds(self):
        """Initialisation des sons après chargement de pygame"""
        pygame.mixer.init()
        self.money_sound = pygame.mixer.Sound("sounds/money.mp3")
        self.change_sound = pygame.mixer.Sound("sounds/change.mp3")
        self.money_sound.set_volume(0.5)
        self.change_sound.set_volume(0.5)

    def play_background_music(self):
        """Joue la bande sonore"""
        pygame.mixer.music.load("sounds/ChillGuy.mp3")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

    @staticmethod
    def stop_background_music():
        """Arrête la bande sonore"""
        pygame.mixer.music.stop()
        pygame.mixer.quit()

    def load_background_image(self):
        """Charge l'image de fond avec une gestion d'erreur robuste"""
        try:
            image_path = "../Data/images/museum_bg.jpg"
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Le fichier '{image_path}' n'existe pas.")

            img = Image.open(image_path)
            img = img.resize((800, 600), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(img)

            self.bg_label = tk.Label(self.root, image=self.bg_image)
            self.bg_label.lower()
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

            print("Image de fond chargée avec succès.")

        except FileNotFoundError as e:
            print(f"Erreur : {e}")
            self.root.configure(bg='#2c3e50')

        except Exception as e:
            print(f"Erreur lors du chargement de l'image de fond : {e}")
            self.root.configure(bg='#2c3e50')

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setup_top_bar()
        self.setup_navigation()
        self.setup_content_frame()
        self.page_oeuvres()
        self.root.bind("<Configure>", self.on_resize)

    def setup_top_bar(self):
        """Configure la barre supérieure"""
        self.top_bar = tk.Frame(self.overlay, bg='#34495e', height=0.1)  # 10% de la hauteur de la fenêtre
        self.top_bar.pack(fill='x')

        # Section utilisateur
        self.user_frame = tk.Frame(self.top_bar, bg=self.top_bar['bg'])
        self.setup_user_interface()
        self.user_frame.pack(side='left', padx=20)

        # Affichage de l'argent
        self.money_label = tk.Label(self.top_bar,
                                  text=f"${money_tot:,.2f}",
                                  font=("Consolas", 14),
                                  fg='#2ecc71',
                                  bg='#34495e')
        self.money_label.pack(side='right', padx=20)

    def setup_user_interface(self):
        """Configure l'interface utilisateur"""
        try:
            image_path = "../Data/images/unnamed.png"
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Le fichier '{image_path}' n'existe pas.")

            img = Image.open(image_path)
            img = img.resize((30, 30), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)

        except:
            img_tk = "🎨"

        global username
        self.user_icon = tk.Label(self.user_frame,
                                image=img_tk,
                                bg=self.user_frame['bg'])
        self.user_icon.image = img_tk  # Garder une référence pour éviter la suppression par le garbage collector
        self.user_icon.pack(side='left')

        self.username_var = tk.StringVar(value=username)
        self.username_label = tk.Label(self.user_frame,
                                    textvariable=self.username_var,
                                    font=("Arial", 12, "bold"),
                                    fg='#ecf0f1',
                                    bg=self.user_frame['bg'],
                                    cursor="hand2")
        self.username_label.pack(side='left', padx=10)
        self.username_label.bind("<Button-1>", self.edit_username)

    def setup_navigation(self):
        """Configure la barre de navigation"""
        self.nav_frame = tk.Frame(self.overlay, bg='#34495e', height=0.01)  # 1% de la hauteur de la fenêtre
        self.nav_frame.pack(fill='x')

        nav_items = [
            ("🖼️ Collection", self.page_oeuvres),
            ("🏛️ Musée", self.page_musee),
            ("📈 Trading", self.page_trading),
            ("🌐 Réseau", self.page_reseau)
        ]

        for col, (text, cmd) in enumerate(nav_items):
            btn = tk.Button(self.nav_frame,
                          text=text,
                          command=cmd,
                          font=("Arial", 11),
                          bg='#3498db',
                          fg='white',
                          activebackground='#2980b9',
                          borderwidth=0,
                          width=15)
            btn.grid(row=0, column=col, padx=5, pady=5, sticky='ew')
            self.nav_frame.grid_columnconfigure(col, weight=1)

    def setup_content_frame(self):
        """Configure le cadre principal du contenu"""
        self.content_frame = tk.Frame(self.overlay,
                                    bg='#ffffff',
                                    bd=2,
                                    relief='groove')
        self.content_frame.place(relx=0.02, rely=0.15, relwidth=0.96, relheight=0.83)  # 2% de marge à gauche, 10% en haut, 96% de largeur, 83% de hauteur

    def edit_username(self, event):
        """Permet à l'utilisateur de modifier son pseudo"""
        self.username_entry = tk.Entry(self.user_frame,
                                     font=("Arial", 12),
                                     bd=0,
                                     justify='center')
        self.username_entry.insert(0, self.username_var.get())
        self.username_entry.pack(side='left')
        self.username_entry.focus_set()
        self.username_entry.bind("<Return>", self.save_username)
        self.username_entry.bind("<FocusOut>", self.save_username)
        self.username_label.pack_forget()

    def save_username(self, event):
        """Sauvegarde le nouveau pseudo"""
        global username
        new_name = self.username_entry.get().strip()
        if 3 <= len(new_name) <= 15:
            self.username_var.set(new_name)
            username = new_name
        else:
            self.show_alert("Nom invalide", "Le nom doit contenir entre 3 et 15 caractères", is_error=True)
        self.username_entry.destroy()
        self.username_label.pack(side='left', padx=10)
        return username

    def check_afk_gains(self):
        """Vérifie les gains AFK"""
        global time_afk, gains_afk
        if time_afk > 60:
            self.show_afk_popup(gains_afk)

    def show_afk_popup(self, gains):
        """Affiche la popup des gains AFK"""
        self.popup = tk.Toplevel(self.root)
        self.popup.title("Gains AFK")
        self.popup.geometry("300x180")
        self.popup.resizable(False, False)
        self.popup.configure(bg='#34495e')
        self.center_popup()

        self.popup.grab_set()

        # Contenu de la popup
        container = tk.Frame(self.popup, bg='#2c3e50', padx=20, pady=15)
        container.pack(fill='both', expand=True)

        tk.Label(container,
               text="⚡ Gains AFK ⚡",
               font=("Arial", 14, "bold"),
               fg='#2ecc71',
               bg='#2c3e50').pack(pady=5)

        tk.Label(container,
               text=f"🤑 + {gains:,} $",
               font=("Consolas", 16),
               fg='#f1c40f',
               bg='#2c3e50').pack(pady=10)

        tk.Label(container,
               text="Fermez cette fenêtre pour continuer",
               font=("Arial", 8),
               fg='#bdc3c7',
               bg='#2c3e50').pack(pady=5)

        self.animate_popup(0.1)

    def center_popup(self):
        """Centre la popup sur l'écran"""
        self.popup.update_idletasks()
        width = self.popup.winfo_width()
        height = self.popup.winfo_height()
        x = (self.popup.winfo_screenwidth() // 2) - (width // 2)
        y = (self.popup.winfo_screenheight() // 2) - (height // 2)
        self.popup.geometry(f'+{x}+{y}')

    def animate_popup(self, alpha):
        """Animation de la popup"""
        if alpha < 1.0:
            self.popup.attributes("-alpha", alpha)
            self.root.after(50, lambda: self.animate_popup(alpha + 0.1))
        else:
            self.popup.attributes("-alpha", 1.0)

    def normalize_filename(self, name):
        """Normalise les noms de fichiers pour les images"""
        return str.lower(unicodedata.normalize('NFKD', name)\
                        .encode('ASCII', 'ignore')\
                        .decode()\
                        .replace(' ', '_')\
                        .replace("'", '_')[:30]
                        .replace('?', ''))

    def clear_frame(self):
        """Vide TOTALEMENT le contenu précédent"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        # Annule toutes les mises à jour en attente

    def page_oeuvres(self):
        """Affiche la page des œuvres d'art."""
        global firstrun
        self.change_sound.play()
        self.clear_frame()

        # Configuration des couleurs
        BG_COLOR = '#f5f6fa'
        CARD_COLOR = 'white'
        PRIMARY_COLOR = '#3498db'
        SECONDARY_COLOR = '#2ecc71'

        # Conteneur principal sans barre de défilement
        main_canvas = tk.Canvas(self.content_frame, 
                                bg=BG_COLOR, 
                                highlightthickness=0,
                                width=self.content_frame.winfo_width(),
                                height=self.content_frame.winfo_height())

        main_frame = tk.Frame(main_canvas, bg=BG_COLOR)

        # Placement du canvas
        main_canvas.pack(side="left", fill="both", expand=True)
        main_canvas.create_window((0, 0), window=main_frame, anchor="nw", tags="frame")

        def on_canvas_configure(event):
            """Adapte la taille du frame interne au canvas."""
            main_canvas.itemconfig("frame", width=event.width)
            main_canvas.yview_moveto(0)
            
        main_canvas.bind("<Configure>", on_canvas_configure)

        # ================= PARTIE SUPÉRIEURE =================
        top_frame = tk.Frame(main_frame, bg=BG_COLOR)
        top_frame.pack(fill="x", pady=10, padx=10)

        # Module d'achat
        purchase_frame = tk.Frame(top_frame, bg=CARD_COLOR, padx=10, pady=10, relief="groove")
        purchase_frame.pack(fill="both", expand=True)

        if oeuvres:
            cheapest = min(oeuvres.items(), key=lambda x: x[1]['prix'])
            name, details = cheapest

            # Image à gauche
            img_frame = tk.Frame(purchase_frame, bg=CARD_COLOR)
            img_frame.pack(side="left", fill="y")

            try:
                original_img = Image.open(f"""../Data/images/{self.normalize_filename(name)}.jpg""")
                aspect_ratio = original_img.width / original_img.height
                new_height = 150
                new_width = int(aspect_ratio * new_height)
                img = original_img.resize((new_width, new_height), Image.LANCZOS)
                self.tk_img = ImageTk.PhotoImage(img)
                tk.Label(img_frame, image=self.tk_img, bg=CARD_COLOR).pack()
            except Exception as e:
                tk.Label(img_frame, text="🖼️", font=("Arial", 48), bg=CARD_COLOR).pack()
                print(f"Erreur lors du chargement de l'image pour {name}: {str(e)}")

            # Détails à droite
            details_frame = tk.Frame(purchase_frame, bg=CARD_COLOR)
            details_frame.pack(side="right", fill="both", expand=True)

            tk.Label(details_frame, 
                      text=name,
                      font=("Arial", 12, "bold"),
                      bg=CARD_COLOR).pack(anchor="w")

            desc_text = details['description'][:100] + '...' if len(details['description']) > 100 else details['description']
            tk.Label(details_frame,
                     text=desc_text,
                     wraplength=300,
                     justify="left",
                     bg=CARD_COLOR).pack(anchor="w")

            price_frame = tk.Frame(details_frame, bg=CARD_COLOR)
            price_frame.pack(anchor="w", pady=5)

            tk.Label(price_frame,
                     text=f"Prix: ${details['prix']:,.2f}",
                     font=("Arial", 12, "bold"),
                     fg=SECONDARY_COLOR,
                     bg=CARD_COLOR).pack(side="left")

            btn_frame = tk.Frame(price_frame, bg=CARD_COLOR)
            btn_frame.pack(side="right")

            tk.Button(btn_frame,
                      text="Acheter",
                      command=lambda: self.acheter_oeuvre(name, details['prix']),
                      bg=SECONDARY_COLOR,
                      fg="white").pack(side="left", padx=2)

        # ================= PARTIE INFÉRIEURE =================
        bottom_frame = tk.Frame(main_frame, bg=BG_COLOR)
        bottom_frame.pack(fill="both", expand=True, pady=10, padx=10)

        # En-tête collection
        header_frame = tk.Frame(bottom_frame, bg=BG_COLOR)
        header_frame.pack(fill="x")

        tk.Label(header_frame,
                 text="VOTRE COLLECTION",
                 font=("Arial", 14, "bold"),
                 bg=BG_COLOR).pack(side="left")

        tk.Label(header_frame,
                 text=f"Total: {len(mes_oeuvres)} œuvres",
                 font=("Arial", 12),
                 bg=BG_COLOR).pack(side="right")

        # Liste des œuvres avec scrollbar
        list_canvas = tk.Canvas(bottom_frame, bg=BG_COLOR, highlightthickness=0)
        list_vsb = tk.Scrollbar(bottom_frame, orient="vertical", command=list_canvas.yview)
        list_content = tk.Frame(list_canvas, bg=BG_COLOR)

        list_canvas.configure(yscrollcommand=list_vsb.set)
        list_vsb.pack(side="right", fill="y")
        list_canvas.pack(side="left", fill="both", expand=True)
        list_canvas.create_window((0, 0), window=list_content, anchor="nw")

        # Remplissage de la liste
        for idx, (name, details) in enumerate(mes_oeuvres.items()):
            item_frame = tk.Frame(list_content,
                                  bg=CARD_COLOR,
                                  padx=10,
                                  pady=10,
                                  relief="groove")
            item_frame.grid(row=idx, column=0, sticky="nsew", pady=2)
            item_frame.columnconfigure(0, weight=1)

            # Colonne image
            try:
                filename = self.normalize_filename(name) + ".jpg"
                img_path = os.path.join("../Data/images", filename)
                
                if os.path.exists(img_path):
                    img = Image.open(img_path)
                    img = img.resize((120, 90), Image.Resampling.LANCZOS)
                    tk_img = ImageTk.PhotoImage(img)
                    self.image_references.append(tk_img)  # <-- Conserver la référence
                    img_label = tk.Label(item_frame, image=tk_img, bg=CARD_COLOR)
                else:
                    raise FileNotFoundError(f"Image non trouvée: {img_path}")
                
            except Exception as e:
                img_label = tk.Label(item_frame, 
                                     text="🖼️", 
                                     font=("Arial", 24), 
                                     bg=CARD_COLOR)
                print(f"Erreur chargement image {name}: {str(e)}")
            
            img_label.grid(row=0, column=0, rowspan=3, padx=10)

            # Colonne informations
            info_frame = tk.Frame(item_frame, bg=CARD_COLOR)
            info_frame.grid(row=0, column=1, sticky="w")

            tk.Label(info_frame, 
                     text=name,
                     font=("Arial", 12, "bold"),
                     bg=CARD_COLOR).pack(anchor="w")

            tk.Label(info_frame,
                     text=f"Artiste: {details['artiste']}",
                     font=("Arial", 10),
                     fg="#666",
                     bg=CARD_COLOR).pack(anchor="w")

            tk.Label(info_frame,
                     text=f"Valeur: ${details['prix']:,.2f}",
                     font=("Arial", 10),
                     fg=SECONDARY_COLOR,
                     bg=CARD_COLOR).pack(anchor="w")

            # Colonne actions
            action_frame = tk.Frame(item_frame, bg=CARD_COLOR)
            action_frame.grid(row=0, column=2, sticky="e")

            tk.Button(action_frame,
                      text="Exposer",
                      command=lambda n=name: self.placer_au_musee(n),
                      bg=PRIMARY_COLOR,
                      fg="white",
                      width=12).pack(pady=2)

            tk.Button(action_frame,
                      text="Vendre",
                      command=lambda n=name: self.open_sell_window(n),
                      bg="#e74c3c",
                      fg="white",
                      width=12).pack(pady=2)

        # Configuration responsive
        list_content.update_idletasks()
        list_canvas.config(scrollregion=list_canvas.bbox("all"))

        if firstrun == True:
            # Chargement complet de l'UI avant initialisation
            self.root.after(500, self.silent_initialization)


    def acheter_oeuvre(self, nom_oeuvre, prix, silent=True):
        """Gère l'achat direct d'une œuvre"""
        global money_tot, oeuvres, mes_oeuvres

        if not silent:
            if self.money_sound:
                self.money_sound.play()

        nom_oeuvre, details = next(iter(oeuvres.items()))
        prix = details["prix"]
        try:
            # Vérifier si l'œuvre existe toujours
            if nom_oeuvre not in oeuvres:
                self.show_alert("Erreur", "Cette œuvre n'est plus disponible", is_error=True)
                return

            # Vérifier les fonds
            if money_tot < prix:
                self.show_alert("Erreur", "Fonds insuffisants !", is_error=True)
                return

            # Effectuer l'achat
            money_tot -= prix
            mes_oeuvres[nom_oeuvre] = oeuvres.pop(nom_oeuvre)

            # Feedback visuel et sonore
            self.show_alert("Achat réussi", f"{nom_oeuvre} ajoutée à votre collection !")
            self.update_ui()

            self.page_oeuvres()
            return oeuvres, mes_oeuvres

        except Exception as e:
            self.show_alert("Erreur", f"Échec de l'achat : {str(e)}", is_error=True)

    def open_sell_window(self, oeuvre_name):
        if oeuvre_name not in mes_oeuvres:
            self.show_alert("Erreur", "Cette œuvre n'est plus disponible", is_error=True)
            return

        sell_win = tk.Toplevel(self.root)
        sell_win.title("Vendre l'œuvre")

        current_price = mes_oeuvres[oeuvre_name]['prix']

        # Widgets pour la négociation
        tk.Label(sell_win, text=f"Prix actuel : ${current_price:,.2f}").pack(pady=5)

        price_var = tk.DoubleVar(value=current_price)
        tk.Entry(sell_win,
                textvariable=price_var,
                font=("Arial", 14),
                justify='center').pack(pady=10)

        tk.Button(sell_win,
                text="Proposer prix",
                command=lambda: self.proposer_prix_vente(oeuvre_name, price_var.get()),
                bg='#27ae60',
                fg='white').pack(pady=10)

    def proposer_prix_vente(self, oeuvre_name, prix_propose):
        global money_tot
        try:
            if oeuvre_name not in mes_oeuvres:
                self.show_alert("Erreur", "Œuvre introuvable", is_error=True)
                return

            prix_actuel = mes_oeuvres[oeuvre_name]['prix']
            if prix_propose >= prix_actuel * 0.8 and prix_propose <= prix_actuel * 1.5:  # Accepte à partir de 80% du prix
                money_tot += prix_propose
                del mes_oeuvres[oeuvre_name]
                self.show_alert("Vente réussie", f"Vendu à {prix_propose:,.2f}$ !")
                self.page_oeuvres()  # Rafraîchir
            else:
                self.show_alert("Refusé", "Offre non acceptable", is_error=True)
        except Exception as e:
            self.show_alert("Erreur", str(e), is_error=True)

    def handle_negotiation(self, buyer_type, oeuvre_name):
        try:
            if oeuvre_name not in oeuvres:
                self.show_alert("Erreur", "Œuvre non disponible", is_error=True)
                return

            original_price = oeuvres[oeuvre_name]['prix']
            offered_price, success = mes_oeuvres_instance.negocier_prix(oeuvre_name, buyer_type)

            if success:
                response = f"Offre acceptée ! {offered_price:,.2f}$"
                mes_oeuvres_instance.achat(oeuvre_name)
                self.show_alert("Succès", response)
                self.update_ui()
            else:
                response = f"Offre refusée. Le vendeur demande {original_price:,.2f}$"
                self.show_alert("Échec", response, is_error=True)
        except KeyError as e:
            self.show_alert("Erreur", f"Œuvre introuvable : {str(e)}", is_error=True)

    def initier_vente(self, oeuvre_name):
        global money_tot
        price = mes_oeuvres[oeuvre_name]['prix']
        offered_price = price * random.uniform(0.9, 1.5)
        success = random.random() < 0.4  # 40% de chance de succès

        if success:
            del mes_oeuvres[oeuvre_name]
            money_tot += offered_price
            self.show_alert("Vente réussie", f"Vendu pour {offered_price:,.2f}$ !")
        else:
            self.show_alert("Vente échouée", "Aucun acheteur intéressé", is_error=True)

        self.update_ui()

    def placer_au_musee(self, oeuvre_name):
        global musee, musee_lvl
        try:
            if len(musee) < musee_lvl * 2:
                mesoeuvres.place_musee(oeuvre_name)
                self.show_alert("Exposition", f"{oeuvre_name} exposé au musée !")
                self.update_ui()
                self.page_oeuvres()
            else:
                self.show_alert("Exposition", "Plus de place au musée pour afficher cette oeuvre", is_error=True)

        except Exception as e:
            self.show_alert("Erreur", str(e), is_error=True)

    def page_musee(self):
        """Affiche la section Mon Musée selon le design fourni"""
        global visiteurs, musee_lvl, concordance_musee_lvl_prix_amelioration
        self.change_sound.play()
        self.clear_frame()

        # Configuration des couleurs
        bg_color = '#f5f6fa'
        card_color = 'white'
        primary_color = '#3498db'

        # Frame principal
        main_frame = tk.Frame(self.content_frame, bg=bg_color)
        main_frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)  # 5% de marge, 90% de largeur et hauteur

        # Section des œuvres du musée
        oeuvres_frame = tk.Frame(main_frame, bg=bg_color)
        oeuvres_frame.place(relx=0.05, rely=0.05, relwidth=0.6, relheight=0.9)  # 60% de la largeur

        # Titre
        tk.Label(oeuvres_frame,
                text="MON MUSÉE",
                font=("Arial", 14, "bold"),
                bg=bg_color).pack(pady=5)

        # Liste des œuvres avec années
        for idx, (name, details) in enumerate(musee.items()):
            item_frame = tk.Frame(oeuvres_frame,
                                bg=card_color,
                                padx=10,
                                pady=5,
                                relief='groove')
            item_frame.pack(fill='x', pady=2)

            # Année et nom
            tk.Label(item_frame,
                    text=f"{details.get('année', 'N/A')} | {name}",
                    font=("Arial", 10),
                    bg=card_color).pack(side='left')

            # Bouton de retrait
            tk.Button(item_frame,
                    text="Retirer",
                    command=lambda n=name: self.retirer_oeuvre(n),
                    bg=primary_color,
                    fg='white').pack(side='right')

        # Section de gestion à droite
        gestion_frame = tk.Frame(main_frame, bg=bg_color, padx=10)
        gestion_frame.place(relx=0.7, rely=0.05, relwidth=0.25, relheight=0.9)  # 25% de la largeur

        # Revenus
        revenus_frame = tk.Frame(gestion_frame, bg=card_color, padx=10, pady=10)
        revenus_frame.pack(pady=10)

        tk.Label(revenus_frame,
                text="Revenus",
                font=("Arial", 12, "bold"),
                bg=card_color).pack()

        # Calcul des revenus
        musee_gains = 0
        for oeuvre in musee:
            musee_gains += musee[oeuvre]['prix'] * 0.0005

        tk.Label(revenus_frame,
                text=f"Revenus musee : ${round((10 * math.sqrt(musee_gains * (1.5 ** musee_employes)) * 10), 2):.2f}/s",
                bg=card_color).pack()

        self.visiteurs_label = tk.Label(revenus_frame,
                text=f"Visiteurs : {visiteurs} dans le musée",
                bg=card_color)
        self.visiteurs_label.pack()

        """gestion_frame = tk.Frame(main_frame, bg=bg_color, padx=10)
        gestion_frame.place(relx=0.7, rely=0.05, relwidth=0.25, relheight=0.9)"""

        try:
            # Bouton d'agrandissement
            tk.Button(gestion_frame,
                    text="Agrandir le Musée\n(${})".format(concordance_musee_lvl_prix_amelioration[musee_lvl + 1]),
                    command=self.agrandir_musee,
                    bg='#2ecc71',
                    fg='white').pack(pady=10, fill='x')

            # Bouton d'embauche
            tk.Button(gestion_frame,
                    text="Embaucher employé\n(50$/employé)",
                    command=self.embaucher_employe,
                    bg='#3498db',
                    fg='white').pack(pady=10, fill='x')

            # Afficher le nombre d'employés
            tk.Label(gestion_frame,
                text=f"Employés actuels: {musee_employes}",
                bg=bg_color).pack(pady=5)
        
        except:
            # Bouton d'agrandissement
            tk.Button(gestion_frame,
                    text="LVL MAX",
                    bg='#2ecc71',
                    fg='white').pack(pady=10, fill='x')

            # Bouton d'embauche
            tk.Button(gestion_frame,
                    text="Embaucher employé\n(50$/employé)",
                    command=self.embaucher_employe,
                    bg='#3498db',
                    fg='white').pack(pady=10, fill='x')

            # Afficher le nombre d'employés
            tk.Label(gestion_frame,
                text=f"Employés actuels: {musee_employes}",
                bg=bg_color).pack(pady=5)

    def agrandir_musee(self):
        result = monmusee.agrandir_musee()
        if isinstance(result, str):
            self.show_alert("Erreur", result, is_error=True)
        else:
            self.money_sound.play()
            self.show_alert("Succès", "Musée agrandi !")
            self.page_musee()

    def embaucher_employe(self):
        result = monmusee.embaucher_employe()
        if isinstance(result, str):
            self.show_alert("Erreur", result, is_error=True)
        else:
            self.money_sound.play()
            self.show_alert("Succès", "Employé embauché !")
            self.page_musee()

    def retirer_oeuvre(self, nom_oeuvre):
        """Retire une œuvre du musée"""
        try:
            monmusee.retire_musee(nom_oeuvre)
            self.show_alert("Succès", f"{nom_oeuvre} retirée du musée !")
            self.page_musee()  # Rafraîchir la page
        except Exception as e:
            self.show_alert("Erreur", str(e), is_error=True)

    def page_trading(self):
        """Affiche la section Algo Trading avec graphique et contrôles"""
        self.change_sound.play()
        self.clear_frame()

        # Configuration du layout
        main_frame = tk.Frame(self.content_frame, bg='#ecf0f1')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Frame pour le graphique
        graph_frame = tk.Frame(main_frame, bg='white')
        graph_frame.pack(fill='both', expand=True, side='top')

        # Fermer l'ancienne figure si elle existe
        if hasattr(self, 'fig'):
            plt.close(self.fig)

        # Initialisation du graphique (plus d'erreur ici)
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.line, = self.ax.plot([], [], 'b-')
        self.ax.set_facecolor('#f5f6fa')
        self.fig.patch.set_facecolor('#ecf0f1')
        self.ax.set_xlabel('Temps')
        self.ax.set_ylabel('Valeur')
        self.ax.set_title('Évolution du Trading en Temps Réel')
        self.ax.grid(True)

        # Intégration dans Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # Contrôles de trading
        control_frame = tk.Frame(main_frame, bg='#ecf0f1')
        control_frame.pack(fill='x', pady=10)

        # Boutons et entrées
        self.setup_trading_controls(control_frame)

        # Démarrer la mise à jour du graphique
        self.update_graph()

    def setup_trading_controls(self, parent):
        """Configure les contrôles de trading"""
        # Mode de trading
        mode_frame = tk.Frame(parent, bg='#ecf0f1')
        mode_frame.pack(side='left', padx=10)

        tk.Label(mode_frame, text="Mode de Risque:", bg='#ecf0f1').pack()
        self.mode_var = tk.StringVar(value=trading_mode)
        mode_menu = tk.OptionMenu(mode_frame, self.mode_var, *modes_dispo.keys(),
                                command=self.change_trading_mode)
        mode_menu.config(bg='#3498db', fg='white')
        mode_menu.pack()

        # Dépôt/Retrait
        money_frame = tk.Frame(parent, bg='#ecf0f1')
        money_frame.pack(side='left', padx=10)

        tk.Label(money_frame, text="Montant ($):", bg='#ecf0f1').grid(row=0, column=0)
        self.amount_entry = tk.Entry(money_frame, width=10)
        self.amount_entry.grid(row=0, column=1, padx=5)

        tk.Button(money_frame, text="Déposer", command=self.deposit,
                bg='#2ecc71', fg='white').grid(row=1, column=0, pady=5)
        tk.Button(money_frame, text="Retirer", command=self.withdraw,
                bg='#e74c3c', fg='white').grid(row=1, column=1, pady=5)

        # Traders
        trader_frame = tk.Frame(parent, bg='#ecf0f1')
        trader_frame.pack(side='left', padx=10)

        levels = [
            ('Trader N1 (1000$)', 1, '#1abc9c'),
            ('Trader N2 (100k$)', 2, '#f1c40f'),
            ('Trader N3 (10M$)', 3, '#e67e22')
        ]

        for text, trader_name, color in levels:
            btn = tk.Button(trader_frame, text=text, command=lambda tn=trader_name: self.embaucher_trader(tn),
                        bg=color, fg='white')
            btn.pack(pady=2, fill='x')

    def embaucher_trader(self, trader_name):
        """Gestionnaire d'événements pour embaucher un trader."""
        try:
            if trader_name == 1:
                result = algo_trade_instance.traders1()
            elif trader_name == 2:
                result = algo_trade_instance.traders2()
            elif trader_name == 3:
                result = algo_trade_instance.traders3()
            else:
                result = "Trader inconnu"

            if isinstance(result, str) and ("pas assez d'argent" in result or "embauché 20 traders" in result):
                self.show_alert("Erreur", result, is_error=True)
            else:
                self.money_sound.play()  # Jouer le son après avoir embauché le trader
                self.show_alert("Succès", f"Trader niveau {trader_name} embauché !")
        except Exception as e:
            self.show_alert("Erreur", f"Erreur lors de l'embauche du trader : {e}", is_error=True)

    def update_graph(self):
        """Met à jour le graphique avec les dernières données."""
        if not running or not self.root.winfo_exists():
            print("Fenêtre fermée ou mise à jour arrêtée.")
            return

        try:
            # Ajouter la dernière valeur
            self.trading_history.append(trading_tot)

            # Limiter le nombre de points visibles
            if len(self.trading_history) > self.max_visible_points:
                self.trading_history.pop(0)

            # Adapter l'échelle
            y_min = min(self.trading_history)
            y_max = max(self.trading_history)
            self.ax.set_ylim(0 if y_min > 0 else y_min * 1.1,
                            y_max * 1.1 if y_max != 0 else 1)

            # Mettre à jour les données
            x_data = list(range(len(self.trading_history)))
            self.line.set_data(x_data, self.trading_history)
            self.ax.relim()
            self.ax.autoscale_view(scalex=True, scaley=False)
            self.canvas.draw_idle()

            # Planifier la prochaine mise à jour si la fenêtre existe toujours
            if self.root.winfo_exists():
                self.update_id = self.root.after(self.update_interval, self.update_graph)
        except Exception as e:
            print(f"Erreur lors de la mise à jour du graphique : {e}")

    def change_trading_mode(self, mode):
        """Change le mode de trading"""
        global trading_mode
        trading_mode = mode
        self.show_alert("Mode changé", f"Mode de trading: {mode}")

    def deposit(self):
        """Dépose de l'argent dans le trading"""
        try:
            amount = float(self.amount_entry.get())
            if amount <= money_tot and amount > 0:
                algo_trade_instance.deposer(amount)
                self.money_sound.play()
                self.show_alert("Succès", f"Dépôt de {amount}$ effectué!")
            else:
                self.show_alert("Erreur", "Montant invalide", is_error=True)
        except ValueError:
            self.show_alert("Erreur", "Veuillez entrer un nombre valide", is_error=True)

    def withdraw(self):
        """Retire de l'argent du trading"""
        try:
            amount = float(self.amount_entry.get())
            if amount <= trading_tot and amount > 0:
                algo_trade_instance.recup(amount)
                self.money_sound.play()
                self.show_alert("Succès", f"Retrait de {amount}$ effectué!")
            else:
                self.show_alert("Erreur", "Montant invalide", is_error=True)
        except ValueError:
            self.show_alert("Erreur", "Veuillez entrer un nombre valide", is_error=True)

    def page_reseau(self):
        self.change_sound.play()
        self.clear_frame()
        
        # Vérifier si le réseau est débloqué
        if not menu.unlock_reseau(musee_lvl):  # Ajout d'une vérification dynamique
            locked_frame = tk.Frame(self.content_frame, bg="#1a1a1a")
            # ... (message de verrouillage)
            return
        
        # Réinitialiser complètement l'interface
        self.phone_frame = PhoneFrame(self.content_frame, self)
        self.phone_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Charger les messages même après changement de page
        self.reseau.load_conversation()  # Recharger les messages à chaque accès
        for msg, is_jose in self.reseau.message_history:
            self.phone_frame.add_message(msg, is_jose)
        
        # Vérifier les événements en attente
        if self.reseau.active_jose_event:
            self.trigger_jose_event(self.reseau.active_jose_event)

    def trigger_jose_event(self, event_name):
        print("Tentative de déclenchement de l'événement:", event_name)
        if event_name in self.reseau.jose_events:
            event = self.reseau.jose_events[event_name]
            self.reseau.active_jose_event = event_name
            
            # Utiliser 'description' si 'message' n'existe pas
            message_content = event.get("message", event.get("description", "Message d'erreur"))
            
            # Ajouter le message à l'historique
            self.reseau.message_history.append((message_content, True))
            
            # Mettre à jour l'interface si le phone_frame existe
            if hasattr(self, 'phone_frame') and self.phone_frame.winfo_exists():
                self.phone_frame.add_message(message_content, is_jose=True)
                
            # Vérifier la présence des choix
            if "choices" in event:
                choices = [choice["text"] for choice in event["choices"]]
                if hasattr(self, 'phone_frame') and self.phone_frame.winfo_exists():
                    self.phone_frame.show_responses(choices)
                else:
                    print("Avertissement: PhoneFrame non disponible pour afficher les choix")
            else:
                print(f"Avertissement: Pas de choix pour l'événement {event_name}")
                
            if event_name == "introduction":
                self.reseau.introduction_done = True
        else:
            print(f"Erreur: Événement '{event_name}' non trouvé")
            
    def trigger_jose_introduction(self):
        if not self.reseau.introduction_done:  # Utiliser l'attribut du reseau
            msg = "José: Salut... On m'a dit que tu savais garder des secrets.\n"\
                  "Le cartel a besoin d'un endroit discret. Intéressé par un partenariat ?"
            self.phone_frame.add_message(msg, is_jose=True)
            self.reseau.introduction_done = True
    
    def handle_response(self, response_idx):
        event_type = self.reseau.active_event
        response_map = {
            "introduction": {
                0: (self.accept_partnership, 0.3),
                1: (self.refuse_partnership, -0.5),
                2: (self.ask_more_info, -0.1)
            },
            "mission": {
                0: (self.accept_mission, 0.2),
                1: (self.decline_mission, -0.3),
                2: (self.postpone_mission, -0.05)
            }
        }
        
        if event_type in response_map:
            handler, confidence_change = response_map[event_type].get(response_idx, (self.default_handler, 0))
            handler()
            self.update_confidence(confidence_change)
            self.reseau.save_conversation()
    
    def accept_partnership(self):
        global confiance_cartel
        confiance_cartel = min(1.0, confiance_cartel + 0.3)
        self.phone_frame.add_message("Vous: D'accord, je suis partenaire.", False)
        self.phone_frame.add_message("José: Bon choix. On commence maintenant.", True)
        self.reseau.introduction_done = True
        self.reseau.active_event = None
        self.unlock_cartel_features()
    
    def refuse_partnership(self):
        global confiance_cartel
        confiance_cartel = max(0.0, confiance_cartel - 0.5)
        self.phone_frame.add_message("Vous: Jamais de la vie!", False)
        self.phone_frame.add_message("José: Tu regretteras ça...", True)
        self.reseau.active_event = None
    
    def ask_more_info(self):
        self.phone_frame.add_message("Vous: Expliquez-vous...", False)
        msg = "José: On fournit des œuvres rares, tu prends 20%.\n"\
              "En échange, on utilise ton musée pour certaines opérations."
        self.phone_frame.add_message(msg, True)
        self.phone_frame.show_responses([
            "Accepter le deal", 
            "Refuser le deal",
            "Temps de réflexion"
        ])
    
    def unlock_cartel_features(self):
        self.phone_frame.add_message("José: Voici ta première mission...", True)
        self.trigger_mission("convoi_special")
    
    def trigger_mission(self, mission_type):
        missions = {
            "convoi_special": {
                "message": "José: On a un convoi à stocker 48h. 20% de bonus si tu acceptes.",
                "reponses": [
                    "Accepter (+20% confiance)",
                    "Refuser (-15% confiance)",
                    "Négocier le pourcentage"
                ]
            }
        }
        
        mission = missions[mission_type]
        self.phone_frame.add_message(mission["message"], True)
        self.phone_frame.show_responses(mission["reponses"])
        self.reseau.active_event = "mission"
    
    def default_handler(self):
        self.phone_frame.add_message("José: Tu dois choisir une réponse!", True)

    def update_reseau_ui(self):
        if hasattr(self, 'events_listbox'):
            self.events_listbox.delete(0, tk.END)
            for event in self.reseau.get_active_events_descriptions():
                self.events_listbox.insert(tk.END, f"• {event}")

    def acheter_drogue(self):
        try:
            quantity = int(self.drogue_entry.get())
            if self.reseau.achat_drogue(quantity):
                self.show_alert("Succès", f"{quantity} unités achetées ! (+{2*quantity}% confiance cartel)")
                self.update_ui()
            else:
                self.show_alert("Erreur", "Fonds insuffisants !", is_error=True)
        except ValueError:
            self.show_alert("Erreur", "Quantité invalide", is_error=True)

    def negocier_police(self):
        if self.reseau.negocier_avec_police():
            self.show_alert("Succès", "Relations policières améliorées ! (+15% confiance)")
        else:
            self.show_alert("Info", "Négociation impossible (confiance police >50%)")
        self.update_ui()


    def update_ui(self):
        """Met à jour l'interface utilisateur."""
        global check, check1
        if not running or not self.root.winfo_exists():
            print("Fenêtre fermée ou mise à jour de l'UI arrêtée.")
            return

        """print(f"Visiteurs avant mise à jour : {visiteurs}")"""

        if money_tot == 0 and check == True:
            time.sleep(0.02)
            self.show_alert("Info", f"Vous devez vous endetter pour continuer à payer les salaires de vos traders et de vos employés. Au lieu de vous endetter, vous décidez de virer le surplus de traders/employés. Il vous reste {musee_employes} employés dans votre musée, {nb_traders_lvl1} traders low risk, {nb_traders_lvl2} traders medium risk et {nb_traders_lvl3} traders high risk.", is_error=True)
            check = False
        
        if money_tot == 1000000000000000 and check1 == True:
            self.show_alert("Info", "Désormais, le surplus de votre argent ne vous sert plus à rien. Vous décidez donc de distribuer vos gains à une association d'art.")
            check1 = False

        if money_tot > 0 and money_tot < 1000000000000000:
            check = True
            check1 = True

        self.money_label.config(text=f"${money_tot:,.2f}")

        # Mettez à jour le texte du label des visiteurs
        try:
            if hasattr(self, 'visiteurs_label') and self.visiteurs_label.winfo_exists():
                self.visiteurs_label.config(text=f"Visiteurs : {visiteurs} dans le musée")
        except Exception as e:
            print(f"Erreur lors de la mise à jour du label des visiteurs : {e}")

        # Planifier la prochaine mise à jour si la fenêtre existe toujours
        if self.root.winfo_exists() and running:
            self.update_ui_id = self.root.after(100, self.update_ui)

    def update_network(self):
        """Gère les événements réseau en temps réel"""
        global running
        while running:
            try:
                current_time = time.time()  # <-- CAPTURER LE TEMPS ACTUEL ICI
                
                if not reseau_state:
                    time.sleep(5)
    
                if random.random() < 0.3:
                    # Ne déclencher que les événements avec interface José
                    valid_events = [e for e in self.reseau.jose_events 
                                if "message" in self.reseau.jose_events[e]]
                    chosen_event = random.choice(valid_events)
                    self.reseau.add_event_to_queue(chosen_event)
                
                # Vérifier tous les événements
                for event_name, event_data in self.reseau.events.items():
                    try:
                        # Vérifier les conditions de déclenchement
                        conditions_met = True
                        for cond_key, cond_value in event_data.get('conditions', {}).items():
                            if cond_key == 'musee_lvl' and musee_lvl < cond_value:
                                conditions_met = False
                            elif cond_key == 'confiance_cartel_min' and confiance_cartel < cond_value:
                                conditions_met = False
                            elif cond_key == 'oeuvres_exposees' and len(musee) < cond_value:
                                conditions_met = False

                        if not conditions_met:
                            continue

                        # Calculer la probabilité ajustée
                        base_prob = event_data.get('probability', 0.0)
                        prob_multiplier = self.reseau.probability_multiplier
                        adjusted_prob = base_prob * prob_multiplier

                        # Déclencher l'événement aléatoirement
                        if random.random() < adjusted_prob:
                            triggered_event = self.reseau.trigger_event(event_name)
                            if triggered_event:
                                # Envoyer une alerte à l'UI
                                self.root.event_generate('<<NetworkEvent>>')
                                self.show_alert("Événement Réseau", triggered_event['description'])

                    except Exception as e:
                        print(f"Erreur traitement événement {event_name}: {str(e)}")

                # Mettre à jour les événements actifs
                self.reseau.update_events()

                # Vérifier les événements spéciaux
                self.check_special_events(current_time)

                self.reseau.check_random_events()
                """time.sleep(10)"""
                time.sleep(10 - (time.time() - current_time))  # Intervalle précis

            except Exception as main_error:
                print(f"Erreur majeure dans update_network: {str(main_error)}")
                time.sleep(30)

    def check_special_events(self, current_time):
        """Gère les événements permanents et à durée illimitée"""
        # Vérifier le partenariat cartel
        if 'partenariat_cartel' in self.reseau.active_events:
            event_data = self.reseau.events['partenariat_cartel']
            if not self.reseau.introduction_done:
                self.trigger_jose_introduction()
                self.reseau.introduction_done = True

        # Gérer les inspections policières
        if confiance_police < 0.2 and random.random() < 0.1:
            self.reseau.trigger_event('inspection_surprise')

    def stop_updates(self):
        """Arrête les mises à jour périodiques."""
        global running
        running = False
        print("Arrêt des mises à jour périodiques...")
        if hasattr(self, 'update_id') and self.update_id:
            try:
                self.root.after_cancel(self.update_id)
                self.update_id = None
                print("Tâche after annulée pour update_graph.")
            except Exception as e:
                print(f"Erreur lors de l'annulation de la tâche after pour update_graph 'r: {e}")

        if hasattr(self, 'update_ui_id') and self.update_ui_id:
            try:
                self.root.after_cancel(self.update_ui_id)
                self.update_ui_id = None
                print("Tâche after annulée pour update_ui.")
            except Exception as e:
                print(f"Erreur lors de l'annulation de la tâche after pour update_ui : {e}")

        # Fermer la figure matplotlib
        if hasattr(self, 'fig'):
            plt.close(self.fig)

        """# Tue le processus Python pour être sûr (méthode ultime si le béboguage n'est pas assez concluant)
        os._exit(0)  # À utiliser en dernier recours si le processus reste zombie"""

        """try:
            thread1.join()
            thread2.join()
            thread3.join()
            print("Threads arrêtés.")
        except Exception as e:
            print(f"Erreur lors de l'arrêt des threads : {e}")"""


def on_closing():
    ping_fin(app)
    global running
    running = False  # Arrête les boucles
    print("Fermeture de la fenêtre...")

    app.stop_updates()  # Annule les tâches after

    # Fermer les figures matplotlib
    if hasattr(app, 'fig'):
        plt.close(app.fig)
    plt.close('all')  # Fermer toutes les figures potentielles

    Jeu.stop_background_music()  # Arrêter la bande sonore

    root.destroy()  # Ferme la fenêtre

def handle_jose_event(self, event):
    if self.current_page == "reseau":
        latest_event = self.reseau.jose_events[-1]
        self.phone_interface.add_message(latest_event['message'], is_jose=True)
        self.phone_interface.show_responses(latest_event['responses'])

def show_phone_alert(self):
    if not self.phone_visible:
        self.bell()
        self.flash_window()
        self.show_alert("Nouveau message", "José vous a envoyé un message!")

def flash_window(self):
    for _ in range(3):
        self.root.attributes('-alpha', 0.8)
        time.sleep(0.1)
        self.root.attributes('-alpha', 1.0)

def handle_choice(self, event_name, response):
    event = self.jose_events[event_name]
    penalty = -0.05 if response == 2 else -0.1 if response == 1 else 0.1
    global confiance_cartel
    confiance_cartel = max(0, confiance_cartel + penalty)
    
    if penalty < 0:
        self.show_alert("José mécontent", "Le cartel note votre hésitation...")

def show_jose_intro(self):
    intro_text = """José: Écoute bien... Mon cartel a besoin de ton musée.
    En échange, tu pourras acheter des œuvres... spéciales."""
    choice = askyesno("Corruption", "Accepter de collaborer avec le cartel?")
    global confiance_cartel
    confiance_cartel = 0.5 if choice else 0.3
    self.jose_introduced = True

if __name__ == "__main__":
    root = tk.Tk()
    app = Jeu(root)
    
    # Démarrer les threads avec l'instance app
    thread1 = threading.Thread(target=update_money_tot)
    thread2 = threading.Thread(target=update_trading)
    thread3 = threading.Thread(target=ping, args=(app,))  # Passer l'instance
    thread4 = threading.Thread(target=update_visiteurs)
    
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    
    network_thread = threading.Thread(target=Jeu.update_network, args=(app,), daemon=True)
    network_thread.start()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
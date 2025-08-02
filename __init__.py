"""
MyLib - Libreria Universale AWS SSO

Libreria Python per la gestione di credenziali AWS SSO, operazioni S3, DynamoDB 
e utility comuni per i progetti ENEL.

Caratteristiche:
- Auto-configurazione AWS SSO con setup automatico
- Gestione dinamica file .env
- Auto-riparazione configurazioni non valide
- GUI per selezione manuale
- Ricaricamento configurazione in tempo reale
- Compatibilità come submodule Git

Versione: 2.0.0
Autore: Francesco Freiles
"""

import os

# Leggi la versione dal file VERSION
__version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
if os.path.exists(__version_file):
    with open(__version_file, 'r') as f:
        __version__ = f.read().strip()
else:
    __version__ = "2.0.0"

__author__ = "Francesco Freiles"
__description__ = "Libreria Universale AWS SSO per progetti ENEL"

# Esporta i principali componenti
from . import mylib
from . import setup_aws_sso

# Per compatibilità con import diretti
from .mylib import *

__all__ = [
    'mylib',
    'setup_aws_sso',
    '__version__',
    '__author__',
    '__description__'
]

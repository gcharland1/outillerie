# Setup initial et migrations futures

```
# Instancier pour le projet (une seule fois)
uv run flask db init

# Enregistrer la migration (durant le développement)
uv run flask db migrate -m "<message>"

# Appliquer la migration (avant de lancer l'app)
uv run flask db upgrade
```

# LIMITATIONS

* Si on ajoute une colonne non Nullable, il faut lui procurer une valeur par défaut sinon la migration plante

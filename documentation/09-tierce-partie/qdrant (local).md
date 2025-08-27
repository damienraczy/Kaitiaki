Voici la procédure exacte pour obtenir le **binaire Qdrant** de manière autonome, sans Docker, en le compilant depuis la source officielle.

---

### 1. Aller sur la page des releases de Qdrant sur GitHub

Accédez à la page des **releases de Qdrant**, où sont publiés les fichiers précompilés selon chaque version.
([GitHub][1])

---

### 2. Identifier et télécharger l’archive contenant le binaire

Dans la liste des assets d’une version stable (par exemple, `v1.x.x`), cherchez une archive spécifique à votre système :

* Exemple pour Windows (64 bits) : `qdrant-x86_64-pc-windows-msvc.zip`
  ([SourceForge][2])

Pour Linux (x86\_64 ou autre) ou macOS (Intel/ARM), une archive nommée de façon similaire (ex. `qdrant-*-linux-*`) devrait être disponible. Si elle ne l’est pas, optez pour la compilation par défaut (voir point 4).

---

### 3. Extraire et rendre exécutable

Une fois l’archive téléchargée :

```bash
unzip qdrant-*-*-*.zip     # adapter selon l’archive
# ou pour tar.gz / tar.bz2 :
tar -xzvf qdrant-*-*-*.tar.gz
```

Puis, rendez le fichier exécutable (si besoin) :

```bash
chmod +x qdrant
```

Copiez-le éventuellement dans votre `PATH` :

```bash
mv qdrant /usr/local/bin/
```

---

### 4. Alternative : Compiler le binaire avec Rust (si aucun asset natif disponible)

1. Installez Rust et Cargo (outil de compilation).

2. Clonez le dépôt Qdrant :

   ```bash
   git clone https://github.com/qdrant/qdrant.git
   cd qdrant
   ```

3. Compilez en mode release :

   ```bash
   cargo build --release --bin qdrant
   ```

4. Le binaire compilé sera disponible dans :

   ```
   ./target/release/qdrant
   ```

   Il fait environ 64 Mo décompressé.
   ([GitHub][3], [qdrant.co][4])

---

### 5. Lancer Qdrant (binaire natif)

Exécution simple :

```bash
./qdrant --storage-dir ./qdrant_storage
```

Vérifiez le bon fonctionnement avec :

```bash
curl http://localhost:6333/ready
```

Vous devriez voir une réponse `"ok"` si tout est configuré correctement.

---

### Récapitulatif

| Méthode                       | Description                                            |
| ----------------------------- | ------------------------------------------------------ |
| **Téléchargement direct**     | Récupération d’un binaire précompilé depuis GitHub     |
| **Compilation depuis source** | Utiliser Rust/Cargo pour générer le binaire localement |

---

Grâce à cette procédure, vous pouvez obtenir un **binaire Qdrant autonome**, sans Docker, et l’intégrer facilement dans votre pipeline Kaitiaki pour tests et prototypage.

[1]: https://github.com/qdrant/qdrant/releases?utm_source=chatgpt.com "Releases · qdrant/qdrant · GitHub"
[2]: https://sourceforge.net/projects/qdrant.mirror/files/v1.13.6/qdrant-x86_64-pc-windows-msvc.zip/download?utm_source=chatgpt.com "Download qdrant-x86_64-pc-windows-msvc.zip (Qdrant)"
[3]: https://github.com/qdrant/qdrant/issues/3920?utm_source=chatgpt.com "[Help] Regarding binary size of Qdrant Service · Issue #3920 · qdrant/qdrant · GitHub"
[4]: https://qdrant.co/documentation/guides/installation/?utm_source=chatgpt.com "Installation - Qdrant"

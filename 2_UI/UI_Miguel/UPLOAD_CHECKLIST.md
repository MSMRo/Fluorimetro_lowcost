# Lista de revisión para GitHub

## Contenido

1. Abre `README.md` y comprueba que la descripción del estado actual coincide con el montaje físico.
2. Revisa `PROGRESS.md` y completa cualquier fecha o cambio eléctrico que no esté registrado en los nombres de archivo.
3. Confirma que los cuatro clips representan el LED correcto. Los LED 3 y 4 no tienen longitud de onda nominal asignada porque el video no identifica el componente.
4. Revisa los datos de `Experiments/Arduino_Mega_4_LED/data/` y retira cualquier sesión que no deba publicarse.
5. Confirma la licencia de `Firmware/IO_Rodeo_PyBadge/reference_upstream/`.

## Archivos de macOS

`.DS_Store` está ignorado para archivos nuevos. Si el repositorio ya tenía copias rastreadas, Git seguirá mostrándolas hasta retirarlas del índice o restaurarlas. Revísalas por separado antes de usar `git add .`.

## Comprobaciones locales

```bash
git status --short
git diff --check
find . -type f -size +95M -print
```

No debería aparecer ningún archivo nuevo por encima de 95 MB. Los videos derivados actuales están por debajo de 46 MB cada uno.

## Preparar el commit

```bash
git add .
git status --short
git commit -m "Organiza avances del fluorimetro y documenta versiones"
git push
```

Revisa la lista de `git status` antes de confirmar. Este documento describe los comandos, pero no sustituye la revisión del contenido que se hará público.


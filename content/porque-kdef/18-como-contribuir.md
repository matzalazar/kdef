---
title: "18 — cómo contribuir"
date: 2026-04-08
tags: [meta, contribuir]
---

# 18. Cómo contribuir

## El modelo de dos zonas

```
content/
├── notas-automaticas/     ← zona del pipeline (no tocar)
└── notas-colaborativas/   ← acá contribuís vos
```

`content/notas-automaticas/` lo escribe el pipeline automáticamente cada semana. Los PRs que toquen ese directorio se rechazan.

`content/notas-colaborativas/` es el espacio para notas escritas por estudiantes. Apuntes de clase, resúmenes propios, explicaciones de conceptos difíciles, ejercicios resueltos, recursos adicionales. Cualquier cosa que le sirva a alguien que llega después que vos.

---

## Cómo abrir un PR

```bash
# Fork del repositorio desde GitHub

git clone https://github.com/matzalazar/kdef.git
cd kdef

# Crear rama
git checkout -b notas/criptografia-simetrica

# Crear tu nota en la carpeta de tu materia
# Usá la plantilla: content/notas-colaborativas/plantilla.md
cp content/notas-colaborativas/plantilla.md \
   content/notas-colaborativas/analisis-i/derivadas.md

# Editar, commitear y pushear
git add content/notas-colaborativas/analisis-i/derivadas.md
git commit -m "notas: derivadas — analisis-i"
git push origin notas/criptografia-simetrica

# Abrir el PR desde GitHub
```

---

## Convenciones de nombre de archivo

El nombre del archivo debe ser **una sola palabra en minúsculas sin acentos**:

```
derivadas.md       ✓
limites.md         ✓
criptografia.md    ✓

mi-nota-sobre-derivadas.md   ✗  (varias palabras)
Derivadas.md                 ✗  (mayúscula)
```

El título completo va en el frontmatter (`title`), no en el nombre del archivo.

---

## Frontmatter requerido

```yaml
---
title: "Derivadas — definición y reglas básicas"
date: 2026-04-08
tags: [analisis-i, derivadas, calculo]
subject: analisis-i
author: tu-usuario-de-github
---
```

---

## Qué se acepta y qué no

**Aceptado:** 
- Notas de clase 
- Resúmenes propios 
- Explicaciones de conceptos 
- Ejercicios resueltos 
- Referencias útiles

**Rechazado:**
- Contenido fuera del curriculum de la carrera
- Exámenes completos o material que facilite trampa
- Archivos sin frontmatter
- Archivos binarios (imágenes, PDFs, ejecutables)
- Contenido ofensivo o inapropiado
- Modificaciones a `content/notas-automaticas/`

---

¿Dudas? Abrí un [issue en GitHub](https://github.com/matzalazar/kdef/issues).

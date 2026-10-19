---
title: bilbiografia
date: '2026-10-19'
tags:
- auto-generado
source: Bilbiografia_Auxiliar_Introducción al UML.pdf
source_path: lenguajes-programacion/10-19-a-10-23/Bilbiografia_Auxiliar_Introducción al UML.pdf
generated_at: '2026-10-19T08:47:44.499239+00:00'
important_dates: []
---

> **Nota:** Este archivo fue generado automáticamente por el pipeline de kdef.
> El contenido proviene de materiales del aula virtual de la UNDEF.
> Para correcciones, abrí un issue en el repositorio.

## Resumen de “Introducción al Lenguaje de Modelado Unificado (UML)”

**Título:** Introducción al Lenguaje de Modelado Unificado (UML)  

**Conceptos clave:**  
- **UML:** lenguaje de modelado basado en diagramas para especificar, visualizar, construir y documentar sistemas software.  
- **Clase y objeto:** plantilla y sus instancias; se representan con rectángulo de tres compartimentos (nombre, atributos, operaciones).  
- **Atributos y operaciones:** propiedades y comportamiento; visibilidad indicada con `+` (público), `#` (protegido), `-` (privado).  
- **Asociación:** vínculo entre clases; puede ser binaria o n‑aria, con cardinalidad (0..1, 1..*, etc.) y roles.  
- **Agregación y composición:** relaciones “todo/parte”; composición implica ciclo de vida dependiente del todo.  
- **Dependencia (uso):** relación débil donde un cambio en la clase usada puede afectar al dependiente.  
- **Generalización (herencia):** relación “es un tipo de” entre superclase y subclase, representada con flecha triangular.  
- **Interfaz:** especificación de operaciones abstractas, estereotipo `<<interface>>`.  
- **Excepción:** clase estereotipada `<<exception>>` que puede llevar atributos (parámetros).  
- **Paquete:** agrupación de elementos del modelo para reducir acoplamiento y aumentar cohesión; relación con paquetes Java mediante estructura de nombres.

**Desarrollo principal:**  
El documento comienza definiendo UML y su independencia de metodologías y lenguajes, destacando su base en la orientación a objetos. Se detalla la notación de clases (nombre, atributos con tipo y visibilidad, operaciones con signatura y dirección de parámetros) y se muestra su traducción a Java, incluyendo constructores, getters/setters y comentarios Javadoc.  
Se analizan las relaciones entre clases: asociaciones binarias (con dirección, roles y cardinalidad), asociaciones reflexivas y n‑arias, agregación y composición (con ejemplos de GrupoDeTrabajo y Documento/Página/Párrafo), y dependencias (uso sin mantenimiento de enlaces).  
Luego se explica la generalización mediante jerarquías de herencia, con ejemplo de cuentas bancarias que derivan en CuentaPlazoFijo y cuenta con crédito limitado.  
Se introducen otros elementos de modelado: interfaces (para separar especificación e implementación) y excepciones (con atributos que informan el motivo del error).  
Finalmente, se trata la estructuración mediante paquetes UML, su correspondencia con paquetes Java (ej. `es.uoc.iti.bancario.cuentas` y `es.uoc.iti.bancario.hacienda`), y se concluye con recursos y bibliografía (Booch 1999, Gamma 1995 y el OMG UML 1.3).

**Conclusiones:**  
UML constituye una herramienta esencial para modelar la estructura estática de sistemas software, facilitando la comunicación entre analistas, desarrolladores y otros stakeholders mediante diagramas de clases bien definidos. Su notación permite representar con precisión atributos, operaciones, visibilidad y diversos tipos de relaciones (asociación, agregación, composición, dependencia y generalización), y se integra directamente con lenguajes de programación como Java mediante reglas de implementación claras. El uso de paquetes mejora la organización de modelos grandes, manteniendo bajo acoplamiento y alta cohesión, lo que resulta útil en proyectos de ciberdefensa donde la claridad y la trazabilidad son críticas.

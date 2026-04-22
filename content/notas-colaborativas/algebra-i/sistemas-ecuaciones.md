---
title: sistemas-ecuaciones
tags:
  - colaborativo
  - algebra-i
  - sistemas-ecuaciones
subject: algebra-i
author: matzalazar
date: 2026-04-22
---

## 1. Definición de un SEL

Un sistema de $m$ ecuaciones lineales con $n$ incógnitas se expresa como:
$$\begin{cases} a_{11}x_1 + a_{12}x_2 + \dots + a_{1n}x_n = b_1 \\ a_{21}x_1 + a_{22}x_2 + \dots + a_{2n}x_n = b_2 \\ \vdots \\ a_{m1}x_1 + a_{m2}x_2 + \dots + a_{mn}x_n = b_m \end{cases}$$

### Representación Matricial

Todo SEL puede escribirse de forma compacta como **$A \cdot X = B$**, donde:

* **$A$**: Matriz de coeficientes (dimensión $m \times n$).
* **$X$**: Vector columna de incógnitas.
* **$B$**: Vector columna de términos independientes.
* **$[A|B]$**: Matriz ampliada (incluye los resultados).

**Ejemplo de representación:**

Para el sistema:
$$\begin{cases} 2x - 3y = 4 \\ 5x + y = -1 \end{cases}$$

La representación matricial es:
$$\underbrace{\begin{pmatrix} 2 & -3 \\ 5 & 1 \end{pmatrix}}_{A} \cdot \underbrace{\begin{pmatrix} x \\ y \end{pmatrix}}_{X} = \underbrace{\begin{pmatrix} 4 \\ -1 \end{pmatrix}}_{B}$$

Y la matriz ampliada:
$$[A|B] = \left( \begin{array}{cc|c} 2 & -3 & 4 \\ 5 & 1 & -1 \end{array} \right)$$

---

## 2. Clasificación de los Sistemas

Dependiendo de sus soluciones, un sistema puede ser:

1.  **Compatible (SC):** Tiene solución.
    * **Determinado (SCD):** Solución única.
    * **Indeterminado (SCI):** Infinitas soluciones.
2.  **Incompatible (SI):** No tiene solución (el conjunto solución es vacío $\emptyset$).

### Ejemplos de Clasificación

#### Sistema Compatible Determinado (SCD)

Un sistema con una única solución. Por ejemplo:
$$\begin{cases} x + y = 3 \\ x - y = 1 \end{cases}$$
Al sumar ambas ecuaciones obtenemos $2x = 4 \implies x = 2$. Sustituyendo en la primera: $2 + y = 3 \implies y = 1$.
**Solución única:** $(x, y) = (2, 1)$.

#### Sistema Compatible Indeterminado (SCI)

Un sistema con infinitas soluciones. Por ejemplo:
$$\begin{cases} x + y = 2 \\ 2x + 2y = 4 \end{cases}$$
La segunda ecuación es el doble de la primera, por lo que aporta la misma información. Tenemos una sola restricción para dos incógnitas.
**Solución general:** $y = 2 - x$, donde $x$ es una variable libre ($x \in \mathbb{R}$).

#### Sistema Incompatible (SI)

Un sistema que no tiene solución. Por ejemplo:
$$\begin{cases} x + y = 2 \\ x + y = 3 \end{cases}$$
Restando la primera de la segunda obtendríamos $0 = 1$, lo cual es un absurdo.
**Solución:** No existe ninguna pareja $(x, y)$ que satisfaga ambas igualdades simultáneamente. Conjunto solución: $\emptyset$.

---

## 3. Teorema de Rouché-Capelli

Es la herramienta fundamental para clasificar un sistema comparando el rango de la matriz de coeficientes ($rg(A)$) y el de la matriz ampliada ($rg(A|B)$).

Sea $n$ el número de incógnitas:

| Condición | Tipo de Sistema | Notas |
| :--- | :--- | :--- |
| $rg(A) \neq rg(A\|B)$ | **Incompatible (SI)** | No hay solución. |
| $rg(A) = rg(A\|B) = n$ | **Compatible Determinado (SCD)** | Solución única ($n$ es el nº de incógnitas). |
| $rg(A) = rg(A\|B) < n$ | **Compatible Indeterminado (SCI)** | Infinitas soluciones (existen variables libres). |

---

## 4. Análisis de Sistemas con Parámetros

A menudo los sistemas dependen de una variable (como $\lambda$ o $a$). El objetivo es determinar para qué valores de dicho parámetro el sistema cambia de tipo.

**Ejemplo Práctico con Parámetro:**

Sea el sistema:
$$\begin{cases} x + y + z = 1 \\ x + 2y + 3z = 2 \\ x + 2y + \lambda z = 3 \end{cases}$$

Su matriz ampliada es:
$$[A|B] = \left( \begin{array}{ccc|c} 1 & 1 & 1 & 1 \\ 1 & 2 & 3 & 2 \\ 1 & 2 & \lambda & 3 \end{array} \right)$$

Aplicando Gauss ($F_2 - F_1$ y $F_3 - F_1$):
$$\left( \begin{array}{ccc|c} 1 & 1 & 1 & 1 \\ 0 & 1 & 2 & 1 \\ 0 & 1 & \lambda-1 & 2 \end{array} \right)$$

Y luego $F_3 - F_2$:
$$\left( \begin{array}{ccc|c} 1 & 1 & 1 & 1 \\ 0 & 1 & 2 & 1 \\ 0 & 0 & \lambda-3 & 1 \end{array} \right)$$

**Análisis según $\lambda$:**
*   **Si $\lambda = 3$:** La última fila es $(0 \ 0 \ 0 \ | \ 1)$, lo que implica $0 = 1$ (**Sistema Incompatible**).
*   **Si $\lambda \neq 3$:** El rango de $A$ es 3 y el de la ampliada también es 3, igual al número de incógnitas (**Sistema Compatible Determinado**).

---

## 5. Métodos de Resolución

* **Eliminación de Gauss:** Transformar la matriz ampliada en una forma escalonada.
* **Sustitución Regresiva:** Una vez escalonado el sistema, despejar las variables desde la última ecuación hacia la primera.
* **Variables Libres:** En un SCI, si $rg(A) = k < n$, entonces hay $n - k$ variables libres que definen la solución general.

---

## 6. Interpretación Geométrica (en $\mathbb{R}^2$)

* **SCD:** Dos rectas que se cruzan en un único punto $(x, y)$.
* **SCI:** Dos rectas coincidentes (una encima de la otra).
* **SI:** Dos rectas paralelas no coincidentes.
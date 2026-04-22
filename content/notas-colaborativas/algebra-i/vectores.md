---
title: vectores
tags:
  - colaborativo
  - algebra-i
  - vectores
subject: algebra-i
author: matzalazar
date: 2026-04-22
---

## 1. Definición y Representación

Un vector es un elemento de un espacio vectorial caracterizado por una **magnitud** y una **dirección**. Se expresan generalmente en forma de fila con componentes reales.

* **En el plano ($\mathbb{R}^2$):** $v=(v_{1},v_{2})$.
* **En el espacio ($\mathbb{R}^3$):** $v=(v_{1},v_{2},v_{3})$.
* **Caso general ($\mathbb{R}^n$):** $v=(v_{1},v_{2},...,v_{n})$.

---

## 2. Operaciones Básicas

### Suma y Resta
Dados $u=(u_{1},u_{2})$ y $v=(v_{1},v_{2})$, las operaciones se realizan componente a componente:
* **Suma:** $u+v=(u_{1}+v_{1},u_{2}+v_{2})$.
* **Resta:** $u-v=(u_{1}-v_{1},u_{2}-v_{2})$.

**Ejemplo:**
Si tenemos los vectores $u = (3, -1)$ y $v = (1, 4)$:
* **Suma:** $u + v = (3 + 1, -1 + 4) = (4, 3)$.
* **Resta:** $u - v = (3 - 1, -1 - 4) = (2, -5)$.

Gráficamente, la suma se representa mediante la **regla del paralelogramo**.

### Producto por un Escalar

Multiplicar un vector por un número real $k$ afecta a cada componente:

$$
kv=(kv_{1},kv_{2})
$$

Esta operación puede alterar la magnitud y el sentido del vector, pero mantiene su dirección (o la invierte si $k < 0$).

**Ejemplo:**
Sea $v = (2, -4, 5)$ en $\mathbb{R}^3$ y el escalar $k = 3$:
$$3v = (3 \cdot 2, 3 \cdot (-4), 3 \cdot 5) = (6, -12, 15)$$
El nuevo vector tiene la misma dirección que $v$ pero es tres veces más largo.

---

## 3. Operaciones Avanzadas

### Producto Escalar

Se define para dos vectores de igual dimensión como la suma de los productos de sus componentes:

$$
u\cdot v=u_{1}v_{1}+u_{2}v_{2}+\dots+u_{n}v_{n}
$$

* **Propiedades:** Es conmutativo ($u\cdot v=v\cdot u$), distributivo respecto a la suma y asociativo con escalares.

**Ejemplo:**
Dados $u = (1, 2, -3)$ y $v = (4, 0, 1)$:
$$u \cdot v = (1)(4) + (2)(0) + (-3)(1) = 4 + 0 - 3 = 1$$
Como el resultado es un escalar (número) y no un vector, se llama producto escalar.

### Producto Vectorial

Operación exclusiva del espacio $\mathbb{R}^3$. Para $u=(u_{1},u_{2},u_{3})$ y $v=(v_{1},v_{2},v_{3})$, el resultado es otro vector perpendicular a ambos:

$$
u\times v=(u_{2}v_{3}-u_{3}v_{2}, u_{3}v_{1}-u_{1}v_{3}, u_{1}v_{2}-u_{2}v_{1})
$$

**Ejemplo:**
Sean $u = (1, 0, 2)$ y $v = (0, 1, 3)$. Calculamos $u \times v$:
$$u \times v = \begin{vmatrix} \mathbf{i} & \mathbf{j} & \mathbf{k} \\ 1 & 0 & 2 \\ 0 & 1 & 3 \end{vmatrix}$$
$$u \times v = (0\cdot3 - 2\cdot1)\mathbf{i} - (1\cdot3 - 2\cdot0)\mathbf{j} + (1\cdot1 - 0\cdot0)\mathbf{k}$$
$$u \times v = (-2, -3, 1)$$


### Proyección

La proyección del vector $u$ sobre el vector $v$ se calcula como:

$$
proj_{v}u = \left( \frac{u\cdot v}{\|v\|^{2}} \right) v
$$

**Ejemplo:**
Proyectar $u = (2, 1)$ sobre $v = (-3, 4)$:
1. $u \cdot v = (2)(-3) + (1)(4) = -6 + 4 = -2$
2. $\|v\|^2 = (-3)^2 + 4^2 = 9 + 16 = 25$
3. $proj_{v}u = \frac{-2}{25}(-3, 4) = (\frac{6}{25}, -\frac{8}{25})$

---

## 4. Conceptos de Magnitud y Relación

### Norma y Versores

* **Norma:** Representa la longitud del vector:

$$
\|v\|=\sqrt{v_{1}^{2}+v_{2}^{2}+\dots+v_{n}^{2}}
$$

* **Versor:** Es un vector unitario ($\| \hat{v} \|=1$) con la misma dirección que $v$

$$
\hat{v}=\frac{v}{\|v\|}
 $$

**Ejemplo:**
Para el vector $v = (3, 4)$:
* **Norma:** $\|v\| = \sqrt{3^2 + 4^2} = \sqrt{9 + 16} = 5$.
* **Versor:** $\hat{v} = \frac{(3, 4)}{5} = (0.6, 0.8)$.

### Paralelismo y Ortogonalidad

* **Paralelos:** Si existe un escalar $k$ tal que $u=kv$.
* **Ortogonales (Perpendiculares):** Si su producto escalar es cero: $u\cdot v=0$.

**Ejemplo de Ortogonalidad:**
¿Son $u = (1, 2)$ y $v = (-2, 1)$ perpendiculares?
$$u \cdot v = (1)(-2) + (2)(1) = -2 + 2 = 0$$
Sí, son perpendiculares.
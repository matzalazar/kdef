---
title: plantilla
tags:
  - colaborativo
  - analisis-i
  - conjuntos
  - intervalos
subject: analisis-i
author: matzalazar
date: 2026-04-22
---

## 1. Conjuntos Numéricos

Se repasan los conjuntos fundamentales utilizados en el análisis matemático:

* **Naturales ($\mathbb{N}$):** $\{1, 2, 3, 4, ...\}$, utilizados para contar.
    * *Ejemplo:* $5 \in \mathbb{N}$, pero $0 \notin \mathbb{N}$ (en este contexto).
* **Enteros ($\mathbb{Z}$):** $\{..., -2, -1, 0, 1, 2, ...\}$, incluyen los naturales y sus opuestos.
    * *Ejemplo:* $-3 \in \mathbb{Z}$, $0 \in \mathbb{Z}$.
* **Racionales ($\mathbb{Q}$):** Formados por todas las fracciones de la forma $\frac{a}{b}$ con $a, b \in \mathbb{Z}$ y $b \neq 0$.
    * *Ejemplo:* $\frac{3}{4} = 0,75$ (decimal finito) o $\frac{1}{3} = 0,333... = 0,\hat{3}$ (decimal periódico).
* **Irracionales ($\mathbb{I}$):** Números que no pueden expresarse como fracción. Tienen infinitas cifras decimales no periódicas.
    * *Ejemplo:* $\sqrt{2} \approx 1,4142...$, $\pi \approx 3,1415...$, $e \approx 2,7182...$.
* **Reales ($\mathbb{R}$):** La unión de racionales e irracionales ($\mathbb{R} = \mathbb{Q} \cup \mathbb{I}$).
* **Relación de inclusión:** $\mathbb{N} \subset \mathbb{Z} \subset \mathbb{Q} \subset \mathbb{R}$.

### Propiedades de los Racionales

Los números racionales poseen dos operaciones (suma y producto) que satisfacen los **axiomas de cuerpo**. Además, $\mathbb{Q}$ es un **cuerpo ordenado**, lo que permite comparar cualquier par de números ($x < y$, $x > y$ o $x = y$). Todo número racional puede expresarse como un desarrollo decimal finito o periódico.

---

## 2. Intervalos e Inecuaciones

Un **intervalo** es el conjunto de números reales que ocupan los puntos de un segmento o una semirrecta.

### Ejemplos de representación:

* **Semirrecta cerrada:** $A = \{x \in \mathbb{R} | x \ge 1\}$ se denota como $A = [1, +\infty)$.
* **Segmento semiabierto:** $B = \{x \in \mathbb{R} | -1 < x \le 2\}$ se escribe como $B = (-1, 2]$.
* **Intervalo abierto:** $C = \{x \in \mathbb{R} | -3 < x < 5\}$ se escribe como $C = (-3, 5)$.

### Resolución de Inecuaciones:

**Ejemplo 1: Inecuación lineal doble**

Para determinar el conjunto $A = \{x \in \mathbb{R} | 7 \le 2x + 1 \le 9\}$, se opera algebraicamente manteniendo el equilibrio en todos los miembros:
$$7 \le 2x + 1 \le 9$$
$$7 - 1 \le 2x \le 9 - 1 \Rightarrow 6 \le 2x \le 8$$
$$\frac{6}{2} \le x \le \frac{8}{2} \Rightarrow 3 \le x \le 4$$
Por lo tanto, $A = [3, 4]$.

**Ejemplo 2: Inecuación cuadrática**

Resolver $x^2 - 4 < 0$:
$$x^2 < 4 \Rightarrow \sqrt{x^2} < \sqrt{4} \Rightarrow |x| < 2$$
Esto define el intervalo $(-2, 2)$.

### Valor Absoluto:

El valor absoluto $|x|$ representa la distancia al origen. Las inecuaciones con valor absoluto se resuelven según:
1. $|x| < a \iff -a < x < a$
2. $|x| > a \iff x > a \text{ o } x < -a$

**Ejemplo 3: Distancia a un punto**

$$|x - 3| < 2 \Rightarrow -2 < x - 3 < 2$$
Sumamos 3 en todos los términos:
$$-2 + 3 < x < 2 + 3 \Rightarrow 1 < x < 5$$
Dando como resultado el intervalo $D = (1, 5)$.

**Ejemplo 4: Exterior de un intervalo**

$$|2x + 4| \ge 6$$
Esto se divide en dos casos:
1. $2x + 4 \ge 6 \Rightarrow 2x \ge 2 \Rightarrow x \ge 1$
2. $2x + 4 \le -6 \Rightarrow 2x \le -10 \Rightarrow x \le -5$
El conjunto solución es $(-\infty, -5] \cup [1, +\infty)$.

---

## 3. Acotación: Supremo e Ínfimo

### Cotas Superiores y Supremo

*   **Cota superior:** Un número $K$ es cota superior de $A$ si $\forall a \in A, a \le K$. Si existe al menos una cota superior, se dice que el conjunto está **acotado superiormente**.
*   **Supremo ($\sup$):** Es la menor de las cotas superiores. Es decir, $S = \sup(A)$ si:
    1. $S$ es cota superior de $A$.
    2. Si $K$ es otra cota superior, entonces $S \le K$.
*   **Máximo ($\max$):** Si $\sup(A) \in A$, entonces el supremo es el máximo.

### Cotas Inferiores e Ínfimo

*   **Cota inferior:** Un número $k$ es cota inferior de $A$ si $\forall a \in A, k \le a$. Si existe al menos una cota inferior, el conjunto está **acotado inferiormente**.
*   **Ínfimo ($\inf$):** Es la mayor de las cotas inferiores. Es decir, $i = \inf(A)$ si:
    1. $i$ es cota inferior de $A$.
    2. Si $k$ es otra cota inferior, entonces $k \le i$.
*   **Mínimo ($\min$):** Si $\inf(A) \in A$, entonces el ínfimo es el mínimo.

### Ejemplos de Análisis de Acotación:

**Ejemplo 1: Intervalo abierto $A = (0, 1)$**
*   Cotas superiores: $[1, +\infty)$. Supremo: $\sup(A) = 1$. ¿Máximo? No, $1 \notin (0, 1)$.
*   Cotas inferiores: $(-\infty, 0]$. Ínfimo: $\inf(A) = 0$. ¿Mínimo? No, $0 \notin (0, 1)$.

**Ejemplo 2: Conjunto discreto $B = \{2 + \frac{1}{n} : n \in \mathbb{N}\}$**
1.  Elementos: $B = \{3, 2.5, 2.33, 2.25, ...\}$
2.  **Supremo:** $\sup(B) = 3$. Como $3 \in B$ (cuando $n=1$), entonces $\max(B) = 3$.
3.  **Ínfimo:** A medida que $n \to \infty$, el término $\frac{1}{n} \to 0$, por lo que los valores se acercan a 2 pero nunca lo alcanzan. Así, $\inf(B) = 2$. Como $2 \notin B$, no existe mínimo.

---

## 4. Anexo Teórico

### Axiomas de Cuerpo (Suma y Producto) 

Para todo $a, b, c \in \mathbb{R}$:
*   **Conmutatividad:** $a+b = b+a$ y $a \cdot b = b \cdot a$.
*   **Asociatividad:** $(a+b)+c = a+(b+c)$ y $(a \cdot b) \cdot c = a \cdot (b \cdot c)$.
*   **Existencia de Neutro:** $a+0 = a$ y $a \cdot 1 = a$.
*   **Existencia de Inverso:** $a + (-a) = 0$ y $a \cdot a^{-1} = 1$ (para $a \neq 0$).
*   **Distributividad:** $a \cdot (b+c) = a \cdot b + a \cdot c$.

### Conversión de Decimales Periódicos a Fracción

**Ejemplo: Convertir $x = 1,23535... = 1,2\widehat{35}$**
1.  Multiplicamos para que el periodo empiece justo después de la coma: $10x = 12,3535...$
2.  Multiplicamos para mover un periodo a la izquierda de la coma: $1000x = 1235,3535...$
3.  Restamos ambas ecuaciones:
    $$1000x - 10x = 1235,3535... - 12,3535...$$
    $$990x = 1223 \Rightarrow x = \frac{1223}{990}$$

### Irracionalidad de $\sqrt{2}$ (Demostración por el Absurdo)

1.  Supongamos que $\sqrt{2}$ es racional: $\sqrt{2} = \frac{p}{q}$ con $p, q$ coprimos (fracción irreducible).
2.  Elevamos al cuadrado: $2 = \frac{p^2}{q^2} \Rightarrow p^2 = 2q^2$.
3.  Esto implica que $p^2$ es par, por lo tanto $p$ es par ($p = 2k$).
4.  Sustituimos: $(2k)^2 = 2q^2 \Rightarrow 4k^2 = 2q^2 \Rightarrow 2k^2 = q^2$.
5.  Esto implica que $q^2$ es par, por lo tanto $q$ es par.
6.  **Contradicción:** Si $p$ y $q$ son ambos pares, la fracción $\frac{p}{q}$ no era irreducible. Por lo tanto, la suposición inicial es falsa y $\sqrt{2}$ es irracional.
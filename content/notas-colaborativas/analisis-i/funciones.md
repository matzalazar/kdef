---
title: plantilla
tags:
  - colaborativo
  - analisis-i
  - funciones
subject: analisis-i
author: matzalazar
date: 2026-04-22
---

## 1. Definición de Función y Dominios

Una **función** $f: A \to B$ es una regla que asigna a cada elemento $x \in A$ un **único** elemento $y = f(x) \in B$.
* **Dominio ($A$):** Conjunto de todos los valores de entrada permitidos.
* **Imagen o Rango:** Conjunto de todos los valores que efectivamente toma $f(x)$.

### Restricciones del Dominio en $\mathbb{R}$

Para determinar el dominio de forma analítica, debemos vigilar tres prohibiciones clave:

1.  **Denominadores:** No se puede dividir por cero ($denominador \neq 0$).

**Ejemplo:** $f(x) = \frac{x+1}{x^2-9}$
$$x^2 - 9 \neq 0 \implies x^2 \neq 9 \implies x \neq \pm 3$$
**Dominio:** $\text{Dom}(f) = \mathbb{R} - \{-3, 3\}$

2.  **Raíces de índice par:** El argumento debe ser no negativo ($\geq 0$).

**Ejemplo:** $g(x) = \sqrt{2x+3}$
$$2x + 3 \geq 0 \implies 2x \geq -3 \implies x \geq -\frac{3}{2}$$
**Dominio:** $\text{Dom}(g) = [-\frac{3}{2}, +\infty)$

3.  **Logaritmos:** El argumento debe ser estrictamente positivo ($0$).

**Ejemplo:** $h(x) = \ln(x-5)$
$$x - 5 0 \implies x 5$$
**Dominio:** $\text{Dom}(h) = (5, +\infty)$

---

## 2. Clasificación por Simetría: Pares e Impares

Las funciones pueden presentar simetrías respecto al eje de ordenadas o al origen.

| Tipo | Condición Algebraica | Simetría Geométrica | Ejemplo |
| :--- | :--- | :--- | :--- |
| **Par** | $f(-x) = f(x)$  | Simétrica respecto al **eje $y$**  | $f(x) = x^2$  |
| **Impar** | $f(-x) = -f(x)$  | Simétrica respecto al **origen**  | $f(x) = x^3$  |

### Verificación Algebraica

*   **Para $f(x) = x^2 + 4$:**
$$f(-x) = (-x)^2 + 4 = x^2 + 4 = f(x) \implies \text{Es Par}$$
*   **Para $g(x) = x^3 - x$:**
$$g(-x) = (-x)^3 - (-x) = -x^3 + x = -(x^3 - x) = -g(x) \implies \text{Es Impar}$$

---

## 3. Propiedades de Inyectividad y Biyectividad

Para entender si una función tiene inversa, debemos analizar cómo se relacionan los elementos:

* **Inyectiva:** Elementos distintos del dominio tienen imágenes distintas. No hay dos $x$ que compartan la misma $y$.
* **Sobreyectiva:** Todos los elementos del codominio son imagen de al menos un elemento del dominio.
* **Biyectiva:** Es inyectiva y sobreyectiva a la vez.

### Función Inversa ($f^{-1}$)

Si una función es **biyectiva**, admite una inversa tal que:
$$y = f(x) \iff x = f^{-1}(y)$$
**Procedimiento para hallarla:** Intercambiar variables $x$ e $y$ y despejar la nueva $y$.
**Ejemplo:** Sea $f(x) = \frac{x+5}{3}$
1. Escribimos $y = \frac{x+5}{3}$.
2. Intercambiamos: $x = \frac{y+5}{3}$.
3. Despejamos $y$: $3x = y + 5 \implies y = 3x - 5$.
4. Por lo tanto, $f^{-1}(x) = 3x - 5$.

---

## 4. Trigonometría: Identidades Clave

Las identidades permiten simplificar expresiones complejas y resolver ecuaciones.

* **Identidad Fundamental:** $\cos^2(\alpha) + \sin^2(\alpha) = 1$.
* **Suma de Ángulos (Tangente):** $\tan(\alpha+\beta) = \frac{\tan \alpha + \tan \beta}{1 - \tan \alpha \tan \beta}$.
* **Ángulo Doble:**
* $\sin(2\alpha) = 2 \sin \alpha \cos \alpha$.
* $\cos(2\alpha) = \cos^2\alpha - \sin^2\alpha$.

**Ejemplo (Ángulo Doble):** Si $\sin \alpha = 0,6$ y $\cos \alpha = 0,8$:
$$\sin(2\alpha) = 2 \cdot 0,6 \cdot 0,8 = 0,96$$

---

## 5. Exponenciales y Logaritmos

Son funciones inversas entre sí. La base $b$ debe cumplir $b 0$ y $b \neq 1$.

### Propiedades de los Logaritmos:

1.  $\log_b(1) = 0$ 
2.  $\log_b(b) = 1$ 
3.  **Producto:** $\log_b(m \cdot n) = \log_b(m) + \log_b(n)$ 
* Ejemplo: $\log_2(8 \cdot 4) = \log_2(8) + \log_2(4) = 3 + 2 = 5$
1.  **Cociente:** $\log_b(\frac{m}{n}) = \log_b(m) - \log_b(n)$ 
* Ejemplo: $\log_2(\frac{16}{2}) = \log_2(16) - \log_2(2) = 4 - 1 = 3$
1.  **Potencia:** $\log_b(m^p) = p \cdot \log_b(m)$ 
* Ejemplo: $\log_{10}(100^5) = 5 \cdot \log_{10}(100) = 5 \cdot 2 = 10$
1.  **Cambio de Base:** $\log_a(x) = \frac{\log_b(x)}{\log_b(a)}$ 
* Ejemplo: $\log_8(64) = \frac{\ln(64)}{\ln(8)} = \frac{6 \ln 2}{3 \ln 2} = 2$

---

## 6. Análisis de Proposiciones y Errores Comunes

En matemática, una afirmación es falsa si existe al menos un **contraejemplo**.

| Proposición Falsa                                  | Contraejemplo / Error                          | Forma Correcta                                                      |
| :------------------------------------------------- | :--------------------------------------------- | :------------------------------------------------------------------ |
| $\ln(x+y) = \ln x + \ln y$  | $\ln(1+1) \neq \ln(1) + \ln(1)$ | Solo se separan productos: $\ln(x \cdot y)$  |
| $(a+b)^2 = a^2 + b^2$       | $(1+2)^2 = 9 \neq 1^2 + 2^2 = 5$ | $(a+b)^2 = a^2 + 2ab + b^2$                  |
| $\sqrt{x^2+y^2} = x+y$      | $\sqrt{3^2+4^2} = 5 \neq 3+4 = 7$ | No existe propiedad distributiva para sumas |

**Recordatorio:** Las funciones trigonométricas tampoco son lineales:
$$\sin(x+y) \neq \sin x + \sin y$$
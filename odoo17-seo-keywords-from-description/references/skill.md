---
name: odoo17-seo-keywords-from-description
description: En Odoo 17 Community (navegador), recorre productos, lee description_ecommerce y rellena Título, Descripción y Palabras clave del modal "Optimizar SEO".
---

# Odoo 17: generar SEO completo (Title, Description, Keywords) desde description_ecommerce

## Antes de empezar (no compartir credenciales)
Necesito:
1) La URL exacta es `https://palomar.xtd.es/`
2) Las credenciales son "xtendoo" y "Xtend00!"
3) Confirmación de que:
   - Estás **logueado** en el navegador (sesión activa)
   - Tienes permisos para editar productos y acceder a edición del sitio web

> Importante: **no pegues usuario ni contraseña**. Si no estás logueado, inicia sesión tú manualmente y dime “listo”.

## Qué hace este skill (resultado)
Para cada producto publicado (empezando por el primero de la lista):
- Comprueba si ya está procesado (en `seo_keywords_report.csv`).
- Si ya está hecho → Pasa al siguiente (botón "Siguiente").
- Si NO está hecho:
  - Lee `description_ecommerce`.
  - Genera SEO (Title, Desc, Keywords).
  - Va al sitio web, rellena y guarda.
  - Vuelve al backend.
  - Registra en CSV.
  - Pasa al siguiente.

## Reglas de contenido (IA)

### 1) Título (Title)
- Longitud: **50 a 60 caracteres**.
- Formato: `[Nombre Producto] [Atributo clave] | [Marca/Tienda]` (o similar).
- Debe ser atractivo y contener la keyword principal.
- **Ortografía perfecta**: El Título SEO generado debe tener tildes y mayúsculas correctas, aunque el nombre original del producto flaquee. NO TOCA el nombre del producto en el backend.

### 2) Descripción (Description)
- Longitud: **140 a 160 caracteres**.
- **Resumen persuasivo** del producto basado en la `description_ecommerce`.
- Incluir llamada a la acción o beneficio claro.
- No cortar frases a mitad.
- **Corrección gramatical**: El texto generado para el SEO debe tener ortografía y redacción impecables. **IMPORTANTE**: No corregir ni tocar la descripción original en la ficha del producto, solo escribir bien en la ventana modal de SEO.

### 3) Keywords
- 8 a 15 keywords.
- Minúsculas.
- Deduplicadas.
- Mezcla:
  - términos principales del producto
  - long-tail (2–5 palabras) con intención de compra
  - usos / aplicaciones del texto
  - marca/modelo si aparece
- Evitar genéricas vacías (“producto”, “tienda”, “online”) salvo que aporten.
- Salida final: lista de keywords (no texto con comas) porque el SEO las guarda como tags.

## Reporte (obligatorio)
Archivo: `seo_keywords_report.csv` en el directorio de trabajo.
Columnas:
- timestamp, product_name, product_ref, website_slug, meta_title, meta_description, keywords, status, notes

Para registrar:
`python scripts/append_report_csv.py "<product_name>" "<product_ref>" "<website_slug>" "<meta_title>" "<meta_description>" "<keywords_csv>" "<status>" "<notes>"`

> keywords_csv: en el reporte sí se guardan separadas por coma para lectura humana.

## Runbook exacto (tu UI)

### 1) Ir a la lista de productos (backoffice)
Entrar por:
- **Comercio electrónico → Productos** (preferido)
o alternativamente:
- **Ventas → Productos → Productos**

### 2) Filtrar SOLO publicados
Aplicar filtro/condición:
- “Publicado” / “Publicado en el sitio web” / “En el sitio web” = TRUE

Si no aparece el filtro, usar filtros avanzados para localizar el boolean de publicado.

### 3) Estrategia de Iteración (Botón "Siguiente")
1.  **Cargar contexto**: Leer `seo_keywords_report.csv` (si existe) para saber qué productos saltar.
2.  **Iniciar ciclo**:
    - Desde la vista de lista filtrada, abrir el **primer producto**.
3.  **Bucle (para cada producto)**:
    - Verificar Nombre/Ref.
    - **¿Ya está en el reporte?**
      - **SÍ**: Pulsar botón **"Siguiente" (flecha derecha >)** en la esquina superior derecha del formulario. Repetir bucle.
      - **NO**: Ejecutar pasos de SEO (ver abajo).
        - Al terminar y guardar en frontend:
        - Volver al backend (atrás en navegador 2 veces o click en breadcrumb del producto).
        - Registrar en CSV.
        - Pulsar botón **"Siguiente"**.
4.  **Fin**: Cuando el botón "Siguiente" esté deshabilitado o desaparezca.

### 4) En cada producto (formulario backoffice)
#### 4.1 Capturar datos para reporte
- `product_name`: título del producto (header).
- `product_ref`: “Referencia interna” si está visible (ej. G02150). Si no, vacío.
- Confirmar si aparece el indicador “Publicado” (en tu captura aparece).

#### 4.2 Localizar y leer description_ecommerce
En Odoo 17 suele estar en alguna pestaña tipo:
- **Ventas** / **Comercio electrónico** / **Sitio web**
y suele llamarse parecido a:
- “Descripción del sitio web”
- “Descripción eCommerce”
- “Descripción para eCommerce”
- Editor HTML/WYSIWYG

Acción:
- Extraer el **texto** (sin etiquetas HTML si las hay).
- Si el contenido está vacío:
  - status = SKIPPED_EMPTY
  - notes = "description_ecommerce empty"
  - Registrar en CSV y volver a lista (sin tocar SEO)

#### 4.3 Generar con IA (Title, Desc, Keywords)
A partir del texto:
1.  **Título SEO**: crear un título optimizado (~50-60 chars) usando el nombre del producto y detalles clave.
2.  **Descripción SEO**: resumir el texto en una frase atractiva (140-160 chars).
3.  **Keywords**: lista de 8–15 keywords (minúsculas, deduplicadas).

(Se puede usar `scripts/normalize_keywords.py` si se ha generado una lista con comas.)

### 5) Abrir la página web del producto
En la ficha del producto:
- Pulsar **“Ir a sitio web”** (smart button que se ve arriba en tu captura).
Esto abre la página `/shop/<slug>-<id>` del producto.

Capturar `website_slug`:
- Si es visible en la barra de direcciones, guardar la URL o el path `/shop/...` para el reporte.

### 6) Abrir y editar “Optimizar SEO” (modal)
En la página web del producto:
- Abrir menú superior **“Sitio”**
- Click **“Optimizar SEO”**
Se abre el modal con:
- **Título** (input)
- **Descripción** (textarea)
- **Palabras clave** (input + botón “Añadir”)
- Botón **Guardar**

### 7) Rellenar campos (Title, Description, Keywords)

#### 7.1 Título y Descripción
- Escribir el **Título SEO** generado en el campo "Título".
- Escribir la **Descripción SEO** generada en el campo "Descripción".

#### 7.2 Palabras clave (IMPORTANTÍSIMO: tags uno a uno)
El campo “Palabras clave” de tu captura funciona por **tags**:
- Escribir 1 keyword en el input (sin comas)
- Pulsar **“Añadir”**
- Repetir para cada keyword

Regla de mezcla:
- Si ya hay tags existentes:
  - Mantenerlos y solo añadir los nuevos que no existan.
- Objetivo: que queden 8–15 tags finales.

Si el input permite Enter (a veces Odoo lo permite):
- Enter puede sustituir a “Añadir”, pero por defecto usar “Añadir” (más fiable).

### 8) Guardar SEO
- Pulsar **Guardar** en el modal.
- Confirmar que el modal se cierra y no hay errores.

### 9) Reporte
- status = OK
- notes = "seo saved" o "merged existing keywords" si había.

Registrar:
`python scripts/append_report_csv.py "<product_name>" "<product_ref>" "<website_slug>" "<meta_title>" "<meta_description>" "<kw1, kw2, ...>" "OK" "<notes>"`

> **IMPORTANTE**: Tras registrar, avanzar al siguiente producto usando la flecha "Siguiente" del formulario backend.

## Manejo de errores
- Si no aparece “Optimizar SEO”:
  - status = ERROR
  - notes = "Optimizar SEO not available"
  - Registrar y continuar con siguiente producto.
- Si “Ir a sitio web” no abre (popups):
  - abrir manualmente en misma pestaña y continuar.
- Si hay multiwebsite/idiomas:
  - no cambiar configuraciones; trabajar con el website activo.

## Restricciones
- No cambiar precios, nombre del producto (en backend), categorías, imágenes ni publicación.
- Solo modificar el SEO (Title, Description, Keywords) en el frontend.

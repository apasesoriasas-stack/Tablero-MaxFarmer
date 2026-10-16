# Tablero de planificación de importaciones avícolas (Streamlit)

Max Farmer S.A.S. · 16 SKU Clase A · Pronóstico a 3 meses · Modelo vigente: SES

## Archivos
- `app.py`: el tablero (4 vistas: Resumen, Pronóstico y reposición, Precisión del modelo, Calidad de datos y quiebres).
- `data/resultados.json`: resultados calculados en Colab (ventas 2023-2025, pronóstico SES, WAPE/Bias/MASE por modelo, stock reconstruido y quiebres).
- `requirements.txt`: librerías necesarias.

## Ejecutar en tu computadora
```
pip install -r requirements.txt
streamlit run app.py
```

## Publicar con un link (gratis)
1. Crea una cuenta en github.com y un repositorio nuevo (puede ser privado).
2. Sube los archivos de esta carpeta, manteniendo la carpeta `data/`.
3. Entra a share.streamlit.io, inicia sesión con GitHub y elige "Create app".
4. Selecciona el repositorio, la rama `main` y el archivo `app.py`. Pulsa "Deploy".
5. Obtendrás un link del tipo `https://<nombre>.streamlit.app` para compartir.

## Actualizar cada mes
Vuelve a correr el Colab con los datos nuevos, exporta `resultados.json` con la misma estructura y reemplázalo en `data/`. El tablero recalcula cobertura, stock de seguridad, pedido sugerido y semáforo automáticamente.

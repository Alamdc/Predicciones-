# Sistema Predictivo de Flujo de Efectivo (Demo)

Aplicación web modular construida con **Streamlit** diseñada para gestionar el ciclo de vida completo de los datos financieros: desde la extracción y limpieza (ETL), hasta el entrenamiento de modelos predictivos y la automatización de tareas para la ayuda del traslado de efectivo entre sucursales de la financiera.

Este proyecto sirve como un entorno de pruebas (sandbox) para la implementación de predicciones de flujo de efectivo utilizando algoritmos de Machine Learning, optimizando la logística de distribución de recursos.

## Tecnologías Principales
* **Frontend / UI:** Streamlit
* **Machine Learning:** XGBoost, Scikit-Learn
* **Bases de Datos:** PostgreSQL, SQLite (Jobstore)
* **Automatización:** APScheduler (Cron jobs)
* **Procesamiento de Datos:** Pandas, NumPy

---

## Características Principales

### 1. Pipeline ETL y Preprocesamiento
* Conexión segura a bases de datos PostgreSQL.
* Limpieza automatizada de datos históricos financieros y aplicación de filtros parametrizables.
* Ingeniería de características (Feature Engineering): creación de variables temporales, generación de rezagos (*lags*) y cálculo de medias móviles.
* Carga de datos limpios a la base de datos destino mediante estrategias de inserción eficientes.

### 2. Modelado Predictivo (XGBoost)
* Interfaz de usuario para configurar y entrenar modelos de series temporales.
* Soporte para múltiples estrategias de entrenamiento: **Global** (un modelo general) o **Localizada** (un modelo por cada sucursal/entidad).
* Ajuste de hiperparámetros (learning rate, max depth, etc.) y manejo de valores atípicos (winsorización).
* Generación de métricas de validación (RMSE) y exportación de pronósticos.

### 3. Asignación y Optimización de Recursos
* Módulo para calcular rangos operativos y definir transferencias óptimas de efectivo basadas en el pronóstico generado y el histórico reciente.

### 4. Automatización de Tareas (Scheduler)
* Sistema integrado para programar la ejecución recurrente de pipelines de datos (ej. actualizaciones semanales).
* Gestión de tareas mediante un almacén persistente (SQLite) que permite ejecutar, visualizar o eliminar *jobs* programados.

---

## Estructura del Proyecto (Arquitectura Modular)
El código sigue buenas prácticas de ingeniería de software, separando la interfaz de usuario de la lógica de negocio:

* `app.py`: Punto de entrada principal de la aplicación.
* `pages/`: Vistas independientes del dashboard (ML, ETL, Programación).
* `src/clean/`: Lógica de limpieza, preparación de datos y programación de tareas.
* `src/xgb/`: Pipeline de Machine Learning, ingeniería de características y entrenamiento.
* `src/db/`: Gestión de conexiones seguras a la base de datos.
* `src/rangos/`: Lógica de optimización y asignación de recursos.

---


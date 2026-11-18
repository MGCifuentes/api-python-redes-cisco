# API REST del Network Controller con Python (Grupo 09)

Repositorio del **Grupo 09** para el TP N° 4 integrador de **Redes de Computadoras (3643)**, UNLaM, 2° cuatrimestre 2026.
Es un fork de [redes-computadoras/api-python-redes-cisco](https://github.com/redes-computadoras/api-python-redes-cisco):
tiene los scripts que dio la cátedra y suma el script propio del grupo, `05_inventario_csv.py`.

Los scripts usan la API Northbound del Network Controller de Cisco Packet Tracer. Para que la API se vea desde la PC hay
que habilitar el acceso externo del controlador; queda en `http://localhost:58000/api/v1`.

## Qué hace cada script

| Script | Endpoint | Qué hace |
|---|---|---|
| `src/01_get-ticket.py` | `POST /ticket` | Se autentica con el usuario del controlador y muestra el *service ticket* (el token que va en el header `X-Auth-Token`). |
| `src/02_get-network-device.py` | `GET /network-device` | Lista los equipos de red que administra el controlador: hostname, plataforma e IP de gestión. Usa un ticket escrito en el código. |
| `src/03_get-host.py` | `GET /host` | Lista los hosts que ve el controlador: IP, MAC y el switch y puerto donde están conectados. Usa un ticket escrito en el código. |
| `src/04_tabulate.py` | `POST /ticket` y `GET /network-device` | Pide el ticket solo y muestra los equipos en una tabla con `tabulate`. |
| `src/05_inventario_csv.py` | `POST /ticket`, `GET /network-device`, `GET /host`, `DELETE /ticket/{ticket}` | **Script propio.** Arma un inventario único de equipos y hosts, lo exporta a `inventario.csv` y muestra un resumen. Ver abajo. |

### Script propio: `05_inventario_csv.py`

Junta en una sola tabla todo lo que ve el controlador y la exporta a CSV (separado por `;`, se abre directo con Excel o
LibreOffice). Columnas: `tipo`, `nombre`, `ip`, `mac`, `serie`, `plataforma`, `estado`, `switch`, `puerto`.

Qué le agrega a los scripts suministrados:

- **Maneja la sesión completa:** pide el ticket solo y al terminar lo cierra con `DELETE /ticket/{ticket}`.
- **No se corta con equipos sin hostname.** `02_get-network-device.py` y `04_tabulate.py` fallan con
  `KeyError: 'hostname'` cuando el inventario incluye un equipo que el controlador no administra (en nuestra topología,
  el router del ISP, que figura como *Wrong credential*). El script propio lo lista como `(sin hostname)`.
- **Une equipos y hosts** en un mismo archivo, con el estado de cada equipo (*Managed* o no) y si cada host responde al ping.
- **Descarta hosts repetidos:** el controlador conserva entradas viejas de un mismo host cuando renueva su IP por DHCP;
  el script deja una por MAC.
- **No tiene credenciales en el código:** las lee de las variables de entorno `NC_USER` y `NC_PASS` o de un archivo
  `.env`, que el `.gitignore` excluye del repositorio.

Uso:

```bash
cp .env.example .env        # en Windows: copy .env.example .env
# completar NC_USER y NC_PASS en .env con el usuario del Network Controller
cd src
python 05_inventario_csv.py               # genera inventario.csv
python 05_inventario_csv.py otro.csv      # o con otro nombre
```

Salida de ejemplo (resumen final):

```
Equipos de red: 10 (9 Managed, 1 Wrong credential)
Hosts: 9 (9 responden al ping); se descartaron 3 entrada(s) repetida(s)
Inventario exportado a ...\src\inventario.csv
```

Si la API no está en la URL por defecto, se puede definir `NC_URL` (por ejemplo `NC_URL=http://localhost:58000/api/v1`).

## Antes de ejecutar los scripts de la cátedra

- **Credenciales:** `01_get-ticket.py` y `04_tabulate.py` usan el usuario `cisco` y la clave `cisco123!`. Si en el
  Network Controller se creó otro usuario, hay que cambiarlos en esos dos archivos.
- **Ticket:** `02_get-network-device.py` y `03_get-host.py` traen escrito un ticket de ejemplo que no sirve en otro
  Packet Tracer, porque el controlador genera uno nuevo en cada sesión y vence. Ejecutar primero `01_get-ticket.py`,
  copiar el ticket que muestra y reemplazarlo en el header `X-Auth-Token` de esos dos scripts. `04_tabulate.py` y
  `05_inventario_csv.py` no necesitan este paso: piden el ticket solos.

## Entorno virtual de Python

1. **Clonar el proyecto**

   ```bash
   git clone https://github.com/MGCifuentes/api-python-redes-cisco
   cd api-python-redes-cisco
   ```

2. **Crear el entorno virtual** (por ejemplo, con el nombre `cisco`)

   ```bash
   python3 -m venv cisco
   source cisco/bin/activate        # Linux
   cisco\Scripts\activate           # Windows
   ```

3. **Instalar las dependencias** (`requests` y `tabulate`)

   ```bash
   pip install -r requirements.txt
   ```

4. **Elegir el intérprete** del entorno virtual en VS Code (*Python: Select Interpreter* → `cisco`).

5. **Desactivar el entorno** al terminar: `deactivate`.

La carpeta del entorno virtual, el archivo `.env` y el `inventario.csv` generado no se suben al repositorio: están en
el `.gitignore`.

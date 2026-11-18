"""
05_inventario_csv.py - Script propio del Grupo 09 (TP N° 4, Redes de Computadoras 3643).

Arma un inventario unico con todo lo que ve el Network Controller de Packet Tracer:
los equipos de red (GET /network-device) y los hosts (GET /host). Lo exporta a
inventario.csv y muestra un resumen por pantalla.

Que agrega respecto de los scripts suministrados:
  - Pide el ticket solo (POST /ticket) y al terminar cierra la sesion (DELETE /ticket/{ticket}).
  - No se corta con equipos sin hostname (por ejemplo el ISP, que el controlador no administra
    y aparece como "Wrong credential"): 02_get-network-device.py y 04_tabulate.py fallan ahi con
    KeyError: 'hostname'.
  - Une equipos y hosts en una sola tabla y la exporta a CSV (se abre con Excel o LibreOffice).
  - No tiene credenciales en el codigo: las lee de las variables de entorno NC_USER y NC_PASS,
    o de un archivo .env (que el .gitignore excluye del repositorio).

Uso:
    python 05_inventario_csv.py                 # escribe inventario.csv en la carpeta actual
    python 05_inventario_csv.py salida.csv      # elige el nombre del archivo

Variables opcionales:
    NC_URL   URL base de la API (por defecto http://localhost:58000/api/v1)
"""

import csv
import os
import sys
from collections import Counter
from pathlib import Path

import requests
from tabulate import tabulate

requests.packages.urllib3.disable_warnings()

COLUMNAS = ["tipo", "nombre", "ip", "mac", "serie", "plataforma", "estado", "switch", "puerto"]


def cargar_env():
    """Carga NC_USER, NC_PASS y NC_URL desde un archivo .env si no estan en el entorno."""
    for carpeta in (Path.cwd(), Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent):
        archivo = carpeta / ".env"
        if not archivo.is_file():
            continue
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))
        break


def pedir_ticket(base, usuario, clave):
    r = requests.post(f"{base}/ticket", json={"username": usuario, "password": clave},
                      headers={"Content-Type": "application/json"}, verify=False, timeout=15)
    print(f"POST /ticket -> {r.status_code}")
    r.raise_for_status()
    return r.json()["response"]["serviceTicket"]


def cerrar_ticket(base, ticket):
    # El controlador de Packet Tracer devuelve 500 si el DELETE no lleva Content-Type.
    r = requests.delete(f"{base}/ticket/{ticket}",
                        headers={"X-Auth-Token": ticket, "Content-Type": "application/json"},
                        verify=False, timeout=15)
    print(f"DELETE /ticket -> {r.status_code}")


def obtener(base, ticket, recurso):
    r = requests.get(f"{base}/{recurso}", headers={"X-Auth-Token": ticket}, verify=False, timeout=15)
    print(f"GET /{recurso} -> {r.status_code}")
    r.raise_for_status()
    return r.json().get("response", [])


def fila_equipo(d):
    return {
        "tipo": d.get("type") or "sin administrar",
        "nombre": d.get("hostname") or "(sin hostname)",
        "ip": d.get("managementIpAddress", ""),
        "mac": d.get("macAddress", ""),
        "serie": d.get("serialNumber", ""),
        "plataforma": d.get("productId") or d.get("platformId", ""),
        "estado": d.get("collectionStatus") or d.get("inventoryStatusDetail", ""),
        "switch": "",
        "puerto": "",
    }


def fila_host(h):
    return {
        "tipo": f"Host ({h.get('hostType', '')})",
        "nombre": h.get("hostName") or "(sin nombre)",
        "ip": h.get("hostIp", ""),
        "mac": h.get("hostMac", ""),
        "serie": "",
        "plataforma": "",
        "estado": "Ping OK" if h.get("pingStatus") == "SUCCESS" else h.get("pingStatus", ""),
        "switch": h.get("connectedNetworkDeviceName", ""),
        "puerto": h.get("connectedInterfaceName", ""),
    }


def main():
    cargar_env()
    base = os.environ.get("NC_URL", "http://localhost:58000/api/v1").rstrip("/")
    usuario, clave = os.environ.get("NC_USER"), os.environ.get("NC_PASS")
    if not usuario or not clave:
        sys.exit("Faltan NC_USER y NC_PASS: definilas como variables de entorno o en un archivo .env "
                 "(ver .env.example).")
    salida = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("inventario.csv")

    ticket = pedir_ticket(base, usuario, clave)
    try:
        equipos = [fila_equipo(d) for d in obtener(base, ticket, "network-device")]
        crudos = obtener(base, ticket, "host")
    finally:
        cerrar_ticket(base, ticket)

    # El controlador conserva entradas viejas de un mismo host (por ejemplo cuando renovo su IP
    # por DHCP): se deja una sola por MAC, la ultima que informa el controlador.
    por_mac = {}
    for h in crudos:
        por_mac[h.get("hostMac") or id(h)] = h
    hosts = [fila_host(h) for h in por_mac.values()]
    repetidos = len(crudos) - len(hosts)

    equipos.sort(key=lambda f: (f["nombre"] == "(sin hostname)", f["nombre"]))
    hosts.sort(key=lambda f: (f["switch"], f["nombre"]))
    filas = equipos + hosts

    with salida.open("w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS, delimiter=";")
        escritor.writeheader()
        escritor.writerows(filas)

    print()
    print(tabulate([[f[c] for c in COLUMNAS] for f in filas], headers=COLUMNAS, tablefmt="simple"))
    estados = Counter(e["estado"] for e in equipos)
    print()
    print(f"Equipos de red: {len(equipos)} (" + ", ".join(f"{n} {e}" for e, n in estados.items()) + ")")
    print(f"Hosts: {len(hosts)} ({sum(h['estado'] == 'Ping OK' for h in hosts)} responden al ping)"
          + (f"; se descartaron {repetidos} entrada(s) repetida(s)" if repetidos else ""))
    print(f"Inventario exportado a {salida.resolve()}")


if __name__ == "__main__":
    main()

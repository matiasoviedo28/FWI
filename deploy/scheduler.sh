#!/usr/bin/env sh
# Scheduler simple del pipeline: corre una vez al arranque y después cada 24h.
# (Alternativa a un cron del sistema; mantiene el contenedor autónomo.)
set -eu

INTERVALO="${FWI_INTERVALO_SEG:-86400}"   # 24h por defecto

while true; do
  echo "[scheduler] $(date -u +%FT%TZ) ejecutando pipeline..."
  python -m pipeline.run || echo "[scheduler] el pipeline falló; reintenta en el próximo ciclo"
  echo "[scheduler] durmiendo ${INTERVALO}s"
  sleep "${INTERVALO}"
done

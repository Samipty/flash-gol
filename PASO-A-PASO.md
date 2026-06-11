# ✅ Paso a paso — World Cup Shorts (stack casi gratis)

Solo Claude cuesta (pago por uso). Todo lo demás es gratis. El Mundial empieza
el **11 de junio**: prioriza las fases 1 a 4.

---

## Fase 1 — Preparar la máquina
- [ ] Instalar **Python 3.11+**
- [ ] Instalar **ffmpeg** (Mac: `brew install ffmpeg` · Linux: `sudo apt install ffmpeg` · Windows: ffmpeg.org + PATH)
- [ ] Descomprimir el proyecto y abrir la terminal en `sports-shorts`
- [ ] `pip install -r requirements.txt`

## Fase 2 — Voz gratis (Piper)
- [ ] Confirmar que el comando `piper` quedó instalado (`piper --help`)
- [ ] Descargar una voz en español de https://huggingface.co/rhasspy/piper-voices (los DOS archivos: `.onnx` y `.onnx.json`)
- [ ] Ponerlos en la carpeta `models/`
- [ ] Apuntar `PIPER_MODEL` en `.env` al archivo `.onnx`

## Fase 3 — Datos gratis (football-data.org)
- [ ] Crear cuenta gratis en football-data.org y copiar el **token** (X-Auth-Token)
- [ ] Confirmar que la competición **WC** (Mundial) aparece en tu plan gratis

## Fase 4 — Claude (lo único de pago)
- [ ] Crear **API key** en console.anthropic.com
- [ ] Activar el **web search tool** para tu organización en la consola

## Fase 5 — YouTube (gratis, pero laborioso)
- [ ] En Google Cloud Console: crear proyecto y habilitar **YouTube Data API v3**
- [ ] Crear credenciales **OAuth client ID** tipo **Desktop**, descargar el JSON a `state/yt_client_secret.json`
- [ ] Correr `python -m pipeline.upload` → autorizar en el navegador → se crea `state/yt_token.json`

## Fase 6 — Configurar
- [ ] `cp .env.example .env` y pegar `ANTHROPIC_API_KEY`, `SPORTS_API_KEY` (token football-data), `PIPER_MODEL`
- [ ] En `config.py` revisar la watchlist y dejar `YT_PRIVACY = "private"`

## Fase 7 — Probar (sin gastar casi nada)
- [ ] `python main.py --dry-run` → revisar el guión (preview y, ya empezado el Mundial, recap)
- [ ] Cuando convenza, `python main.py` (real, en private) y revisar el `.mp4` en `output/`

## Fase 8 — Automatizar
- [ ] Subir a un repo **público** de GitHub (Actions gratis ilimitado) — o usar cron local
- [ ] Si usas Actions, configurar Secrets: `ANTHROPIC_API_KEY`, `SPORTS_API_KEY`, `YT_TOKEN`, `PIPER_MODEL_URL`, `PIPER_MODEL_JSON_URL`
- [ ] Vigilar las primeras corridas; cuando todo esté bien, cambiar `YT_PRIVACY` a `"public"`

---

## 💸 Costos (verificado jun 2026)

| Servicio | Costo |
|---|---|
| **Claude API** (cerebro + búsqueda web) | ~$0.20–$0.40 por Short, pago por uso |
| football-data.org (datos) | Gratis (Mundial incluido en el tier free) |
| Piper (voz, local) | Gratis |
| Pillow + ffmpeg (imágenes/video) | Gratis |
| YouTube Data API (publicar) | Gratis |
| GitHub Actions (repo público) o cron local | Gratis |

**Total real = solo lo que consuma Claude.** Con la watchlist curada, son unos pocos
dólares durante todo el Mundial. Para bajarlo aún más: reduce `MAX_SHORTS_PER_DAY`.

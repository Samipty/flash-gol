# ⚽ World Cup Shorts — pipeline automatizado

Cubre el Mundial 2026 (11 jun – 19 jul) en dos modos:
- **Preview** antes del partido: quién lleva la ventaja y por qué, con datos relevantes.
- **Recap** después: marcador, goleadores, punto de quiebre e implicaciones.

Un partido genera 2 Shorts (antes y después), con dedupe separado.

## Proveedores intercambiables
Cambia entre opciones con flags en `.env`:

| Pieza | Opción A | Opción B |
|---|---|---|
| Cerebro (`LLM_PROVIDER`) | `claude` (pago, con búsqueda web) | `gemini` / `groq` / `ollama` (gratis) |
| Datos (`DATA_PROVIDER`) | `api_sports` (datos completos) | `football_data` (gratis) |
| Voz (`TTS_PROVIDER`) | `elevenlabs` (voz natural) | `piper` (local, gratis) |

Solo Claude trae búsqueda web integrada. Con un cerebro gratis (Gemini), el guión
se escribe a partir de los datos reales de API-Sports (lesiones en el preview,
goleadores en el recap) más conocimiento general — por eso conviene tener
`DATA_PROVIDER=api_sports` cuando uses un LLM gratis.

### Usar Gemini ahora y cambiar a Claude después
Hoy (sin la llave de Claude):
```
LLM_PROVIDER=gemini
GEMINI_API_KEY=...        # gratis en https://aistudio.google.com/apikey
```
Cuando tengas saldo en Claude, solo cambia:
```
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
```
Nada más cambia. (Ojo: el tier gratis de Gemini tiene límites diarios; si ves
errores 429, baja `MAX_SHORTS_PER_DAY` o espera al reset.)

## Arquitectura
```
main.py  (orquestador: preview + recap por corrida)
   ├─ pipeline/matches.py   1) partidos próximos + terminados → API-Sports / football-data
   ├─ pipeline/research.py  2) investiga + escribe guión        → Claude API + web_search
   ├─ pipeline/voice.py     3) locución                         → ElevenLabs / Piper
   ├─ pipeline/visuals.py   4) tarjetas (incl. scoreboard)      → Pillow
   ├─ pipeline/video.py     5) arma el video 9:16               → ffmpeg
   └─ pipeline/upload.py    6) publica el Short                 → YouTube Data API
```

## Qué cambia con el stack de pago (API-Sports + ElevenLabs)
- **Recap más confiable**: API-Sports entrega goleadores y minutos reales, así que el
  recap no depende de la búsqueda web para el marcador (Claude la usa solo para contexto).
- **Preview más rico**: hay datos reales de lesiones/alineaciones disponibles.
- **Voz natural**: ElevenLabs en lugar de la voz local de Piper.
- **Costo**: ahora pagas API-Sports + crédito de ElevenLabs + uso de Claude.

## Puesta en marcha
```bash
pip install -r requirements.txt
sudo apt-get install -y ffmpeg          # (o brew install ffmpeg)
cp .env.example .env                    # pega ANTHROPIC_API_KEY, APISPORTS_KEY, ELEVENLABS_API_KEY, TTS_VOICE_ID
python -m pipeline.upload               # autoriza YouTube una vez
```
En ElevenLabs, copia el **voice id** de la voz que elijas (idealmente una en español) a `TTS_VOICE_ID`.

## Correr
```bash
python main.py --dry-run   # investiga e imprime el guión, sin voz ni publicación
python main.py             # corrida real (en private mientras pruebas)
```

## Volver al modo gratis
Si se agota el crédito de ElevenLabs o el plan de API-Sports:
```
DATA_PROVIDER=football_data
TTS_PROVIDER=piper
```
y agrega `FOOTBALLDATA_TOKEN`, instala `pip install piper-tts` y descarga una voz (abajo).

### Voces en español para Piper (solo si usas el fallback gratis)
Cada voz necesita el `.onnx` y el `.onnx.json`. Recomendada: **es_MX-claude-high**.
```bash
curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_MX/claude/high/es_MX-claude-high.onnx" -o models/es_MX-claude-high.onnx
curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_MX/claude/high/es_MX-claude-high.onnx.json" -o models/es_MX-claude-high.onnx.json
```
Otras: es_MX-ald-medium, es_AR-daniela-high, es_ES-davefx-medium, es_ES-sharvard-medium
(prefijo `https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/`).

## Automatización
- **Cron local**: `0 * * * *  cd /ruta && python3 main.py >> run.log 2>&1`
- **GitHub Actions** (incluido): repo público = gratis. Secrets: `ANTHROPIC_API_KEY`,
  `APISPORTS_KEY`, `ELEVENLABS_API_KEY`, `TTS_VOICE_ID`, `YT_TOKEN`.

## Notas
- Verifica que tu plan de API-Sports incluya el Mundial (league `1`, season `2026`).
- No uses fotos/clips con copyright: solo gráficos generados.
- YouTube restringe el contenido en masa para monetización; mantén la watchlist curada
  y aporta tu propio ángulo.

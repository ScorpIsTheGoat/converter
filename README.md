# converter
## Idee
In diesem Projekt ist das Ziel darin, eine über das Internet zugängliche Website zu erstellen, auf der der Benutzer:
- convert video codecs (example: H.264 --> DNxHD) 
- convert data types (example: mp4 --> mov)
- add subtitles (creation of srt file, aswell as inbedding in video)
- upscaling of video/picutres (example: from HD to 4K)
- colorgrading of video (example: darker, higher contrast)
## Requirements
Das FrontEnd werde ich standard mässig mit HTML, CSS und JavaScript programmieren, beim BackEnd benutzte ich FastAPI, ein Framework für Python, welches einfach zu benutzten ist. Für die konvertierung bietet sich ffmpeg-python an, damit habe ich bereits Erfahrung. Für die Untertitel und das ColorGrading/Upscaling werde ich Open-AI verwenden. Falls möglich würde ich die erstellten Benutzer in einer SQL-Datenbank speichern.
## Nächste Schritte
1. Konvertierung der Hochgeladenen Videos und das zurück senden an FrontEnd(Hochladen funktioniert schon)
2. Implementierung eines Ladebalkens
3. User-Login erstellen
4. ColorGrading/Untertitel implementieren


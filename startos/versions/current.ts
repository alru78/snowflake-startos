import { IMPOSSIBLE, VersionInfo } from '@start9labs/start-sdk'

export const current = VersionInfo.of({
  version: '2.14.1:5',
  releaseNotes: {
    en_US: `Redesigned dashboard: rolling 24-hour and 7-day bandwidth with trends and a down/up split, live uptime in the status line, daily average and all-time sparklines, peak throughput, and a weekday-by-hour activity heatmap.`,
    es_ES: `Panel rediseñado: ancho de banda de las últimas 24 horas y 7 días con tendencias y desglose de bajada/subida, tiempo de actividad en vivo en la barra de estado, promedio diario y totales con minigráficos, rendimiento máximo y un mapa de calor de actividad por día y hora.`,
    de_DE: `Neu gestaltetes Dashboard: rollierende Bandbreite der letzten 24 Stunden und 7 Tage mit Trends und Aufteilung nach Down-/Upload, Live-Laufzeit in der Statuszeile, Tagesdurchschnitt und Gesamtwerte mit Sparklines, Spitzendurchsatz und eine Aktivitäts-Heatmap nach Wochentag und Stunde.`,
    pl_PL: `Przeprojektowany panel: przepustowość z ostatnich 24 godzin i 7 dni z trendami i podziałem na pobieranie/wysyłanie, czas działania na żywo w pasku stanu, średnia dzienna i sumy z wykresami, szczytowa przepustowość oraz mapa cieplna aktywności według dnia tygodnia i godziny.`,
    fr_FR: `Tableau de bord repensé : bande passante glissante sur 24 heures et 7 jours avec tendances et répartition descendante/montante, durée de fonctionnement en direct dans la barre d'état, moyenne quotidienne et totaux avec mini-graphiques, débit maximal et carte thermique de l'activité par jour et par heure.`,
  },
  migrations: {
    up: async ({ effects }) => {},
    down: IMPOSSIBLE,
  },
})

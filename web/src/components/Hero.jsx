import { Link } from 'react-router-dom'

export default function Hero({ summary }) {
  const s = summary || {}
  return (
    <section className="hero">
      <div className="container">
        <h1>
          Análisis de datos<br />
          <span className="accent">Mundial Qatar 2022</span>
        </h1>
        <p className="lead">
          Un pipeline completo de analítica de fútbol profesional sobre los datos
          abiertos de StatsBomb: desde el ETL y la base de datos hasta KPIs, un
          modelo propio de goles esperados (xG), scouting por percentiles y
          monitoreo de carga física. Explorá los resultados de forma interactiva.
        </p>
        <div className="hero-cta">
          <Link className="btn btn-gold" to="/tiros">🎯 Explorar mapa de tiros</Link>
          <Link className="btn btn-ghost" to="/kpis">📊 Ver KPIs</Link>
          <a className="btn btn-ghost" href="https://github.com/oyar23/futbol-analytics"
             target="_blank" rel="noreferrer">⤳ Código en GitHub</a>
        </div>

        <div className="hero-stats">
          <div className="hero-stat"><div className="num">{s.matches ?? '—'}</div><div className="lbl">Partidos analizados</div></div>
          <div className="hero-stat"><div className="num">{s.shots?.toLocaleString?.() ?? '—'}</div><div className="lbl">Tiros procesados</div></div>
          <div className="hero-stat"><div className="num">{s.goals ?? '—'}</div><div className="lbl">Goles en juego</div></div>
          <div className="hero-stat"><div className="num">{s.players?.toLocaleString?.() ?? '—'}</div><div className="lbl">Jugadores</div></div>
        </div>
      </div>
    </section>
  )
}

import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip,
  CartesianGrid, ReferenceLine, LabelList,
} from 'recharts'
import Hero from '../components/Hero.jsx'
import { SectionHead, BarRanking } from '../components/ui.jsx'
import { Loader, ErrorBox } from '../components/Loader.jsx'
import { useJSON, shortName, fmt } from '../lib/data.js'

const FEATURES = [
  { ico: '🧱', t: 'ETL + Base de datos', d: 'Descarga reproducible de StatsBomb, normalización a tablas y carga en SQLite con claves e índices.' },
  { ico: '📊', t: 'KPIs e indicadores', d: 'Métricas de equipo y jugador (goles, xG, asistencias, % de pase) calculadas con SQL.' },
  { ico: '🎯', t: 'Mapa de tiros interactivo', d: 'Ubicación de cada tiro con hover: jugador, minuto, xG y desenlace. Filtros por equipo y jugador.' },
  { ico: '🤖', t: 'Modelo de xG propio', d: 'Goles esperados con scikit-learn. ROC-AUC 0.80 y correlación 0.89 con el xG oficial de StatsBomb.' },
  { ico: '🔍', t: 'Scouting por percentiles', d: 'Comparación de jugadores por radar dentro de su posición (GK/DEF/MID/FWD).' },
  { ico: '🏃', t: 'Carga física (ACWR)', d: 'Monitoreo de carga y alertas de riesgo de lesión (datos simulados, demo metodológica).' },
]

function ScatterTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="tooltip-box">
      <div className="t-name">{d.team_name}</div>
      <div className="t-row">xG: {fmt(d.xg)} · Goles: {d.goals}</div>
    </div>
  )
}

export default function Home() {
  const { loading, error, data } = useJSON(['summary', 'player_kpis', 'team_kpis'])
  if (loading) return <Loader />
  if (error) return <ErrorBox error={error} />
  const [summary, players, teams] = data

  const topScorers = [...players].sort((a, b) => b.goals - a.goals).slice(0, 10)
  const maxAxis = Math.max(...teams.map((t) => Math.max(t.xg, t.goals))) + 1

  return (
    <>
      <Hero summary={summary} />

      <div className="container">
        <section className="section">
          <SectionHead
            title="¿Qué vas a encontrar en este proyecto?"
            subtitle="Un recorrido end-to-end del trabajo de un analista de datos en el fútbol."
          />
          <div className="grid grid-3">
            {FEATURES.map((f) => (
              <div className="feature" key={f.t}>
                <div className="ico">{f.ico}</div>
                <h3>{f.t}</h3>
                <p>{f.d}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="section">
          <div className="grid grid-2">
            <div className="card">
              <h3>Top 10 goleadores</h3>
              <BarRanking data={topScorers} valueKey="goals" labelKey="player_name" color="#7a1230" />
            </div>
            <div className="card">
              <h3>xG total vs goles reales (por equipo)</h3>
              <ResponsiveContainer width="100%" height={340}>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 30, left: 0 }}>
                  <CartesianGrid stroke="#eee" />
                  <XAxis type="number" dataKey="xg" name="xG" domain={[0, maxAxis]}
                         tick={{ fontSize: 12 }}
                         label={{ value: 'xG total', position: 'bottom', fontSize: 12 }} />
                  <YAxis type="number" dataKey="goals" name="Goles" domain={[0, maxAxis]}
                         tick={{ fontSize: 12 }}
                         label={{ value: 'Goles', angle: -90, position: 'insideLeft', fontSize: 12 }} />
                  <ZAxis range={[60, 60]} />
                  <ReferenceLine segment={[{ x: 0, y: 0 }, { x: maxAxis, y: maxAxis }]}
                                 stroke="#c8a23c" strokeDasharray="5 5" />
                  <Tooltip content={<ScatterTooltip />} />
                  <Scatter data={teams} fill="#7a1230">
                    <LabelList dataKey="team_name" position="top" fontSize={9}
                               formatter={(v) => shortName(v)} />
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>
      </div>
    </>
  )
}

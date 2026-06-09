import { useState } from 'react'
import { SectionHead, BarRanking, DataTable } from '../components/ui.jsx'
import { Loader, ErrorBox } from '../components/Loader.jsx'
import { useJSON, fmt } from '../lib/data.js'

const TEAM_METRICS = [
  { key: 'goals', label: 'Goles' },
  { key: 'shots', label: 'Tiros' },
  { key: 'shots_on_target', label: 'Tiros al arco' },
  { key: 'xg', label: 'xG total' },
  { key: 'passes', label: 'Pases' },
  { key: 'pass_completion_pct', label: '% Pase' },
  { key: 'possession_pct', label: 'Posesión (proxy)' },
]
const PLAYER_METRICS = [
  { key: 'goals', label: 'Goles' },
  { key: 'assists', label: 'Asistencias' },
  { key: 'key_passes', label: 'Pases clave' },
  { key: 'xg', label: 'xG' },
  { key: 'xg_per_90', label: 'xG por 90' },
  { key: 'shots', label: 'Tiros' },
  { key: 'minutes', label: 'Minutos' },
]

export default function Kpis() {
  const { loading, error, data } = useJSON(['team_kpis', 'player_kpis'])
  const [tab, setTab] = useState('teams')
  const [teamMetric, setTeamMetric] = useState('goals')
  const [topN, setTopN] = useState(12)
  const [plMetric, setPlMetric] = useState('goals')
  const [team, setTeam] = useState('(Todos)')
  const [minMin, setMinMin] = useState(180)

  if (loading) return <Loader />
  if (error) return <ErrorBox error={error} />
  const [teams, players] = data

  return (
    <div className="container section">
      <SectionHead title="📊 KPIs de equipos y jugadores"
        subtitle="Indicadores calculados con SQL sobre la base. Usá los filtros para explorar." />

      <div className="tabs">
        <button className={'tab' + (tab === 'teams' ? ' active' : '')} onClick={() => setTab('teams')}>🏳️ Equipos</button>
        <button className={'tab' + (tab === 'players' ? ' active' : '')} onClick={() => setTab('players')}>👤 Jugadores</button>
      </div>

      {tab === 'teams' && (
        <>
          <div className="controls">
            <div className="field">
              <label>Métrica</label>
              <select value={teamMetric} onChange={(e) => setTeamMetric(e.target.value)}>
                {TEAM_METRICS.map((m) => <option key={m.key} value={m.key}>{m.label}</option>)}
              </select>
            </div>
            <div className="field">
              <label>Cantidad de equipos: {topN}</label>
              <input type="range" min="5" max="32" value={topN} onChange={(e) => setTopN(+e.target.value)} />
            </div>
          </div>

          <div className="card" style={{ marginBottom: 18 }}>
            <h3>Equipos por {TEAM_METRICS.find((m) => m.key === teamMetric).label}</h3>
            <BarRanking
              data={[...teams].sort((a, b) => b[teamMetric] - a[teamMetric]).slice(0, topN)}
              valueKey={teamMetric} labelKey="team_name" useShort={false} color="#8a1538" />
          </div>

          <DataTable
            columns={[
              { key: 'team_name', label: 'Equipo' },
              { key: 'goals', label: 'Goles', num: true },
              { key: 'shots', label: 'Tiros', num: true },
              { key: 'shots_on_target', label: 'Al arco', num: true },
              { key: 'xg', label: 'xG', num: true, fmt: (v) => fmt(v) },
              { key: 'pass_completion_pct', label: '% Pase', num: true, fmt: (v) => fmt(v, 1) },
              { key: 'possession_pct', label: 'Posesión', num: true, fmt: (v) => fmt(v, 1) },
            ]}
            rows={[...teams].sort((a, b) => b[teamMetric] - a[teamMetric])}
          />
        </>
      )}

      {tab === 'players' && (
        <>
          <div className="controls">
            <div className="field">
              <label>Equipo</label>
              <select value={team} onChange={(e) => setTeam(e.target.value)}>
                {['(Todos)', ...new Set(players.map((p) => p.team_name).filter(Boolean).sort())]
                  .map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="field">
              <label>Minutos mínimos: {minMin}</label>
              <input type="range" min="0" max="700" step="30" value={minMin} onChange={(e) => setMinMin(+e.target.value)} />
            </div>
            <div className="field">
              <label>Métrica</label>
              <select value={plMetric} onChange={(e) => setPlMetric(e.target.value)}>
                {PLAYER_METRICS.map((m) => <option key={m.key} value={m.key}>{m.label}</option>)}
              </select>
            </div>
          </div>

          {(() => {
            const filtered = players
              .filter((p) => p.minutes >= minMin && (team === '(Todos)' || p.team_name === team))
            const top = [...filtered].sort((a, b) => b[plMetric] - a[plMetric]).slice(0, 12)
            return (
              <>
                <div className="card" style={{ marginBottom: 18 }}>
                  <h3>Jugadores por {PLAYER_METRICS.find((m) => m.key === plMetric).label}</h3>
                  <BarRanking data={top} valueKey={plMetric} labelKey="player_name" color="#7a1230" />
                </div>
                <p style={{ color: 'var(--muted)', fontSize: '.88rem' }}>
                  {filtered.length} jugadores con ≥ {minMin} minutos
                  {team !== '(Todos)' ? ` · ${team}` : ''}
                </p>
                <DataTable
                  columns={[
                    { key: 'player_name', label: 'Jugador' },
                    { key: 'team_name', label: 'Equipo' },
                    { key: 'minutes', label: 'Min', num: true },
                    { key: 'goals', label: 'Goles', num: true },
                    { key: 'assists', label: 'Asist.', num: true },
                    { key: 'key_passes', label: 'P. clave', num: true },
                    { key: 'xg', label: 'xG', num: true, fmt: (v) => fmt(v) },
                    { key: 'xg_per_90', label: 'xG/90', num: true, fmt: (v) => fmt(v) },
                  ]}
                  rows={[...filtered].sort((a, b) => b[plMetric] - a[plMetric]).slice(0, 60)}
                />
              </>
            )
          })()}
        </>
      )}
    </div>
  )
}

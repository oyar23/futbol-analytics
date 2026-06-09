import { useState, useEffect, useMemo } from 'react'
import {
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Legend, Tooltip,
} from 'recharts'
import { SectionHead, DataTable } from '../components/ui.jsx'
import { Loader, ErrorBox } from '../components/Loader.jsx'
import { useJSON } from '../lib/data.js'

const METRICS = [
  ['xg_per90_pct', 'xG / 90'],
  ['shots_per90_pct', 'Tiros / 90'],
  ['key_passes_per90_pct', 'Pases clave / 90'],
  ['passes_per90_pct', 'Pases / 90'],
  ['pass_completion_pct_pct', '% Pase'],
  ['dribbles_per90_pct', 'Regates / 90'],
  ['recoveries_per90_pct', 'Recuperac. / 90'],
  ['def_actions_per90_pct', 'Acc. def. / 90'],
]
const GROUPS = { FWD: 'Delanteros', MID: 'Mediocampistas', DEF: 'Defensores', GK: 'Arqueros' }

function pickDefault(names, contains, fallback) {
  const i = names.findIndex((n) => n.toLowerCase().includes(contains.toLowerCase()))
  return i >= 0 ? names[i] : names[fallback] || names[0]
}

export default function Scouting() {
  const { loading, error, data: pct } = useJSON('scouting_percentiles')
  const [group, setGroup] = useState('FWD')
  const [a, setA] = useState(null)
  const [b, setB] = useState(null)

  const pool = useMemo(
    () => (pct ? pct.filter((p) => p.position_group === group)
      .sort((x, y) => x.player_name.localeCompare(y.player_name)) : []),
    [pct, group])
  const names = useMemo(() => pool.map((p) => p.player_name), [pool])

  useEffect(() => {
    if (!names.length) return
    if (group === 'FWD') {
      setA(pickDefault(names, 'Mbappé', 0))
      setB(pickDefault(names, 'Messi', 1))
    } else {
      setA(names[0]); setB(names[1] || names[0])
    }
  }, [group, names])

  if (loading) return <Loader />
  if (error) return <ErrorBox error={error} />

  const pa = pool.find((p) => p.player_name === a)
  const pb = pool.find((p) => p.player_name === b)
  const radarData = (pa && pb)
    ? METRICS.map(([col, label]) => ({
        metric: label,
        a: Math.round(pa[col]),
        b: Math.round(pb[col]),
      }))
    : []

  return (
    <div className="container section">
      <SectionHead title="🔍 Scouting — percentiles por posición"
        subtitle="Compará dos jugadores de la misma posición. Los percentiles se calculan dentro de cada grupo (≥ 180 min)." />

      <div className="controls">
        <div className="field">
          <label>Grupo posicional</label>
          <select value={group} onChange={(e) => setGroup(e.target.value)}>
            {Object.entries(GROUPS).map(([k, v]) => <option key={k} value={k}>{k} · {v}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Jugador A</label>
          <select value={a || ''} onChange={(e) => setA(e.target.value)}>
            {names.map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Jugador B</label>
          <select value={b || ''} onChange={(e) => setB(e.target.value)}>
            {names.map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
      </div>

      {pa && pb && (
        <div className="grid grid-2">
          <div className="card">
            <ResponsiveContainer width="100%" height={460}>
              <RadarChart data={radarData} outerRadius="72%">
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
                <PolarRadiusAxis domain={[0, 100]} angle={90} tick={{ fontSize: 9 }} />
                <Radar name={pa.player_name} dataKey="a" stroke="#1f77b4" fill="#1f77b4" fillOpacity={0.35} />
                <Radar name={pb.player_name} dataKey="b" stroke="#c5283d" fill="#c5283d" fillOpacity={0.3} />
                <Legend />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <div className="card">
            <h3>Percentiles comparados</h3>
            <DataTable
              columns={[
                { key: 'metric', label: 'Métrica' },
                { key: 'a', label: pa.player_name.split(' ').slice(-1)[0], num: true },
                { key: 'b', label: pb.player_name.split(' ').slice(-1)[0], num: true },
              ]}
              rows={radarData}
            />
            <p style={{ color: 'var(--muted)', fontSize: '.85rem', marginTop: 10 }}>
              Valores en percentiles (0–100) dentro de {GROUPS[group]} ·
              {pa.player_name} ({pa.team_name}) vs {pb.player_name} ({pb.team_name}).
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

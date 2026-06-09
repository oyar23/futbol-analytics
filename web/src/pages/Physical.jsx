import { useState, useMemo } from 'react'
import {
  ResponsiveContainer, ComposedChart, Bar, Line, LineChart, XAxis, YAxis,
  Tooltip, Legend, CartesianGrid, ReferenceArea, ReferenceLine,
  ScatterChart, Scatter,
} from 'recharts'
import { SectionHead, StatCard, DataTable } from '../components/ui.jsx'
import { Loader, ErrorBox } from '../components/Loader.jsx'
import { useJSON, fmt } from '../lib/data.js'

const dShort = (d) => (d ? String(d).slice(5) : '')

function riskBadge(zone) {
  const cls = zone === 'Riesgo alto' ? 'danger' : zone === 'Precaución' ? 'warn'
    : zone === 'Óptimo' ? 'ok' : 'muted'
  return <span className={`badge ${cls}`}>{zone}</span>
}

function pearson(xs, ys) {
  const n = xs.length
  const mx = xs.reduce((a, v) => a + v, 0) / n
  const my = ys.reduce((a, v) => a + v, 0) / n
  let num = 0, dx = 0, dy = 0
  for (let i = 0; i < n; i++) {
    num += (xs[i] - mx) * (ys[i] - my)
    dx += (xs[i] - mx) ** 2
    dy += (ys[i] - my) ** 2
  }
  return num / Math.sqrt(dx * dy)
}

function XgTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="tooltip-box">
      <div className="t-name">{d.player_name}</div>
      <div className="t-row">{d.team_name} · min {d.minute}</div>
      <div className="t-row">StatsBomb: {fmt(d.statsbomb_xg)} · Modelo: {fmt(d.predicted_xg)}</div>
    </div>
  )
}

export default function Physical() {
  const { loading, error, data } = useJSON(['acwr_series', 'acwr_alerts', 'xg_predictions'])
  const [tab, setTab] = useState('acwr')
  const [player, setPlayer] = useState('Lionel Andrés Messi Cuccittini')

  const series = data?.[0]
  const players = useMemo(
    () => (series ? [...new Set(series.map((s) => s.player_name))].sort() : []),
    [series])

  if (loading) return <Loader />
  if (error) return <ErrorBox error={error} />
  const [, alerts, pred] = data

  const sel = players.includes(player) ? player : players.find((p) => p.includes('Messi')) || players[0]
  const pdata = series.filter((s) => s.player_name === sel)
  const palerts = alerts.filter((s) => s.player_name === sel)
  const highRisk = alerts.filter((s) => s.risk_zone === 'Riesgo alto')

  const m = pred.filter((p) => p.shot_type !== 'Penalty')
  const r = pearson(m.map((p) => p.statsbomb_xg), m.map((p) => p.predicted_xg))

  return (
    <div className="container section">
      <SectionHead title="🏃 Carga física (ACWR) y modelo de xG"
        subtitle="Monitoreo de carga con alertas de riesgo y validación del modelo de goles esperados." />

      <div className="tabs">
        <button className={'tab' + (tab === 'acwr' ? ' active' : '')} onClick={() => setTab('acwr')}>🏃 Carga (ACWR)</button>
        <button className={'tab' + (tab === 'xg' ? ' active' : '')} onClick={() => setTab('xg')}>🤖 Modelo de xG</button>
      </div>

      {tab === 'acwr' && (
        <>
          <div className="note" style={{ marginBottom: 16 }}>
            ⚠️ <b>Datos de carga simulados</b> — StatsBomb no incluye GPS. Es una
            demostración metodológica del monitoreo de carga (ACWR).
          </div>

          <div className="controls">
            <div className="field">
              <label>Jugador</label>
              <select value={sel} onChange={(e) => setPlayer(e.target.value)}>
                {players.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 18 }}>
            <h3>Carga diaria y medias móviles — {sel}</h3>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={pdata} margin={{ top: 6, right: 16, bottom: 6, left: 0 }}>
                <CartesianGrid stroke="#eee" />
                <XAxis dataKey="date" tickFormatter={dShort} tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip labelFormatter={dShort} />
                <Legend />
                <Bar dataKey="load" name="Carga diaria" fill="#b0c4de" />
                <Line dataKey="acute_7d" name="Aguda (7d)" stroke="#1f77b4" dot={false} strokeWidth={2} />
                <Line dataKey="chronic_28d" name="Crónica (28d)" stroke="#2e7d4f" dot={false} strokeWidth={2} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className="card" style={{ marginBottom: 18 }}>
            <h3>ACWR con zonas de riesgo</h3>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={pdata} margin={{ top: 6, right: 16, bottom: 6, left: 0 }}>
                <ReferenceArea y1={0} y2={0.8} fill="#9e9e9e" fillOpacity={0.12} />
                <ReferenceArea y1={0.8} y2={1.3} fill="#2e7d4f" fillOpacity={0.14} />
                <ReferenceArea y1={1.3} y2={1.5} fill="#e08a1e" fillOpacity={0.16} />
                <ReferenceArea y1={1.5} y2={2.2} fill="#c5283d" fillOpacity={0.14} />
                <ReferenceLine y={1} stroke="#999" strokeDasharray="4 4" />
                <CartesianGrid stroke="#eee" vertical={false} />
                <XAxis dataKey="date" tickFormatter={dShort} tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 2.2]} tick={{ fontSize: 11 }} />
                <Tooltip labelFormatter={dShort} />
                <Line dataKey="acwr" name="ACWR" stroke="#111" strokeWidth={2} dot={{ r: 2 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-2">
            <div>
              <h3>Alertas de {sel.split(' ').slice(-1)[0]}</h3>
              {palerts.length === 0
                ? <div className="note">Sin días fuera de la zona óptima.</div>
                : <DataTable
                    columns={[
                      { key: 'date', label: 'Fecha' },
                      { key: 'acwr', label: 'ACWR', num: true, fmt: (v) => fmt(v) },
                      { key: 'risk_zone', label: 'Zona', render: (r2) => riskBadge(r2.risk_zone) },
                    ]}
                    rows={palerts} />}
            </div>
            <div>
              <h3>Riesgo alto en el plantel ({highRisk.length})</h3>
              <DataTable
                columns={[
                  { key: 'player_name', label: 'Jugador' },
                  { key: 'team_name', label: 'Equipo' },
                  { key: 'date', label: 'Fecha' },
                  { key: 'acwr', label: 'ACWR', num: true, fmt: (v) => fmt(v) },
                ]}
                rows={highRisk.slice(0, 30)} />
            </div>
          </div>
        </>
      )}

      {tab === 'xg' && (
        <>
          <div className="grid grid-3" style={{ marginBottom: 18 }}>
            <StatCard num={r.toFixed(3)} lbl="Correlación de Pearson vs StatsBomb" />
            <StatCard num="0.802" lbl="ROC-AUC (validación cruzada 5-fold)" />
            <StatCard num={m.length.toLocaleString()} lbl="Tiros en juego evaluados" />
          </div>

          <div className="card">
            <h3>xG del modelo propio vs StatsBomb</h3>
            <ResponsiveContainer width="100%" height={460}>
              <ScatterChart margin={{ top: 10, right: 20, bottom: 30, left: 10 }}>
                <CartesianGrid stroke="#eee" />
                <XAxis type="number" dataKey="statsbomb_xg" domain={[0, 1]} tick={{ fontSize: 11 }}
                       label={{ value: 'StatsBomb xG', position: 'bottom', fontSize: 12 }} />
                <YAxis type="number" dataKey="predicted_xg" domain={[0, 1]} tick={{ fontSize: 11 }}
                       label={{ value: 'xG modelo propio', angle: -90, position: 'insideLeft', fontSize: 12 }} />
                <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#c5283d" strokeDasharray="5 5" />
                <Tooltip content={<XgTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                <Scatter data={m} fill="#1f77b4" fillOpacity={0.4} isAnimationActive={false} />
              </ScatterChart>
            </ResponsiveContainer>
            <p style={{ color: 'var(--muted)', fontSize: '.88rem' }}>
              Cada punto es un tiro. Cuanto más cerca de la diagonal, más coincide
              nuestro xG con el de StatsBomb. Penales excluidos.
            </p>
          </div>
        </>
      )}
    </div>
  )
}

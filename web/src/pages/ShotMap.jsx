import { useState, useMemo } from 'react'
import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, Tooltip,
  ReferenceArea, ReferenceLine, ReferenceDot,
} from 'recharts'
import { SectionHead, StatCard } from '../components/ui.jsx'
import { Loader, ErrorBox } from '../components/Loader.jsx'
import { useJSON, fmt } from '../lib/data.js'

function ShotTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="tooltip-box">
      <div className="t-name">{d.player_name}</div>
      <div className="t-row">{d.team_name} · min {d.minute}</div>
      <div className="t-row">{d.shot_type} · {d.body_part}</div>
      <div className="t-row">xG: {fmt(d.statsbomb_xg)} · <b>{d.outcome}</b></div>
    </div>
  )
}

// Punto personalizado (radio y color según gol)
const makeDot = (r, fill, opacity, stroke) => (props) => {
  const { cx, cy } = props
  if (cx == null) return null
  return <circle cx={cx} cy={cy} r={r} fill={fill} fillOpacity={opacity}
                 stroke={stroke || 'none'} strokeWidth={stroke ? 1 : 0} />
}

export default function ShotMap() {
  const { loading, error, data: shots } = useJSON('shots')
  const [team, setTeam] = useState('(Todos)')
  const [player, setPlayer] = useState('(Todos)')
  const [stype, setStype] = useState('(Todos)')
  const [onlyGoals, setOnlyGoals] = useState(false)

  const teams = useMemo(
    () => shots ? ['(Todos)', ...new Set(shots.map((s) => s.team_name).filter(Boolean).sort())] : [],
    [shots])

  const filtered = useMemo(() => {
    if (!shots) return []
    return shots.filter((s) =>
      (team === '(Todos)' || s.team_name === team) &&
      (player === '(Todos)' || s.player_name === player) &&
      (stype === '(Todos)' || s.shot_type === stype) &&
      (!onlyGoals || s.is_goal === 1))
  }, [shots, team, player, stype, onlyGoals])

  if (loading) return <Loader />
  if (error) return <ErrorBox error={error} />

  const playersInTeam = ['(Todos)', ...new Set(
    shots.filter((s) => team === '(Todos)' || s.team_name === team)
      .map((s) => s.player_name).filter(Boolean).sort())]
  const shotTypes = ['(Todos)', ...new Set(shots.map((s) => s.shot_type).filter(Boolean).sort())]

  const goals = filtered.filter((s) => s.is_goal === 1)
  const noGoals = filtered.filter((s) => s.is_goal === 0)
  const totalXg = filtered.reduce((a, s) => a + (s.statsbomb_xg || 0), 0)

  return (
    <div className="container section">
      <SectionHead title="🎯 Mapa de tiros interactivo"
        subtitle="Pasá el mouse por cualquier punto para ver quién remató, en qué minuto, con qué xG y el desenlace." />

      <div className="controls">
        <div className="field">
          <label>Equipo</label>
          <select value={team} onChange={(e) => { setTeam(e.target.value); setPlayer('(Todos)') }}>
            {teams.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Jugador</label>
          <select value={player} onChange={(e) => setPlayer(e.target.value)}>
            {playersInTeam.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div className="field">
          <label>Tipo de jugada</label>
          <select value={stype} onChange={(e) => setStype(e.target.value)}>
            {shotTypes.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <label className="check">
          <input type="checkbox" checked={onlyGoals} onChange={(e) => setOnlyGoals(e.target.checked)} />
          Solo goles
        </label>
      </div>

      <div className="grid grid-3" style={{ marginBottom: 18 }}>
        <StatCard num={filtered.length.toLocaleString()} lbl="Tiros mostrados" />
        <StatCard num={goals.length} lbl="Goles" />
        <StatCard num={fmt(totalXg)} lbl="xG total" />
      </div>

      <div className="card">
        <div style={{ maxWidth: 540, margin: '0 auto' }}>
          <ResponsiveContainer width="100%" height={660}>
            <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
              {/* Campo (mitad de ataque): arco a la derecha en x=120 */}
              <ReferenceArea x1={60} y1={0} x2={120} y2={80} fill="#eef5ee" fillOpacity={0.8} stroke="#cbb" />
              <ReferenceArea x1={102} y1={18} x2={120} y2={62} fill="none" stroke="#b9a98f" />
              <ReferenceArea x1={114} y1={30} x2={120} y2={50} fill="none" stroke="#b9a98f" />
              <ReferenceLine segment={[{ x: 120, y: 36 }, { x: 120, y: 44 }]} stroke="#111" strokeWidth={3} />
              <ReferenceDot x={108} y={40} r={2} fill="#b9a98f" stroke="none" />
              <XAxis type="number" dataKey="location_x" domain={[60, 122]} hide />
              <YAxis type="number" dataKey="location_y" domain={[0, 80]} hide />
              <Tooltip content={<ShotTooltip />} cursor={{ strokeDasharray: '3 3' }} />
              <Scatter data={noGoals} shape={makeDot(3.6, '#2f6fb0', 0.4)} isAnimationActive={false} />
              <Scatter data={goals} shape={makeDot(6, '#c5283d', 0.95, '#fff')} isAnimationActive={false} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <div style={{ textAlign: 'center', color: 'var(--muted)', fontSize: '.85rem' }}>
          <span style={{ color: '#2f6fb0' }}>●</span> Sin gol &nbsp;&nbsp;
          <span style={{ color: '#c5283d' }}>●</span> Gol &nbsp; · &nbsp; el arco está a la derecha
        </div>
      </div>
    </div>
  )
}

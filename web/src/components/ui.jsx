import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts'
import { shortName } from '../lib/data.js'

export function SectionHead({ title, subtitle }) {
  return (
    <div className="section-head">
      <h2>{title}</h2>
      {subtitle && <p>{subtitle}</p>}
    </div>
  )
}

export function StatCard({ num, lbl }) {
  return (
    <div className="stat-card">
      <div className="num">{num}</div>
      <div className="lbl">{lbl}</div>
    </div>
  )
}

/** Ranking de barras horizontales (el mayor queda arriba). */
export function BarRanking({ data, valueKey, labelKey, color = '#7a1230', useShort = true }) {
  const rows = data
    .map((d) => ({ ...d, _label: useShort ? shortName(d[labelKey]) : d[labelKey] }))
    .sort((a, b) => a[valueKey] - b[valueKey]) // asc → el mayor arriba
  const height = Math.max(260, rows.length * 30)
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} stroke="#eee" />
        <XAxis type="number" tick={{ fontSize: 12 }} />
        <YAxis type="category" dataKey="_label" width={150} tick={{ fontSize: 12 }} />
        <Tooltip cursor={{ fill: 'rgba(122,18,48,0.06)' }} />
        <Bar dataKey={valueKey} fill={color} radius={[0, 6, 6, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

/** Tabla simple a partir de columnas [{key, label, num?, fmt?}] */
export function DataTable({ columns, rows }) {
  return (
    <div className="table-wrap">
      <table className="data">
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} className={c.num ? 'num' : ''}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td key={c.key} className={c.num ? 'num' : ''}>
                  {c.render ? c.render(r) : c.fmt ? c.fmt(r[c.key]) : r[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

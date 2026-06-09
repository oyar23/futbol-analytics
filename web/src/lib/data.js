import { useEffect, useState } from 'react'

const cache = {}

/** Carga un JSON de /public/data con caché en memoria. */
export function loadJSON(name) {
  if (cache[name]) return Promise.resolve(cache[name])
  return fetch(`${import.meta.env.BASE_URL}data/${name}.json`)
    .then((r) => {
      if (!r.ok) throw new Error(`No se pudo cargar ${name}.json`)
      return r.json()
    })
    .then((d) => {
      cache[name] = d
      return d
    })
}

/**
 * Hook que carga uno o varios JSON.
 * @param {string|string[]} names
 * @returns {{loading:boolean, error:string|null, data:any}}
 */
export function useJSON(names) {
  const list = Array.isArray(names) ? names : [names]
  const key = list.join(',')
  const [state, setState] = useState({ loading: true, error: null, data: null })

  useEffect(() => {
    let alive = true
    setState({ loading: true, error: null, data: null })
    Promise.all(list.map(loadJSON))
      .then((results) => {
        if (alive) {
          setState({
            loading: false,
            error: null,
            data: Array.isArray(names) ? results : results[0],
          })
        }
      })
      .catch((e) => {
        if (alive) setState({ loading: false, error: e.message, data: null })
      })
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  return state
}

/** Formatea un número con N decimales (devuelve string). */
export const fmt = (v, d = 2) =>
  v === null || v === undefined || Number.isNaN(v) ? '-' : Number(v).toFixed(d)

/** Apellido / nombre corto para etiquetas. */
export const shortName = (name) => {
  if (!name) return ''
  const parts = name.split(' ')
  return parts.length > 1 ? parts.slice(-2).join(' ') : name
}

export function Loader({ text = 'Cargando datos…' }) {
  return (
    <div className="loader">
      <div className="spinner" />
      {text}
    </div>
  )
}

export function ErrorBox({ error }) {
  return (
    <div className="container section">
      <div className="note">
        No se pudieron cargar los datos ({error}). Generá los JSON con{' '}
        <code>python run_pipeline.py</code> y{' '}
        <code>python -m src.dashboard.export_json</code>.
      </div>
    </div>
  )
}

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner container">
        <div>
          <strong>Lautaro Oyarzun</strong> — Análisis de datos · Mundial Qatar 2022
          <div style={{ fontSize: '.82rem', opacity: 0.8, marginTop: 4 }}>
            Datos: StatsBomb Open Data · Proyecto de portfolio (Analista de Datos / BI)
          </div>
        </div>
        <div>
          <a href="https://github.com/oyar23/futbol-analytics" target="_blank" rel="noreferrer">
            ⤳ Repositorio en GitHub
          </a>
        </div>
      </div>
    </footer>
  )
}

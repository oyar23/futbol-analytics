/**
 * Emblema propio (no es el logo oficial de la FIFA, que es marca registrada).
 * Crest de fútbol con la paleta Qatar 2022 — granate y dorado.
 */
export default function Emblem({ size = 42 }) {
  return (
    <svg
      width={size}
      height={(size * 72) / 64}
      viewBox="0 0 64 72"
      role="img"
      aria-label="Qatar 2022 Análisis"
    >
      {/* Escudo */}
      <path
        d="M32 2 L60 12 V36 C60 55 47 66 32 70 C17 66 4 55 4 36 V12 Z"
        fill="#7a1230"
        stroke="#c8a23c"
        strokeWidth="3"
      />
      {/* Pelota */}
      <g transform="translate(32 32)">
        <circle r="16" fill="#fbf6ee" stroke="#5a0d23" strokeWidth="1.5" />
        {/* Pentágono central */}
        <polygon
          points="0,-6 5.7,-1.9 3.5,4.9 -3.5,4.9 -5.7,-1.9"
          fill="#5a0d23"
        />
        {/* Costuras hacia los bordes */}
        <g stroke="#5a0d23" strokeWidth="1.4">
          <line x1="0" y1="-6" x2="0" y2="-15" />
          <line x1="5.7" y1="-1.9" x2="14" y2="-5" />
          <line x1="3.5" y1="4.9" x2="9" y2="12" />
          <line x1="-3.5" y1="4.9" x2="-9" y2="12" />
          <line x1="-5.7" y1="-1.9" x2="-14" y2="-5" />
        </g>
      </g>
      {/* Estrella dorada */}
      <polygon
        points="32,44 33.4,48 37.6,48 34.2,50.6 35.5,54.6 32,52.1 28.5,54.6 29.8,50.6 26.4,48 30.6,48"
        fill="#e3ca7e"
      />
    </svg>
  )
}

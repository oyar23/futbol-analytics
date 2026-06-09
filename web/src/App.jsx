import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Footer from './components/Footer.jsx'
import Home from './pages/Home.jsx'
import Kpis from './pages/Kpis.jsx'
import ShotMap from './pages/ShotMap.jsx'
import Scouting from './pages/Scouting.jsx'
import Physical from './pages/Physical.jsx'

export default function App() {
  return (
    <div className="app">
      <Navbar />
      <main className="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/kpis" element={<Kpis />} />
          <Route path="/tiros" element={<ShotMap />} />
          <Route path="/scouting" element={<Scouting />} />
          <Route path="/fisico-xg" element={<Physical />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}

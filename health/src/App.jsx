import './App.css'
import MentalHealthDashboard from './MentalHealthDashboard'
import TelegramSetup from './components/telegram'

function App() {
  const setupComplete = localStorage.getItem("setupComplete")

  if (!setupComplete) {
    return <TelegramSetup />
  }

  return <MentalHealthDashboard />
}

export default App
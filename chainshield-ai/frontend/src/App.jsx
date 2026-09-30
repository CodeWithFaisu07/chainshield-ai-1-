import TransactionSearch from './pages/TransactionSearch.jsx'
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './layout/Layout.jsx'
import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Investigations from './pages/Investigations.jsx'
import InvestigationDetail from './pages/InvestigationDetail.jsx'
import EntityGraph from './pages/EntityGraph.jsx'

import Alerts from './pages/Alerts.jsx'
import Reports from './pages/Reports.jsx'
import DataSources from './pages/DataSources.jsx'
import Settings from './pages/Settings.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />

      <Route element={<Layout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/investigations" element={<Investigations />} />
        <Route path="/investigations/:txid" element={<InvestigationDetail />} />
        <Route path="/graph" element={<EntityGraph />} />
        
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/data-sources" element={<DataSources />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      <Route path="/transactions" element={<TransactionSearch />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

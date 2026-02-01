import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Result from './pages/Result';
import History from './pages/History';
import Playbook from './pages/Playbook';
import Stats from './pages/Stats';
import Settings from './pages/Settings';

const App: React.FC = () => {
  return (
    <HashRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/result/:caseId" element={<Result />} />
          <Route path="/history" element={<History />} />
          <Route path="/playbook" element={<Playbook />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </HashRouter>
  );
};

export default App;
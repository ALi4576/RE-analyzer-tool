import { useEffect } from 'react';
import { NotificationContainer } from '@/components/index';
import { Dashboard } from '@/pages/Dashboard';
import { useRequirementStore } from '@/store/requirementStore';
import { apiClient } from '@/services/api';

function App() {
  const { notifications, removeNotification } = useRequirementStore();

  // Probe backend health once on mount so dev sees connection status in console.
  useEffect(() => {
    apiClient
      .getHealth()
      .then(() => console.log('Backend connected'))
      .catch((err) => console.error('Backend connection failed:', err));
  }, []);

  return (
    <div
      className="min-h-screen"
      style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-text-primary)' }}
    >
      <NotificationContainer
        notifications={notifications}
        onClose={removeNotification}
      />
      <Dashboard />
    </div>
  );
}

export default App;

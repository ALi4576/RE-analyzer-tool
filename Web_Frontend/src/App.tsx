import { useEffect } from 'react';
import { Header, NotificationContainer } from '@/components/index';
import { Dashboard } from '@/pages/Dashboard';
import { useRequirementStore } from '@/store/requirementStore';
import { apiClient } from '@/services/api';

function App() {
  const { notifications, removeNotification } = useRequirementStore();

  // Check backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await apiClient.getHealth();
        console.log('✓ Backend connected');
      } catch (error) {
        console.error('✗ Backend connection failed:', error);
      }
    };

    checkHealth();
  }, []);

  return (
    <div className="min-h-screen bg-neutral-50">
      <Header />
      <NotificationContainer
        notifications={notifications}
        onClose={removeNotification}
      />
      <main>
        <Dashboard />
      </main>
    </div>
  );
}

export default App;

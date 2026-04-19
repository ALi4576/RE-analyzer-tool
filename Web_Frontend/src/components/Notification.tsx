import { X, Check, AlertCircle, Info } from 'lucide-react';
import { UINotification } from '@/types/index';
import { cn } from '@/utils/helpers';

interface NotificationProps {
  notification: UINotification;
  onClose: (id: string) => void;
}

export const Notification: React.FC<NotificationProps> = ({ notification, onClose }) => {
  const { type, message, id } = notification;

  const styles = {
    success: 'bg-green-50 border-green-200 text-green-900',
    error: 'bg-red-50 border-red-200 text-red-900',
    info: 'bg-blue-50 border-blue-200 text-blue-900',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-900',
  };

  const icons = {
    success: <Check className="w-5 h-5 text-green-600" />,
    error: <AlertCircle className="w-5 h-5 text-red-600" />,
    info: <Info className="w-5 h-5 text-blue-600" />,
    warning: <AlertCircle className="w-5 h-5 text-yellow-600" />,
  };

  return (
    <div
      className={cn(
        'card flex items-start gap-3 p-4 border animate-slide-in',
        styles[type]
      )}
    >
      {icons[type]}
      <div className="flex-1">
        <p className="text-sm font-medium">{message}</p>
      </div>
      <button
        onClick={() => onClose(id)}
        className="text-neutral-400 hover:text-neutral-600 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

interface NotificationContainerProps {
  notifications: UINotification[];
  onClose: (id: string) => void;
}

export const NotificationContainer: React.FC<NotificationContainerProps> = ({
  notifications,
  onClose,
}) => {
  return (
    <div className="fixed top-20 right-6 z-50 max-w-md space-y-2">
      {notifications.map((notification) => (
        <Notification
          key={notification.id}
          notification={notification}
          onClose={onClose}
        />
      ))}
    </div>
  );
};

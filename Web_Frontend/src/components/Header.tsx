import { FileText, Settings, LogOut } from 'lucide-react';

interface HeaderProps {
  onSettingsClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onSettingsClick }) => {
  return (
    <header className="bg-white border-b border-neutral-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
            <FileText className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-neutral-900">RE Tool</h1>
            <p className="text-xs text-neutral-500">Requirements Engineering</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="hidden md:flex items-center gap-8">
          <a href="#" className="text-sm text-neutral-600 hover:text-neutral-900">
            Dashboard
          </a>
          <a href="#" className="text-sm text-neutral-600 hover:text-neutral-900">
            Analyze
          </a>
          <a href="#" className="text-sm text-neutral-600 hover:text-neutral-900">
            Export
          </a>
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={onSettingsClick}
            className="btn-ghost"
            title="Settings"
          >
            <Settings className="w-5 h-5" />
          </button>
          <button className="btn-ghost" title="Logout">
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  );
};

import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  ShieldCheck, 
  History, 
  BookOpen, 
  BarChart2, 
  Settings, 
  Menu,
  X
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);
  const location = useLocation();

  const navItems = [
    { name: '核查', path: '/', icon: ShieldCheck },
    { name: '历史记录', path: '/history', icon: History },
    { name: '规则库', path: '/playbook', icon: BookOpen },
    { name: '统计', path: '/stats', icon: BarChart2 },
    { name: '设置', path: '/settings', icon: Settings },
  ];

  const getPageTitle = () => {
    if (location.pathname === '/') return '事实核查';
    if (location.pathname.startsWith('/result')) return '结果分析';
    const current = navItems.find(item => location.pathname.startsWith(item.path) && item.path !== '/');
    return current ? current.name : 'ECHO';
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Mobile Sidebar Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 z-40 bg-gray-900/50 lg:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 ease-in-out lg:static lg:translate-x-0
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center h-16 px-6 border-b border-gray-100">
          <ShieldCheck className="w-8 h-8 text-gray-900" />
          <span className="ml-3 text-xl font-bold tracking-tight text-gray-900">ECHO</span>
        </div>

        <nav className="p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setIsMobileMenuOpen(false)}
              className={({ isActive }) => `
                flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors
                ${isActive 
                  ? 'bg-gray-100 text-gray-900' 
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'}
              `}
            >
              <item.icon className="w-5 h-5 mr-3" />
              {item.name}
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 w-full p-6 border-t border-gray-100 bg-gray-50/50">
          <div className="flex items-center">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="ml-2 text-xs font-medium text-gray-500">系统运行中</span>
          </div>
          <p className="mt-1 text-xs text-gray-400">v1.0.0 • 本地环境</p>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Mobile Header */}
        <header className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 lg:hidden">
          <div className="flex items-center">
            <ShieldCheck className="w-6 h-6 text-gray-900" />
            <span className="ml-2 text-lg font-bold text-gray-900">ECHO</span>
          </div>
          <button 
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 text-gray-500 rounded-md hover:bg-gray-100"
          >
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </header>

        {/* Desktop Header / Breadcrumb placeholder */}
        <header className="hidden lg:flex items-center justify-between h-16 px-8 bg-white border-b border-gray-200">
          <h1 className="text-xl font-semibold text-gray-900">{getPageTitle()}</h1>
          <div className="flex items-center space-x-4">
            <span className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded-full border border-blue-100">
              默认规则库
            </span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
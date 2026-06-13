import React, { useState, useEffect, lazy, Suspense } from 'react';

// 懒加载页面组件
const Login = lazy(() => import('../pages/login/index'));
const Register = lazy(() => import('../pages/register/index'));
const Home = lazy(() => import('../pages/home/index'));
const Goals = lazy(() => import('../pages/goals/index'));
const Training = lazy(() => import('../pages/training/index'));
const Profile = lazy(() => import('../pages/profile/index'));
const AI = lazy(() => import('../pages/ai/index'));

const pageMap: Record<string, React.LazyExoticComponent<React.ComponentType<any>>> = {
  'pages/login/index': Login,
  'pages/register/index': Register,
  'pages/home/index': Home,
  'pages/goals/index': Goals,
  'pages/training/index': Training,
  'pages/profile/index': Profile,
  'pages/ai/index': AI,
};

// Tab 栏配置
const tabPages = ['pages/home/index', 'pages/goals/index', 'pages/training/index', 'pages/profile/index'];

const tabBarConfig = [
  { pagePath: 'pages/home/index', text: '首页', icon: '🏠' },
  { pagePath: 'pages/goals/index', text: '目标', icon: '🎯' },
  { pagePath: 'pages/training/index', text: '训练', icon: '💪' },
  { pagePath: 'pages/profile/index', text: '我的', icon: '👤' },
];

const Loading = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px', color: '#6B7280' }}>
    加载中...
  </div>
);

export default function AppRouter() {
  const [currentPage, setCurrentPage] = useState(() => {
    return window.location.hash.replace('#', '') || 'pages/login/index';
  });

  useEffect(() => {
    const handleRouteChange = () => {
      const page = window.location.hash.replace('#', '') || 'pages/login/index';
      setCurrentPage(page);
    };

    window.addEventListener('hashchange', handleRouteChange);
    window.addEventListener('taro-route-change', handleRouteChange);
    return () => {
      window.removeEventListener('hashchange', handleRouteChange);
      window.removeEventListener('taro-route-change', handleRouteChange);
    };
  }, []);

  const PageComponent = pageMap[currentPage] || Login;
  const isTabPage = tabPages.includes(currentPage);

  const handleTabClick = (pagePath: string) => {
    window.location.hash = pagePath;
    window.dispatchEvent(new Event('taro-route-change'));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <div style={{ flex: 1, paddingBottom: isTabPage ? '50px' : '0' }}>
        <Suspense fallback={<Loading />}>
          <PageComponent />
        </Suspense>
      </div>

      {isTabPage && (
        <div style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          height: '50px',
          display: 'flex',
          backgroundColor: '#FFFFFF',
          borderTop: '1px solid #E5E7EB',
          zIndex: 1000,
        }}>
          {tabBarConfig.map(tab => (
            <div
              key={tab.pagePath}
              onClick={() => handleTabClick(tab.pagePath)}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                color: currentPage === tab.pagePath ? '#4F46E5' : '#6B7280',
                fontSize: '12px',
              }}
            >
              <span style={{ fontSize: '18px' }}>{tab.icon}</span>
              <span>{tab.text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
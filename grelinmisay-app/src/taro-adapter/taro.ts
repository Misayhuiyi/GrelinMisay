// Taro API 到浏览器 API 的适配层

// 简易哈希路由
function getCurrentPage(): string {
  const hash = window.location.hash.replace('#', '') || '/pages/login/index';
  return hash;
}

function navigateTo(url: string, _replace = false) {
  // 提取页面路径
  let path = url;
  if (path.startsWith('/pages/')) {
    path = path.substring(1); // 去掉开头的 /
  }
  window.location.hash = path;
  window.dispatchEvent(new Event('taro-route-change'));
}

const Taro = {
  // 存储
  setStorageSync(key: string, data: any) {
    try {
      localStorage.setItem(key, typeof data === 'string' ? data : JSON.stringify(data));
    } catch (e) {
      console.warn('setStorageSync failed', e);
    }
  },

  getStorageSync(key: string): any {
    try {
      const val = localStorage.getItem(key);
      if (!val) return null;
      try {
        return JSON.parse(val);
      } catch {
        return val;
      }
    } catch (e) {
      return null;
    }
  },

  clearStorageSync() {
    try {
      localStorage.clear();
    } catch (e) {
      console.warn('clearStorageSync failed', e);
    }
  },

  // Toast
  showToast(options: { title: string; icon?: string }) {
    // 创建自定义 toast
    const toast = document.createElement('div');
    toast.className = 'taro-toast';
    toast.textContent = options.title;
    toast.style.cssText = `
      position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
      background: rgba(0,0,0,0.8); color: #fff; padding: 12px 24px;
      border-radius: 8px; font-size: 14px; z-index: 9999;
      pointer-events: none; transition: opacity 0.3s;
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => document.body.removeChild(toast), 300);
    }, 2000);
  },

  // Modal
  showModal(options: { title: string; content: string; success?: (res: { confirm: boolean; cancel: boolean }) => void }) {
    const confirmed = window.confirm(`${options.title}\n\n${options.content}`);
    if (options.success) {
      options.success({ confirm: confirmed, cancel: !confirmed });
    }
  },

  // 导航
  navigateTo(options: { url: string }) {
    navigateTo(options.url);
  },

  navigateBack() {
    window.history.back();
  },

  switchTab(options: { url: string }) {
    navigateTo(options.url, true);
  },

  reLaunch(options: { url: string }) {
    navigateTo(options.url, true);
  },

  getCurrentPages() {
    return [{ route: getCurrentPage() }];
  },
};

export default Taro;
export default {
  pages: [
    'pages/login/index',
    'pages/register/index',
    'pages/home/index',
    'pages/goals/index',
    'pages/training/index',
    'pages/profile/index',
    'pages/ai/index',
  ],
  window: {
    navigationBarTitleText: 'GrelinMisay',
    navigationBarBackgroundColor: '#4F46E5',
    navigationBarTextStyle: 'white',
    backgroundTextStyle: 'light',
  },
  tabBar: {
    custom: false,
    color: '#6B7280',
    selectedColor: '#4F46E5',
    backgroundColor: '#FFFFFF',
    borderStyle: 'white',
    list: [
      {
        pagePath: 'pages/home/index',
        text: '首页',
        iconPath: '',
        selectedIconPath: '',
      },
      {
        pagePath: 'pages/goals/index',
        text: '目标',
        iconPath: '',
        selectedIconPath: '',
      },
      {
        pagePath: 'pages/training/index',
        text: '训练',
        iconPath: '',
        selectedIconPath: '',
      },
      {
        pagePath: 'pages/profile/index',
        text: '我的',
        iconPath: '',
        selectedIconPath: '',
      },
    ],
  },
};
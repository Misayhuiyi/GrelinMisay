import { useState, useEffect } from 'react';
import { View, Text, Button } from '@tarojs/components';
import Taro from '@tarojs/taro';
import { userAPI } from '../../services/api';
import './index.css';

export default function Profile() {
  const [user, setUser] = useState<any>(null);
  const token = Taro.getStorageSync('token') || '';

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const data = await userAPI.getMe(token);
      setUser(data);
    } catch (e) {
      console.log('加载失败', e);
    }
  };

  const handleAbout = () => {
    Taro.showModal({
      title: '关于 GrelinMisay',
      content: 'GrelinMisay v1.1.0\n全能生活自律 APP\n\n健身训练 / 目标管理 / AI 助手\n\nPower by GLM-4.6V-Flash',
      showCancel: false,
      confirmText: '知道了',
    });
  };

  const handleSettings = () => {
    Taro.showToast({ title: '系统设置开发中', icon: 'none' });
  };

  const handleLogout = () => {
    Taro.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          Taro.clearStorageSync();
          Taro.reLaunch({ url: '/pages/login/index' });
        }
      },
    });
  };

  return (
    <View className="profile-page">
      <View className="profile-header">
        <View className="avatar">
          <Text className="avatar-text">{user?.nickname?.[0] || '?'}</Text>
        </View>
        <Text className="nickname">{user?.nickname || '用户'}</Text>
        <Text className="phone">{user?.phone || ''}</Text>
      </View>

      <View className="menu-section">
        {[
          { label: 'AI 助手', icon: '🤖', url: '/pages/ai/index' },
          { label: '训练记录', icon: '💪', url: '/pages/training/index' },
          { label: '我的目标', icon: '🎯', url: '/pages/goals/index' },
        ].map((item, idx) => (
          <View
            key={idx}
            className="menu-item"
            onClick={() => Taro.switchTab({ url: item.url })}
          >
            <Text className="menu-icon">{item.icon}</Text>
            <Text className="menu-label">{item.label}</Text>
            <Text className="menu-arrow">{'>'}</Text>
          </View>
        ))}
      </View>

      <View className="menu-section">
        <View className="menu-item" onClick={handleAbout}>
          <Text className="menu-icon">📋</Text>
          <Text className="menu-label">关于 GrelinMisay</Text>
          <Text className="menu-arrow">{'>'}</Text>
        </View>
        <View className="menu-item" onClick={handleSettings}>
          <Text className="menu-icon">⚙️</Text>
          <Text className="menu-label">系统设置</Text>
          <Text className="menu-arrow">{'>'}</Text>
        </View>
      </View>

      <Button className="logout-btn" onClick={handleLogout}>
        退出登录
      </Button>
    </View>
  );
}
import { useState } from 'react';
import { View, Input, Button, Text } from '@tarojs/components';
import Taro from '@tarojs/taro';
import { authAPI } from '../../services/api';
import './index.css';

export default function Login() {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!phone || !password) {
      Taro.showToast({ title: '请输入手机号和密码', icon: 'none' });
      return;
    }
    setLoading(true);
    try {
      const data = await authAPI.login(phone, password);
      Taro.setStorageSync('token', data.token);
      Taro.setStorageSync('user', JSON.stringify(data));
      Taro.showToast({ title: '登录成功', icon: 'success' });
      setTimeout(() => Taro.switchTab({ url: '/pages/home/index' }), 1000);
    } catch (e: any) {
      Taro.showToast({ title: e.message || '登录失败', icon: 'none' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <View className="login-page">
      <View className="login-header">
        <Text className="login-title">GrelinMisay</Text>
        <Text className="login-subtitle">全能生活自律助手</Text>
      </View>
      <View className="login-form">
        <View className="form-item">
          <Text className="form-label">手机号</Text>
          <Input
            className="form-input"
            type="number"
            maxlength={11}
            placeholder="请输入手机号"
            value={phone}
            onInput={e => setPhone(e.detail.value)}
          />
        </View>
        <View className="form-item">
          <Text className="form-label">密码</Text>
          <Input
            className="form-input"
            type="password"
            placeholder="请输入密码"
            value={password}
            onInput={e => setPassword(e.detail.value)}
          />
        </View>
        <Button className="login-btn" onClick={handleLogin} loading={loading}>
          登录
        </Button>
        <Button className="register-link" onClick={() => Taro.navigateTo({ url: '/pages/register/index' })}>
          没有账号？去注册
        </Button>
      </View>
    </View>
  );
}
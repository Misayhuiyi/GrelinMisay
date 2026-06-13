import { useState } from 'react';
import { View, Input, Button, Text } from '@tarojs/components';
import Taro from '@tarojs/taro';
import { authAPI } from '../../services/api';
import './index.css';

export default function Register() {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [nickname, setNickname] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!phone || !password || !nickname) {
      Taro.showToast({ title: '请填写所有字段', icon: 'none' });
      return;
    }
    if (password.length < 6) {
      Taro.showToast({ title: '密码至少6位', icon: 'none' });
      return;
    }
    setLoading(true);
    try {
      const data = await authAPI.register(phone, password, nickname);
      Taro.setStorageSync('token', data.token);
      Taro.setStorageSync('user', JSON.stringify(data));
      Taro.showToast({ title: '注册成功', icon: 'success' });
      setTimeout(() => Taro.switchTab({ url: '/pages/home/index' }), 1000);
    } catch (e: any) {
      Taro.showToast({ title: e.message || '注册失败', icon: 'none' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <View className="register-page">
      <View className="register-header">
        <Text className="register-title">注册账号</Text>
      </View>
      <View className="register-form">
        <View className="form-item">
          <Text className="form-label">昵称</Text>
          <Input
            className="form-input"
            placeholder="你的昵称"
            maxlength={20}
            value={nickname}
            onInput={e => setNickname(e.detail.value)}
          />
        </View>
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
            placeholder="请设置密码（至少6位）"
            value={password}
            onInput={e => setPassword(e.detail.value)}
          />
        </View>
        <Button className="login-btn" onClick={handleRegister} loading={loading}>
          注册
        </Button>
        <Button className="register-link" onClick={() => Taro.navigateBack()}>
          已有账号？返回登录
        </Button>
      </View>
    </View>
  );
}
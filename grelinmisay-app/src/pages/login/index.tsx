import { useState, useRef } from 'react';
import { View, Input, Button, Text } from '@tarojs/components';
import Taro from '@tarojs/taro';
import { authAPI } from '../../services/api';
import './index.css';

type LoginMode = 'password' | 'code';

export default function Login() {
  const [mode, setMode] = useState<LoginMode>('password');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const timerRef = useRef<any>(null);

  const handleLogin = async () => {
    if (!phone) {
      Taro.showToast({ title: '请输入手机号', icon: 'none' });
      return;
    }
    if (mode === 'password' && !password) {
      Taro.showToast({ title: '请输入密码', icon: 'none' });
      return;
    }
    if (mode === 'code' && !code) {
      Taro.showToast({ title: '请输入验证码', icon: 'none' });
      return;
    }
    setLoading(true);
    try {
      let data: any;
      if (mode === 'password') {
        data = await authAPI.login(phone, password);
      } else {
        data = await authAPI.loginByCode(phone, code);
      }
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

  const handleSendCode = async () => {
    if (!phone) {
      Taro.showToast({ title: '请输入手机号', icon: 'none' });
      return;
    }
    if (countdown > 0) return;
    setSendingCode(true);
    try {
      await authAPI.sendCode(phone);
      Taro.showToast({ title: '验证码已发送', icon: 'success' });
      setCountdown(60);
      timerRef.current = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timerRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (e: any) {
      Taro.showToast({ title: e.message || '发送失败', icon: 'none' });
    } finally {
      setSendingCode(false);
    }
  };

  return (
    <View className="login-page">
      <View className="login-header">
        <Text className="login-title">GrelinMisay</Text>
        <Text className="login-subtitle">全能生活自律助手</Text>
      </View>

      <View className="login-form">
        {/* 登录方式切换 */}
        <View className="login-tabs">
          <View
            className={`login-tab ${mode === 'password' ? 'active' : ''}`}
            onClick={() => setMode('password')}
          >
            <Text>密码登录</Text>
          </View>
          <View
            className={`login-tab ${mode === 'code' ? 'active' : ''}`}
            onClick={() => setMode('code')}
          >
            <Text>验证码登录</Text>
          </View>
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

        {mode === 'password' ? (
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
        ) : (
          <View className="form-item">
            <Text className="form-label">验证码</Text>
            <View className="code-row">
              <Input
                className="form-input code-input"
                type="number"
                maxlength={6}
                placeholder="请输入验证码"
                value={code}
                onInput={e => setCode(e.detail.value)}
              />
              <Button
                className={`code-btn ${countdown > 0 ? 'counting' : ''}`}
                onClick={handleSendCode}
                loading={sendingCode}
                disabled={countdown > 0}
              >
                {countdown > 0 ? `${countdown}s` : '获取验证码'}
              </Button>
            </View>
          </View>
        )}

        <Button className="login-btn" onClick={handleLogin} loading={loading}>
          {mode === 'password' ? '登录' : '验证码登录'}
        </Button>

        <Button
          className="register-link"
          onClick={() => Taro.navigateTo({ url: '/pages/register/index' })}
        >
          没有账号？去注册
        </Button>
      </View>
    </View>
  );
}

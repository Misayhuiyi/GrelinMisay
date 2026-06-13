import { useState, useEffect } from 'react';
import { View, Text, Input, Button } from '@tarojs/components';
import Taro from '@tarojs/taro';
import { goalAPI } from '../../services/api';
import './index.css';

interface Goal {
  id: string;
  title: string;
  description: string;
  priority: string;
  progress: number;
  status: string;
  deadline: string | null;
}

export default function Goals() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [priority, setPriority] = useState('medium');
  const [deadline, setDeadline] = useState('');
  const token = Taro.getStorageSync('token') || '';

  useEffect(() => {
    loadGoals();
  }, []);

  const loadGoals = async () => {
    try {
      const data = await goalAPI.list(token);
      setGoals(data?.items || []);
    } catch (e) {
      console.log('加载失败', e);
    }
  };

  const handleCreate = async () => {
    if (!title.trim()) {
      Taro.showToast({ title: '请输入目标标题', icon: 'none' });
      return;
    }
    try {
      await goalAPI.create(token, { title, priority, deadline: deadline || null });
      Taro.showToast({ title: '创建成功', icon: 'success' });
      setShowForm(false);
      setTitle('');
      setPriority('medium');
      setDeadline('');
      loadGoals();
    } catch (e: any) {
      Taro.showToast({ title: e.message, icon: 'none' });
    }
  };

  const handleCheckin = async (id: string) => {
    try {
      const data = await goalAPI.checkin(token, id);
      Taro.showToast({ title: `打卡成功! ${data?.progress}%`, icon: 'success' });
      loadGoals();
    } catch (e: any) {
      Taro.showToast({ title: e.message, icon: 'none' });
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await goalAPI.delete(token, id);
      Taro.showToast({ title: '已删除', icon: 'success' });
      loadGoals();
    } catch (e: any) {
      Taro.showToast({ title: e.message, icon: 'none' });
    }
  };

  const activeGoals = goals.filter(g => g.status === 'active');
  const completedGoals = goals.filter(g => g.status === 'completed');

  return (
    <View className="goals-page">
      <View className="page-header">
        <Text className="page-title">目标管理</Text>
        <Button className="create-btn" onClick={() => setShowForm(!showForm)}>
          {showForm ? '取消' : '+ 新建'}
        </Button>
      </View>

      {showForm && (
        <View className="create-form">
          <Input
            className="form-input"
            placeholder="目标标题"
            value={title}
            onInput={e => setTitle(e.detail.value)}
          />
          <View className="priority-row">
            {['high', 'medium', 'low'].map(p => (
              <View
                key={p}
                className={`priority-chip ${priority === p ? 'active' : ''}`}
                onClick={() => setPriority(p)}
              >
                <Text>{p === 'high' ? '高' : p === 'medium' ? '中' : '低'}</Text>
              </View>
            ))}
          </View>
          <Input
            className="form-input"
            placeholder="截止日期 (yyyy-MM-dd)"
            value={deadline}
            onInput={e => setDeadline(e.detail.value)}
          />
          <Button className="create-btn primary" onClick={handleCreate}>确认创建</Button>
        </View>
      )}

      <Text className="section-title">进行中 ({activeGoals.length})</Text>
      {activeGoals.map(goal => (
        <View key={goal.id} className="goal-card">
          <View className="goal-header">
            <Text className="goal-title">{goal.title}</Text>
            <Text className={`priority-tag p-${goal.priority}`}>
              {goal.priority === 'high' ? '高' : goal.priority === 'medium' ? '中' : '低'}
            </Text>
          </View>
          <View className="progress-bar">
            <View className="progress-fill" style={{ width: `${goal.progress}%` }} />
          </View>
          <View className="goal-actions">
            <Text className="progress-label">{goal.progress}%</Text>
            <Button className="checkin-btn" onClick={() => handleCheckin(goal.id)}>打卡</Button>
            <Button className="delete-btn" onClick={() => handleDelete(goal.id)}>删除</Button>
          </View>
        </View>
      ))}

      {activeGoals.length === 0 && (
        <Text className="empty-text">暂无进行中的目标，点击右上角新建</Text>
      )}

      {completedGoals.length > 0 && (
        <>
          <Text className="section-title">已完成 ({completedGoals.length})</Text>
          {completedGoals.map(goal => (
            <View key={goal.id} className="goal-card completed">
              <View className="goal-header">
                <Text className="goal-title">{goal.title}</Text>
                <Text className="completed-badge">✓ 已完成</Text>
              </View>
            </View>
          ))}
        </>
      )}
    </View>
  );
}
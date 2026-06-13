import { useState, useEffect } from 'react';
import { View, Text, ScrollView } from '@tarojs/components';
import Taro from '@tarojs/taro';
import { calendarAPI, goalAPI } from '../../services/api';
import './index.css';

interface Event {
  id: string;
  event_type: string;
  title: string;
  color: string;
  description: string;
  start_time: string;
  progress?: number;
}

interface Goal {
  id: string;
  title: string;
  priority: string;
  progress: number;
  status: string;
}

export default function Home() {
  const [events, setEvents] = useState<Event[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [weekDays, setWeekDays] = useState<string[]>([]);
  const token = Taro.getStorageSync('token') || '';

  useEffect(() => {
    const token = Taro.getStorageSync('token');
    if (!token) {
      Taro.reLaunch({ url: '/pages/login/index' });
      return;
    }
    loadData();
  }, [currentDate]);

  const getWeekRange = (date: Date) => {
    const day = date.getDay();
    const monday = new Date(date);
    monday.setDate(date.getDate() - (day === 0 ? 6 : day - 1));
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);
    return { monday, sunday };
  };

  const loadData = async () => {
    try {
      const { monday, sunday } = getWeekRange(currentDate);
      const s = monday.toISOString().split('T')[0];
      const e = sunday.toISOString().split('T')[0];
      const [eventsData, goalsData] = await Promise.all([
        calendarAPI.events(token, s, e),
        goalAPI.list(token),
      ]);
      setEvents(eventsData?.events || []);
      setGoals(goalsData?.items || []);
    } catch (e) {
      console.log('数据加载失败', e);
    }
  };

  useEffect(() => {
    const days: string[] = [];
    const { monday } = getWeekRange(currentDate);
    const dayNames = ['一', '二', '三', '四', '五', '六', '日'];
    for (let i = 0; i < 7; i++) {
      const d = new Date(monday);
      d.setDate(monday.getDate() + i);
      days.push(`${d.getMonth() + 1}/${d.getDate()}`);
    }
    setWeekDays(days);
  }, [currentDate]);

  const prevWeek = () => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() - 7);
    setCurrentDate(d);
  };
  const nextWeek = () => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() + 7);
    setCurrentDate(d);
  };

  const todayEvents = events.filter(e => {
    const today = new Date().toISOString().split('T')[0];
    return e.start_time?.startsWith(today);
  });

  const handleNavigate = (url: string) => {
    Taro.switchTab({ url });
  };

  return (
    <View className="home-page">
      {/* 日历导航 */}
      <View className="calendar-nav">
        <Text className="nav-arrow" onClick={prevWeek}>{'<'}</Text>
        <Text className="nav-title">周视图</Text>
        <Text className="nav-arrow" onClick={nextWeek}>{'>'}</Text>
      </View>

      {/* 周视图 */}
      <View className="week-view">
        {weekDays.map((day, idx) => {
          const isToday = () => {
            const today = new Date();
            const { monday } = getWeekRange(currentDate);
            const d = new Date(monday);
            d.setDate(monday.getDate() + idx);
            return d.toDateString() === today.toDateString();
          };
          const dayEvents = events.filter(e => {
            const { monday } = getWeekRange(currentDate);
            const d = new Date(monday);
            d.setDate(monday.getDate() + idx);
            const ds = d.toISOString().split('T')[0];
            return e.start_time?.startsWith(ds);
          });
          return (
            <View key={idx} className={`day-cell ${isToday() ? 'today' : ''}`}>
              <Text className="day-text">{day}</Text>
              <View className="day-dots">
                {dayEvents.slice(0, 3).map((ev, i) => (
                  <View
                    key={i}
                    className="day-dot"
                    style={{ backgroundColor: ev.color }}
                  />
                ))}
              </View>
            </View>
          );
        })}
      </View>

      {/* 今日事务 */}
      <View className="section">
        <Text className="section-title">今日事务</Text>
        {todayEvents.length === 0 ? (
          <Text className="empty-text">今日暂无事务</Text>
        ) : (
          todayEvents.map(ev => (
            <View key={ev.id} className="event-card" style={{ borderLeftColor: ev.color }}>
              <Text className="event-title">{ev.title}</Text>
              <Text className="event-type">{ev.event_type === 'goal' ? '目标' : '事件'}</Text>
            </View>
          ))
        )}
      </View>

      {/* 快捷入口 */}
      <View className="section">
        <Text className="section-title">快捷入口</Text>
        <View className="quick-actions">
          {[
            { label: '打卡', icon: '✓', url: '/pages/goals/index' },
            { label: '训练', icon: '💪', url: '/pages/training/index' },
            { label: 'AI', icon: '🤖', url: '/pages/ai/index' },
          ].map((item, idx) => (
            <View key={idx} className="quick-action" onClick={() => handleNavigate(item.url)}>
              <Text className="action-icon">{item.icon}</Text>
              <Text className="action-label">{item.label}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* 进行中的目标 */}
      <View className="section">
        <Text className="section-title">进行中的目标</Text>
        {goals.filter(g => g.status === 'active').slice(0, 3).map(goal => (
          <View key={goal.id} className="goal-card">
            <View className="goal-header">
              <Text className="goal-title">{goal.title}</Text>
              <Text className={`goal-priority priority-${goal.priority}`}>
                {goal.priority === 'high' ? '高' : goal.priority === 'medium' ? '中' : '低'}
              </Text>
            </View>
            <View className="progress-bar">
              <View className="progress-fill" style={{ width: `${goal.progress}%` }} />
            </View>
            <Text className="progress-text">{goal.progress}%</Text>
          </View>
        ))}
        {goals.filter(g => g.status === 'active').length === 0 && (
          <Text className="empty-text">暂无进行中的目标</Text>
        )}
      </View>
    </View>
  );
}
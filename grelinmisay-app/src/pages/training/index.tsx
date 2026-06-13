import { useState, useEffect } from 'react';
import { View, Text, Input, Button, ScrollView } from '@tarojs/components';
import Taro from '@tarojs/taro';
import { trainingAPI } from '../../services/api';
import './index.css';

interface SetItem {
  set_order: number;
  action_name: string;
  reps: number;
  weight: number;
  rest_seconds: number;
  feeling: string;
  notes: string;
}

interface TrainingRecord {
  id: string;
  training_date: string;
  body_part: string;
  duration: number;
  notes: string;
  sets: SetItem[];
}

const DEFAULT_ACTIONS: Record<string, string[]> = {
  '胸部': ['杠铃卧推', '哑铃卧推', '上斜卧推', '哑铃飞鸟', '绳索夹胸', '俯卧撑'],
  '背部': ['引体向上', '杠铃划船', '高位下拉', '坐姿划船', '硬拉'],
  '肩部': ['杠铃推举', '哑铃推举', '侧平举', '前平举', '俯身飞鸟'],
  '手臂': ['杠铃弯举', '哑铃弯举', '三头下压', '窄距卧推'],
  '腿臀': ['深蹲', '腿举', '腿弯举', '腿屈伸', '臀推', '弓步蹲'],
  '核心': ['卷腹', '平板支撑', '悬垂举腿', '仰卧抬腿'],
  '有氧': ['跑步', '椭圆机', '动感单车', '跳绳', '快走'],
};

const FEELINGS = ['hard', 'normal', 'easy'];
const FEELING_LABELS: Record<string, string> = { hard: '😍累', normal: '😎一般', easy: '😐轻松' };

export default function Training() {
  const [records, setRecords] = useState<TrainingRecord[]>([]);
  const [actions, setActions] = useState<Record<string, string[]>>(DEFAULT_ACTIONS);
  const [showForm, setShowForm] = useState(false);
  const [bodyPart, setBodyPart] = useState('');
  const [sets, setSets] = useState<SetItem[]>([]);
  const [currentAction, setCurrentAction] = useState('');
  const [currentReps, setCurrentReps] = useState('');
  const [currentWeight, setCurrentWeight] = useState('');
  const [currentFeeling, setCurrentFeeling] = useState('normal');
  const [notes, setNotes] = useState('');
  const token = Taro.getStorageSync('token') || '';

  useEffect(() => { loadRecords(); loadActions(); }, []);

  const loadActions = async () => {
    try {
      const data = await trainingAPI.actions();
      if (data?.actions && Object.keys(data.actions).length > 0) {
        setActions(data.actions);
      }
    } catch (e) { console.log('加载动作库失败，使用默认数据', e); }
  };

  const loadRecords = async () => {
    try {
      const data = await trainingAPI.records(token);
      setRecords(data?.items || []);
    } catch (e) { console.log('加载失败', e); }
  };

  const addSet = () => {
    if (!currentAction) {
      Taro.showToast({ title: '请选择动作', icon: 'none' });
      return;
    }
    setSets([...sets, {
      set_order: sets.length + 1,
      action_name: currentAction,
      reps: parseFloat(currentReps) || 0,
      weight: parseFloat(currentWeight) || 0,
      rest_seconds: 60,
      feeling: currentFeeling,
      notes: '',
    }]);
    setCurrentReps('');
    setCurrentWeight('');
  };

  const removeSet = (idx: number) => {
    setSets(sets.filter((_, i) => i !== idx));
  };

  const handleSave = async () => {
    if (sets.length === 0) {
      Taro.showToast({ title: '请至少添加一组训练', icon: 'none' });
      return;
    }
    try {
      const today = new Date().toISOString();
      await trainingAPI.create(token, {
        training_date: today,
        body_part: bodyPart,
        duration: sets.length * 3,
        notes,
        sets: sets.map((s, i) => ({ ...s, set_order: i + 1 })),
      });
      Taro.showToast({ title: '训练记录保存成功', icon: 'success' });
      setShowForm(false);
      setSets([]);
      setBodyPart('');
      setNotes('');
      loadRecords();
    } catch (e: any) {
      Taro.showToast({ title: e.message, icon: 'none' });
    }
  };

  return (
    <View className="training-page">
      <View className="page-header">
        <Text className="page-title">训练记录</Text>
        <Button className="create-btn" onClick={() => setShowForm(!showForm)}>
          {showForm ? '取消' : '+ 开始训练'}
        </Button>
      </View>

      {showForm && (
        <View className="training-form">
          <Text className="form-section-title">选择训练部位</Text>
          <View className="body-parts">
            {Object.keys(actions).map(part => (
              <View
                key={part}
                className={`part-chip ${bodyPart === part ? 'active' : ''}`}
                onClick={() => setBodyPart(part)}
              >
                <Text>{part}</Text>
              </View>
            ))}
          </View>

          <Text className="form-section-title">添加训练组</Text>
          <View className="action-select">
            {bodyPart && actions[bodyPart]?.map(action => (
              <View
                key={action}
                className={`action-chip ${currentAction === action ? 'active' : ''}`}
                onClick={() => setCurrentAction(action)}
              >
                <Text>{action}</Text>
              </View>
            ))}
          </View>

          <View className="set-inputs">
            <View className="input-group">
              <Text className="input-label">次数</Text>
              <Input className="form-input" type="digit" placeholder="次数" value={currentReps} onInput={e => setCurrentReps(e.detail.value)} />
            </View>
            <View className="input-group">
              <Text className="input-label">重量(kg)</Text>
              <Input className="form-input" type="digit" placeholder="重量" value={currentWeight} onInput={e => setCurrentWeight(e.detail.value)} />
            </View>
            <View className="input-group">
              <Text className="input-label">感受</Text>
              <View className="feeling-row">
                {FEELINGS.map(f => (
                  <View key={f} className={`feeling-chip ${currentFeeling === f ? 'active' : ''}`} onClick={() => setCurrentFeeling(f)}>
                    <Text>{FEELING_LABELS[f]}</Text>
                  </View>
                ))}
              </View>
            </View>
          </View>
          <Button className="add-set-btn" onClick={addSet}>添加此组</Button>

          {sets.length > 0 && (
            <View className="sets-preview">
              <Text className="form-section-title">已添加 ({sets.length} 组)</Text>
              {sets.map((s, i) => (
                <View key={i} className="set-item">
                  <Text className="set-info">
                    {s.set_order}. {s.action_name} {s.reps > 0 ? `${s.reps}次` : '力竭'} {s.weight > 0 ? `${s.weight}kg` : ''}
                  </Text>
                  <Text className="set-remove" onClick={() => removeSet(i)}>×</Text>
                </View>
              ))}
            </View>
          )}

          <Input className="form-input" placeholder="备注（选填）" value={notes} onInput={e => setNotes(e.detail.value)} />
          <Button className="save-btn" onClick={handleSave}>保存训练记录</Button>
        </View>
      )}

      <Text className="section-title">历史记录</Text>
      {records.slice(0, 10).map(record => (
        <View key={record.id} className="record-card">
          <View className="record-header">
            <Text className="record-date">{record.training_date?.split('T')[0]}</Text>
            <Text className="record-body-part">{record.body_part || '训练'}</Text>
          </View>
          <View className="record-sets">
            {record.sets?.map((s, i) => (
              <Text key={i} className="record-set">
                {s.action_name} {s.reps > 0 ? `${s.reps}次` : '力竭'} {s.weight > 0 ? `${s.weight}kg` : ''}
              </Text>
            ))}
          </View>
        </View>
      ))}
      {records.length === 0 && <Text className="empty-text">暂无训练记录</Text>}
    </View>
  );
}
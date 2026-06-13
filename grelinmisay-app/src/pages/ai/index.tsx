import { useState, useEffect } from 'react';
import { View, Text, Input, Button, ScrollView, Textarea } from '@tarojs/components';
import Taro from '@tarojs/taro';
import { aiAPI } from '../../services/api';
import './index.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function AI() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const token = Taro.getStorageSync('token') || '';

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const data = await aiAPI.chat(token, input);
      const aiMsg: Message = { role: 'assistant', content: data?.reply || '暂无回复' };
      setMessages(prev => [...prev, aiMsg]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'AI 服务暂时不可用' }]);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    '帮我制定一个减脂计划',
    '今天练胸，推荐什么动作',
    '怎么坚持目标',
    '推荐一套背部训练',
  ];

  return (
    <View className="ai-page">
      <View className="page-header">
        <Text className="page-title">AI 助手</Text>
      </View>

      <ScrollView className="chat-list" scrollY scrollWithAnimation>
        {messages.length === 0 && (
          <View className="welcome">
            <Text className="welcome-title">你好，我是 GrelinMisay AI 助手</Text>
            <Text className="welcome-subtitle">我可以帮你制定健身计划、推荐训练动作、管理目标</Text>
            <View className="suggestions">
              {suggestions.map((s, i) => (
                <View key={i} className="suggestion-chip" onClick={() => setInput(s)}>
                  <Text>{s}</Text>
                </View>
              ))}
            </View>
          </View>
        )}
        {messages.map((msg, idx) => (
          <View key={idx} className={`chat-msg ${msg.role}`}>
            <Text className="chat-role">{msg.role === 'user' ? '我' : 'AI'}</Text>
            <View className="chat-bubble">
              <Text className="chat-content">{msg.content}</Text>
            </View>
          </View>
        ))}
        {loading && (
          <View className="chat-msg assistant">
            <Text className="chat-role">AI</Text>
            <View className="chat-bubble">
              <Text className="chat-content">思考中...</Text>
            </View>
          </View>
        )}
      </ScrollView>

      <View className="chat-input-bar">
        <Input
          className="chat-input"
          placeholder="输入消息..."
          value={input}
          onInput={e => setInput(e.detail.value)}
          onConfirm={handleSend}
        />
        <Button className="send-btn" onClick={handleSend} loading={loading}>
          发送
        </Button>
      </View>
    </View>
  );
}
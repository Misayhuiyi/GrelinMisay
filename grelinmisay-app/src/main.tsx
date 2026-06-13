import React from 'react';
import ReactDOM from 'react-dom/client';
import AppRouter from './taro-adapter/router';
import './app.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppRouter />
  </React.StrictMode>
);
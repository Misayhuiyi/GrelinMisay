import React from 'react';

// Taro 组件到 HTML 的适配层

export const View: React.FC<React.HTMLAttributes<HTMLDivElement> & { style?: any }> = (props) => {
  const { children, ...rest } = props;
  return <div {...rest}>{children}</div>;
};

export const Text: React.FC<React.HTMLAttributes<HTMLSpanElement>> = (props) => {
  const { children, ...rest } = props;
  return <span {...rest}>{children}</span>;
};

export const ScrollView: React.FC<React.HTMLAttributes<HTMLDivElement> & {
  scrollY?: boolean;
  scrollWithAnimation?: boolean;
  style?: any;
}> = (props) => {
  const { children, scrollY, ...rest } = props;
  const style: React.CSSProperties = {
    overflowY: scrollY ? 'auto' : 'visible',
    ...(props.style || {}),
  };
  return <div {...rest} style={style}>{children}</div>;
};

export const Input: React.FC<React.InputHTMLAttributes<HTMLInputElement> & {
  onInput?: (e: any) => void;
  maxlength?: number;
  type?: string;
}> = (props) => {
  const { onInput, maxlength, ...rest } = props;
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onInput) {
      onInput({ detail: { value: e.target.value } });
    }
  };
  return <input {...rest} maxLength={maxlength} onChange={handleChange} />;
};

export const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean;
  onClick?: (e: any) => void;
}> = (props) => {
  const { loading, children, disabled, onClick, ...rest } = props;
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading ? '加载中...' : children}
    </button>
  );
};

export const Textarea: React.FC<React.TextareaHTMLAttributes<HTMLTextAreaElement> & {
  onInput?: (e: any) => void;
  maxlength?: number;
}> = (props) => {
  const { onInput, maxlength, ...rest } = props;
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (onInput) {
      onInput({ detail: { value: e.target.value } });
    }
  };
  return <textarea {...rest} maxLength={maxlength} onChange={handleChange} />;
};
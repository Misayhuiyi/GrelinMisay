import { Component, PropsWithChildren } from 'react';
import './app.css';

class App extends Component<PropsWithChildren> {
  componentDidMount() {
    console.log('GrelinMisay App 启动');
  }

  render() {
    return this.props.children;
  }
}

export default App;
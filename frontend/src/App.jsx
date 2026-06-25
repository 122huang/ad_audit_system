import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  AuditOutlined,
  FileTextOutlined,
  BookOutlined,
  AlertOutlined,
  DashboardOutlined,
  PictureOutlined,
  VideoCameraOutlined
} from '@ant-design/icons'
import Dashboard from './pages/Dashboard'
import TextAudit from './pages/TextAudit'
import ImageAudit from './pages/ImageAudit'
import VideoAudit from './pages/VideoAudit'
import Knowledge from './pages/Knowledge'
import Rules from './pages/Rules'
import Cases from './pages/Cases'

const { Header, Sider, Content } = Layout

function App() {
  const [collapsed, setCollapsed] = React.useState(false)
  const [selectedKey, setSelectedKey] = React.useState('dashboard')

  const menuItems = [
    { key: 'dashboard', icon: <DashboardOutlined />, label: '首页' },
    { key: 'audit', icon: <AuditOutlined />, label: '文字审核' },
    { key: 'image-audit', icon: <PictureOutlined />, label: '图片审核' },
    { key: 'video-audit', icon: <VideoCameraOutlined />, label: '视频审核' },
    { key: 'knowledge', icon: <BookOutlined />, label: '知识库管理' },
    { key: 'rules', icon: <AlertOutlined />, label: '法规规则' },
    { key: 'cases', icon: <FileTextOutlined />, label: '案例库' }
  ]

  const renderContent = () => {
    switch (selectedKey) {
      case 'dashboard':
        return <Dashboard onNavigate={setSelectedKey} />
      case 'audit':
        return <TextAudit />
      case 'image-audit':
        return <ImageAudit />
      case 'video-audit':
        return <VideoAudit />
      case 'knowledge':
        return <Knowledge />
      case 'rules':
        return <Rules />
      case 'cases':
        return <Cases />
      default:
        return <Dashboard onNavigate={setSelectedKey} />
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div className="logo">审核宝</div>
        <Menu
          theme="dark"
          selectedKeys={[selectedKey]}
          mode="inline"
          items={menuItems}
          onClick={({ key }) => setSelectedKey(key)}
        />
      </Sider>
      <Layout className="site-layout">
        <Header style={{ padding: '0 24px', background: '#fff', display: 'flex', alignItems: 'center' }}>
          <h2 style={{ margin: 0, color: '#1890ff' }}>广告审核宝 - 多法域合规审核系统</h2>
        </Header>
        <Content style={{ margin: '16px', padding: '24px', background: '#fff', minHeight: 280 }}>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  )
}

export default App

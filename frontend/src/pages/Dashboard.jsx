import React from 'react'
import { Card, Row, Col, Statistic, Button, Typography, Space, Tag } from 'antd'
import { AuditOutlined, BookOutlined, AlertOutlined, FileTextOutlined, ArrowRightOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography

const Dashboard = ({ onNavigate }) => {
  return (
    <div>
      <Title level={3}>欢迎使用广告审核宝</Title>
      <Paragraph type="secondary">
        多法域广告合规智能审核，支持文字/图片/视频广告，覆盖新马泰、日韩、澳洲、印度市场
      </Paragraph>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="支持法域" value={7} suffix="个" prefix={<AlertOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="审核模式" value="文字/图片/视频" prefix={<AuditOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="行业类目" value="小家电" prefix={<BookOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="法规校验" value="三重校验" prefix={<FileTextOutlined />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="快速开始" extra={<Tag color="blue">推荐</Tag>}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button type="primary" size="large" icon={<AuditOutlined />} onClick={() => onNavigate('audit')}>
                开始文字广告审核 <ArrowRightOutlined />
              </Button>
              <Button size="large" icon={<BookOutlined />} onClick={() => onNavigate('knowledge')}>
                导入你的审核经验知识库
              </Button>
              <Button size="large" icon={<AlertOutlined />} onClick={() => onNavigate('rules')}>
                查看法规规则库
              </Button>
            </Space>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="系统功能">
            <Space direction="vertical">
              <div>✅ 文字广告智能审核（关键词+正则匹配）</div>
              <div>✅ 个人经验知识库（文档上传/自定义规则/案例库）</div>
              <div>✅ 三重法规校验机制（防AI幻觉）</div>
              <div>✅ 历史违规案例自动匹配</div>
              <div>✅ 支持7个法域：新马泰、日韩、澳洲、印度</div>
              <div>✅ 所有规则均需人工复核确认</div>
            </Space>
          </Card>
        </Col>
      </Row>

      <Card title="法域覆盖" style={{ marginTop: 24 }}>
        <Row gutter={[16, 16]}>
          <Col span={6}><Tag color="blue">🇸🇬 新加坡 SG</Tag></Col>
          <Col span={6}><Tag color="blue">🇲🇾 马来西亚 MY</Tag></Col>
          <Col span={6}><Tag color="orange">🇹🇭 泰国 TH</Tag></Col>
          <Col span={6}><Tag color="orange">🇦🇺 澳洲 AU</Tag></Col>
          <Col span={6}><Tag color="green">🇯🇵 日本 JP</Tag></Col>
          <Col span={6}><Tag color="green">🇰🇷 韩国 KR</Tag></Col>
          <Col span={6}><Tag color="purple">🇮🇳 印度 IN</Tag></Col>
        </Row>
      </Card>
    </div>
  )
}

export default Dashboard

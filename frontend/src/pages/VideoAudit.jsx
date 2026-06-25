import React, { useState } from 'react'
import {
  Card, Form, Input, Button, Select, Space, Tag, Result, Typography,
  Upload, List, Alert, Divider, Image, message, Row, Col, Timeline
} from 'antd'
import {
  VideoCameraOutlined, UploadOutlined, AuditOutlined,
  CheckCircleOutlined, ExclamationCircleOutlined, CloseCircleOutlined,
  PlayCircleOutlined, SoundOutlined, FileTextOutlined
} from '@ant-design/icons'
import { auditAPI } from '../services/api'

const { TextArea } = Input
const { Title, Text, Paragraph } = Typography

const REGIONS = [
  { value: 'SG', label: '🇸🇬 新加坡' },
  { value: 'MY', label: '🇲🇾 马来西亚' },
  { value: 'TH', label: '🇹🇭 泰国' },
  { value: 'AU', label: '🇦🇺 澳洲' },
  { value: 'JP', label: '🇯🇵 日本' },
  { value: 'KR', label: '🇰🇷 韩国' },
  { value: 'IN', label: '🇮🇳 印度' }
]

const RISK_COLORS = {
  low: { color: 'success', text: '低风险', icon: <CheckCircleOutlined /> },
  medium: { color: 'warning', text: '中等风险', icon: <ExclamationCircleOutlined /> },
  high: { color: 'error', text: '高风险', icon: <CloseCircleOutlined /> },
  critical: { color: 'error', text: '严重违规', icon: <CloseCircleOutlined /> }
}

const VideoAudit = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const onFinish = async (values) => {
    setLoading(true)
    setResult(null)
    try {
      const response = await auditAPI.auditVideo({
        video_script: values.video_script || '',
        video_description: values.video_description || '',
        regions: values.regions || ['SG'],
        category: values.category || '小家电',
        advert_name: values.advert_name || '',
        title: values.title || '视频广告'
      })
      setResult(response)
      message.success('视频审核完成')
    } catch (error) {
      message.error('审核失败: ' + (error.message || '未知错误'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Title level={4}><VideoCameraOutlined /> 视频审核</Title>
      <Paragraph type="secondary">
        输入视频脚本、旁白文案、字幕内容，系统自动审核视频广告的合规性
      </Paragraph>

      <Card style={{ marginBottom: 24 }}>
        <Timeline style={{ marginBottom: 24 }}>
          <Timeline.Item dot={<FileTextOutlined />}>输入视频脚本/旁白/字幕文案</Timeline.Item>
          <Timeline.Item dot={<SoundOutlined />}>描述视频画面内容</Timeline.Item>
          <Timeline.Item dot={<AuditOutlined />}>系统自动审核合规性</Timeline.Item>
        </Timeline>

        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ regions: ['SG'], category: '小家电' }}>
          <Form.Item
            name="video_script"
            label="视频脚本/旁白/字幕文案"
            rules={[{ required: true, message: '请输入视频的文案内容' }]}
          >
            <TextArea rows={8} placeholder={`输入视频中的完整文案，包括：
- 旁白配音文字
- 字幕内容
- 画面上出现的文字
- 产品说明和参数
- 促销话术
- 免责声明文字`}
            />
          </Form.Item>

          <Form.Item name="video_description" label="视频画面描述">
            <TextArea rows={3} placeholder="描述视频画面内容，如：产品展示、使用场景、对比演示、客户评价、开箱过程..." />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="category" label="产品品类">
                <Select options={[
                  { value: '小家电', label: '小家电' },
                  { value: '美妆个护', label: '美妆个护' },
                  { value: '婴童', label: '婴童' },
                  { value: '保健食品', label: '保健食品' },
                  { value: '服装', label: '服装' },
                  { value: '数码', label: '数码' },
                ]} />
              </Form.Item>
            </Col>
            <Col span={16}>
              <Form.Item name="regions" label="目标法域" rules={[{ required: true }]}>
                <Select mode="multiple" options={REGIONS} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} size="large" icon={<AuditOutlined />} block>
              开始审核
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {result && (
        <Card
          title="审核结果"
          style={{ borderLeft: `4px solid ${result.overall_risk === 'critical' || result.overall_risk === 'high' ? '#ff4d4f' : result.overall_risk === 'medium' ? '#faad14' : '#52c41a'}` }}
        >
          <Result
            status={result.overall_status === 'rejected' ? 'error' : result.overall_status === 'warning' ? 'warning' : 'success'}
            title={`${RISK_COLORS[result.overall_risk]?.text} — ${result.overall_status === 'rejected' ? '审核拒绝' : result.overall_status === 'warning' ? '需要注意' : '通过'}`}
          />

          {result.hard_violations?.length > 0 && (
            <Card title="违规详情" size="small" style={{ marginBottom: 16 }}>
              <List
                dataSource={result.hard_violations}
                renderItem={(item, idx) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Tag color={item.severity === 'critical' || item.severity === 'high' ? 'red' : 'orange'}>{item.severity}</Tag>}
                      title={<Space><Text strong>{item.rule_name || item.source}</Text><Tag>{item.matched_text}</Tag></Space>}
                      description={item.violation_desc || item.suggestion}
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}

          {result.similar_cases?.length > 0 && (
            <Card title="相似案例" size="small">
              <List
                dataSource={result.similar_cases}
                renderItem={(item, idx) => (
                  <List.Item>
                    <List.Item.Meta
                      title={item.title}
                      description={item.decision}
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}
        </Card>
      )}
    </div>
  )
}

export default VideoAudit
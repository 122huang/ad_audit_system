import React, { useState } from 'react'
import {
  Card, Form, Input, Button, Select, Space, Tag, Result, Typography,
  Upload, List, Alert, Divider, Image, message, Row, Col, Descriptions
} from 'antd'
import {
  PictureOutlined, UploadOutlined, AuditOutlined,
  CheckCircleOutlined, ExclamationCircleOutlined, CloseCircleOutlined
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

const ImageAudit = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [preview, setPreview] = useState(null)

  const onFinish = async (values) => {
    setLoading(true)
    setResult(null)
    try {
      const formData = new FormData()
      if (values.image?.fileList?.[0]?.originFileObj) {
        formData.append('image', values.image.fileList[0].originFileObj)
      }
      formData.append('image_description', values.image_description || '')
      formData.append('ocr_text', values.ocr_text || '')
      formData.append('regions', (values.regions || ['SG']).join(','))
      formData.append('category', values.category || '小家电')
      formData.append('advert_name', values.advert_name || '')
      formData.append('title', values.title || '图片广告')

      const response = await auditAPI.auditImage(formData)
      setResult(response)
      message.success('图片审核完成')
    } catch (error) {
      message.error('审核失败: ' + (error.message || '未知错误'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Title level={4}><PictureOutlined /> 图片审核</Title>
      <Paragraph type="secondary">
        上传广告图片，输入图片上的文字内容或图片描述，系统自动审核合规性
      </Paragraph>

      <Card style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ regions: ['SG'], category: '小家电' }}>
          <Form.Item name="image" label="上传广告图片" valuePropName="fileList" getValueFromEvent={(e) => e?.fileList ? [e.fileList[e.fileList.length - 1]] : []}>
            <Upload
              listType="picture-card"
              maxCount={1}
              beforeUpload={(file) => {
                const reader = new FileReader()
                reader.onload = (e) => setPreview(e.target.result)
                reader.readAsDataURL(file)
                return false
              }}
              accept="image/*"
            >
              <div>
                <UploadOutlined />
                <div style={{ marginTop: 8 }}>上传图片</div>
              </div>
            </Upload>
          </Form.Item>

          {preview && (
            <div style={{ marginBottom: 16 }}>
              <Image src={preview} alt="预览" style={{ maxHeight: 200 }} />
            </div>
          )}

          <Form.Item name="ocr_text" label="图片上的文字内容">
            <TextArea rows={3} placeholder="输入图片上出现的所有文字/文案，如：标题、标语、参数、小字说明等..." />
          </Form.Item>

          <Form.Item name="image_description" label="图片内容描述">
            <TextArea rows={2} placeholder="描述图片内容，如：产品主图、使用场景图、功能对比图..." />
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

export default ImageAudit
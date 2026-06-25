import React, { useState, useEffect } from 'react'
import { Card, Table, Tag, Typography, Button, Modal, Form, Input, Select, Space, message, List } from 'antd'
import { FileTextOutlined, PlusOutlined } from '@ant-design/icons'
import { knowledgeAPI } from '../services/api'

const { Title, Paragraph } = Typography
const { TextArea } = Input

const REGIONS_OPTIONS = [
  { value: '', label: '通用' },
  { value: 'SG', label: '🇸🇬 新加坡' },
  { value: 'MY', label: '🇲🇾 马来西亚' },
  { value: 'TH', label: '🇹🇭 泰国' },
  { value: 'AU', label: '🇦🇺 澳洲' }
]

const DECISIONS = [
  { value: '通过', label: '通过' },
  { value: '整改后通过', label: '整改后通过' },
  { value: '驳回', label: '驳回' }
]

const Cases = () => {
  const [cases, setCases] = useState([])
  const [modalVisible, setModalVisible] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadCases()
  }, [])

  const loadCases = async () => {
    try {
      const data = await knowledgeAPI.listCases()
      setCases(data || [])
    } catch (e) {
      console.error(e)
    }
  }

  const handleCreate = async (values) => {
    setLoading(true)
    try {
      await knowledgeAPI.createCase({
        title: values.title,
        material_type: 'text',
        violation_type: values.violation_type,
        description: values.description,
        decision: values.decision,
        content_text: values.content_text,
        region_code: values.region_code || null,
        before_edit: values.before_edit ? values.before_edit.split('\n').map(s => s.trim()).filter(s => s) : [],
        after_edit: values.after_edit ? values.after_edit.split('\n').map(s => s.trim()).filter(s => s) : [],
        reviewer_notes: values.reviewer_notes,
        tags: values.tags ? values.tags.split(',').map(t => t.trim()) : []
      })
      message.success('案例创建成功')
      setModalVisible(false)
      form.resetFields()
      loadCases()
    } catch (e) {
      message.error('创建失败: ' + (e.message || ''))
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    { title: '案例标题', dataIndex: 'title', key: 'title' },
    { title: '法域', dataIndex: 'region_code', key: 'region_code', render: r => r ? <Tag>{r}</Tag> : <Tag>通用</Tag> },
    { title: '违规类型', dataIndex: 'violation_type', key: 'violation_type' },
    { title: '处理结果', dataIndex: 'decision', key: 'decision', render: d => <Tag color="blue">{d}</Tag> },
    { title: '命中次数', dataIndex: 'hit_count', key: 'hit_count' },
    {
      title: '详情', key: 'detail', render: (_, r) => (
        <div>
          {r.before_edit && r.before_edit.length > 0 && (
            <div><Text type="danger" delete>{r.before_edit[0]}</Text></div>
          )}
          {r.after_edit && r.after_edit.length > 0 && (
            <div><Text type="success" mark>{r.after_edit[0]}</Text></div>
          )}
        </div>
      )
    }
  ]

  return (
    <div>
      <Title level={4}><FileTextOutlined /> 历史案例库</Title>
      <Paragraph type="secondary">
        录入过往审核案例，系统在审核时会自动匹配相似案例并给出修改建议
      </Paragraph>

      <Card
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>录入案例</Button>}
      >
        <Table columns={columns} dataSource={cases} rowKey="id" pagination={{ pageSize: 10 }} />
      </Card>

      <Modal
        title="录入违规案例"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="title" label="案例标题" rules={[{ required: true }]}>
            <Input placeholder="例如：空气净化器绝对化用语被罚案例" />
          </Form.Item>
          <Space style={{ width: '100%' }} size="middle">
            <Form.Item name="region_code" label="法域" initialValue="" style={{ flex: 1 }}>
              <Select options={REGIONS_OPTIONS} />
            </Form.Item>
            <Form.Item name="violation_type" label="违规类型" rules={[{ required: true }]} style={{ flex: 1 }}>
              <Input placeholder="如：绝对化用语" />
            </Form.Item>
            <Form.Item name="decision" label="处理结果" rules={[{ required: true }]} initialValue="整改后通过" style={{ flex: 1 }}>
              <Select options={DECISIONS} />
            </Form.Item>
          </Space>
          <Form.Item name="content_text" label="违规原文" rules={[{ required: true }]}>
            <TextArea rows={3} placeholder="输入违规的广告原文" />
          </Form.Item>
          <Form.Item name="before_edit" label="修改前（每行一个）">
            <TextArea rows={2} placeholder="违规表述，每行一个" />
          </Form.Item>
          <Form.Item name="after_edit" label="修改后（每行一个，与前面对应）">
            <TextArea rows={2} placeholder="修改后的合规表述" />
          </Form.Item>
          <Form.Item name="description" label="案例详情" rules={[{ required: true }]}>
            <TextArea rows={3} placeholder="案例背景、违规原因、处理结果说明" />
          </Form.Item>
          <Form.Item name="reviewer_notes" label="审核备注">
            <TextArea rows={2} placeholder="审核经验总结、注意事项" />
          </Form.Item>
          <Form.Item name="tags" label="标签（逗号分隔）">
            <Input placeholder="如：绝对化用语,新加坡,空气净化器" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>保存案例</Button>
              <Button onClick={() => setModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Cases

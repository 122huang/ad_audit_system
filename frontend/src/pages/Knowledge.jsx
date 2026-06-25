import React, { useState, useEffect } from 'react'
import { Card, Tabs, Typography, Button, Upload, Form, Input, Select, Table, Space, Tag, message, Modal, Popconfirm } from 'antd'
import { UploadOutlined, PlusOutlined, BookOutlined, AlertOutlined, DeleteOutlined, FileTextOutlined } from '@ant-design/icons'
import { knowledgeAPI } from '../services/api'

const { Title, Paragraph } = Typography
const { TextArea } = Input

const DOC_TYPES = [
  { value: 'regulation', label: '法规文档' },
  { value: 'internal', label: '内部规范' },
  { value: 'case', label: '案例文档' },
  { value: 'guide', label: '审核指南' }
]

const REGIONS = [
  { value: '', label: '通用（不限法域）' },
  { value: 'SG', label: '🇸🇬 新加坡' },
  { value: 'MY', label: '🇲🇾 马来西亚' },
  { value: 'TH', label: '🇹🇭 泰国' },
  { value: 'AU', label: '🇦🇺 澳洲' },
  { value: 'JP', label: '🇯🇵 日本' },
  { value: 'KR', label: '🇰🇷 韩国' },
  { value: 'IN', label: '🇮🇳 印度' }
]

const RULE_TYPES = [
  { value: 'prohibited', label: '禁止（硬阻断）' },
  { value: 'warn', label: '警告（提示）' },
  { value: 'suggest', label: '建议（参考）' }
]

const Knowledge = () => {
  const [activeTab, setActiveTab] = useState('docs')
  const [docModal, setDocModal] = useState(false)
  const [ruleModal, setRuleModal] = useState(false)
  const [docs, setDocs] = useState([])
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(false)
  const [docForm] = Form.useForm()
  const [ruleForm] = Form.useForm()

  useEffect(() => {
    loadDocs()
    loadRules()
  }, [])

  const loadDocs = async () => {
    try {
      const data = await knowledgeAPI.listDocs()
      setDocs(data || [])
    } catch (e) {
      console.error(e)
    }
  }

  const loadRules = async () => {
    try {
      const data = await knowledgeAPI.listRules()
      setRules(data || [])
    } catch (e) {
      console.error(e)
    }
  }

  const handleCreateDocText = async (values) => {
    setLoading(true)
    try {
      await knowledgeAPI.createDocText({
        title: values.title,
        doc_type: values.doc_type,
        content_text: values.content,
        region_code: values.region_code || null,
        tags: values.tags ? values.tags.split(',').map(t => t.trim()) : []
      })
      message.success('文档创建成功')
      setDocModal(false)
      docForm.resetFields()
      loadDocs()
    } catch (e) {
      message.error('创建失败: ' + (e.message || ''))
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (options) => {
    const { file, onSuccess, onError } = options
    const formData = new FormData()
    formData.append('file', file)
    formData.append('doc_type', docForm.getFieldValue('doc_type') || 'internal')
    if (docForm.getFieldValue('region_code')) {
      formData.append('region_code', docForm.getFieldValue('region_code'))
    }
    try {
      await knowledgeAPI.uploadDoc(formData)
      message.success('文档上传成功')
      onSuccess()
      setDocModal(false)
      docForm.resetFields()
      loadDocs()
    } catch (e) {
      onError(e)
      message.error('上传失败')
    }
  }

  const handleCreateRule = async (values) => {
    setLoading(true)
    try {
      await knowledgeAPI.createRule({
        rule_name: values.rule_name,
        rule_type: values.rule_type,
        keywords: values.keywords ? values.keywords.split(',').map(k => k.trim()) : [],
        patterns: values.patterns ? values.patterns.split('\n').map(p => p.trim()).filter(p => p) : [],
        description: values.description,
        suggestion: values.suggestion,
        region_code: values.region_code || null
      })
      message.success('规则创建成功')
      setRuleModal(false)
      ruleForm.resetFields()
      loadRules()
    } catch (e) {
      message.error('创建失败: ' + (e.message || ''))
    } finally {
      setLoading(false)
    }
  }

  const deleteDoc = async (id) => {
    try {
      await knowledgeAPI.deleteDoc(id)
      message.success('已删除')
      loadDocs()
    } catch (e) {
      message.error('删除失败')
    }
  }

  const deleteRule = async (id) => {
    try {
      await knowledgeAPI.deleteRule(id)
      message.success('已删除')
      loadRules()
    } catch (e) {
      message.error('删除失败')
    }
  }

  const docColumns = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '类型', dataIndex: 'doc_type', key: 'doc_type', render: t => <Tag color="blue">{DOC_TYPES.find(d => d.value === t)?.label || t}</Tag> },
    { title: '分块数', dataIndex: 'chunk_count', key: 'chunk_count' },
    { title: '已索引', dataIndex: 'is_indexed', key: 'is_indexed', render: i => i ? <Tag color="green">是</Tag> : <Tag color="orange">否</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: t => t ? new Date(t).toLocaleString() : '' },
    {
      title: '操作', key: 'action', render: (_, r) => (
        <Popconfirm title="确认删除？" onConfirm={() => deleteDoc(r.id)}>
          <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      )
    }
  ]

  const ruleColumns = [
    { title: '规则名称', dataIndex: 'rule_name', key: 'rule_name' },
    { title: '编码', dataIndex: 'rule_code', key: 'rule_code' },
    { title: '类型', dataIndex: 'rule_type', key: 'rule_type', render: t => {
      const color = t === 'prohibited' ? 'red' : 'orange'
      return <Tag color={color}>{RULE_TYPES.find(r => r.value === t)?.label || t}</Tag>
    }},
    { title: '关键词', dataIndex: 'keywords', key: 'keywords', render: k => (k || []).map(kw => <Tag key={kw}>{kw}</Tag>) },
    { title: '命中次数', dataIndex: 'hit_count', key: 'hit_count' },
    {
      title: '操作', key: 'action', render: (_, r) => (
        <Popconfirm title="确认删除？" onConfirm={() => deleteRule(r.id)}>
          <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      )
    }
  ]

  return (
    <div>
      <Title level={4}><BookOutlined /> 知识库管理</Title>
      <Paragraph type="secondary">
        在这里导入你的审核经验文档、自定义审核规则，系统会在审核时自动参考你的知识
      </Paragraph>

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        {
          key: 'docs',
          label: <span><BookOutlined />经验文档</span>,
          children: (
            <Card
              title="文档管理"
              extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setDocModal(true)}>添加文档</Button>}
            >
              <Table columns={docColumns} dataSource={docs} rowKey="id" pagination={{ pageSize: 10 }} />
            </Card>
          )
        },
        {
          key: 'rules',
          label: <span><AlertOutlined />经验规则</span>,
          children: (
            <Card
              title="自定义规则"
              extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setRuleModal(true)}>添加规则</Button>}
            >
              <Table columns={ruleColumns} dataSource={rules} rowKey="id" pagination={{ pageSize: 10 }} />
            </Card>
          )
        }
      ]} />

      <Modal
        title="添加文档"
        open={docModal}
        onCancel={() => setDocModal(false)}
        footer={null}
        width={700}
      >
        <Form form={docForm} layout="vertical" onFinish={handleCreateDocText}>
          <Form.Item name="title" label="文档标题" rules={[{ required: true }]}>
            <Input placeholder="例如：小家电新加坡市场审核要点" />
          </Form.Item>
          <Form.Item name="doc_type" label="文档类型" rules={[{ required: true }]} initialValue="internal">
            <Select options={DOC_TYPES} />
          </Form.Item>
          <Form.Item name="region_code" label="适用法域" initialValue="">
            <Select options={REGIONS} />
          </Form.Item>
          <Form.Item name="tags" label="标签（逗号分隔）">
            <Input placeholder="例如：能效,绝对化用语,新加坡" />
          </Form.Item>
          <Form.Item name="content" label="文档内容（直接输入文本）">
            <TextArea rows={6} placeholder="粘贴你的审核笔记、经验总结..." />
          </Form.Item>
          <Form.Item label="或上传文件">
            <Upload customRequest={handleUpload} accept=".pdf,.docx,.xlsx,.txt,.md" maxCount={1}>
              <Button icon={<UploadOutlined />}>选择文件 (PDF/Word/Excel/TXT)</Button>
            </Upload>
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>保存文本</Button>
              <Button onClick={() => setDocModal(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="添加经验规则"
        open={ruleModal}
        onCancel={() => setRuleModal(false)}
        footer={null}
        width={600}
      >
        <Form form={ruleForm} layout="vertical" onFinish={handleCreateRule}>
          <Form.Item name="rule_name" label="规则名称" rules={[{ required: true }]}>
            <Input placeholder="例如：能效声明必须附检测报告" />
          </Form.Item>
          <Form.Item name="rule_type" label="规则类型" rules={[{ required: true }]} initialValue="warn">
            <Select options={RULE_TYPES} />
          </Form.Item>
          <Form.Item name="region_code" label="适用法域" initialValue="">
            <Select options={REGIONS} />
          </Form.Item>
          <Form.Item name="keywords" label="触发关键词（逗号分隔）" rules={[{ required: true, message: '请输入至少一个关键词' }]}>
            <Input placeholder="例如：能效,最节能,顶级能效" />
          </Form.Item>
          <Form.Item name="patterns" label="正则表达式（可选，每行一个）">
            <TextArea rows={3} placeholder="例如：\d+%节能" />
          </Form.Item>
          <Form.Item name="description" label="违规描述/原因" rules={[{ required: true }]}>
            <TextArea rows={2} placeholder="为什么这是一个问题？" />
          </Form.Item>
          <Form.Item name="suggestion" label="修改建议">
            <TextArea rows={2} placeholder="建议如何修改？" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>保存规则</Button>
              <Button onClick={() => setRuleModal(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Knowledge

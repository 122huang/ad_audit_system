import React, { useState, useEffect } from 'react'
import { Card, Table, Tag, Typography, Select, Space, Button, Modal, Form, Input, message, Descriptions, Alert } from 'antd'
import { AlertOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { ruleAPI, regionAPI } from '../services/api'

const { Title, Paragraph, Text } = Typography
const { TextArea } = Input

const REGIONS_MAP = {
  SG: '🇸🇬 新加坡',
  MY: '🇲🇾 马来西亚',
  TH: '🇹🇭 泰国',
  AU: '🇦🇺 澳洲',
  JP: '🇯🇵 日本',
  KR: '🇰🇷 韩国',
  IN: '🇮🇳 印度'
}

const Rules = () => {
  const [rules, setRules] = useState([])
  const [regions, setRegions] = useState([])
  const [selectedRegion, setSelectedRegion] = useState()
  const [validateModal, setValidateModal] = useState(false)
  const [validateResult, setValidateResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadRegions()
    loadRules()
  }, [])

  const loadRegions = async () => {
    try {
      const data = await regionAPI.list()
      setRegions(data || [])
    } catch (e) {
      console.error(e)
    }
  }

  const loadRules = async (regionCode) => {
    setLoading(true)
    try {
      const data = await ruleAPI.list({ region_code: regionCode })
      setRules(data || [])
    } catch (e) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleRegionChange = (value) => {
    setSelectedRegion(value)
    loadRules(value)
  }

  const handleValidate = async (values) => {
    setLoading(true)
    try {
      const result = await ruleAPI.validate(values)
      setValidateResult(result)
      message.success('校验完成')
    } catch (e) {
      message.error('校验失败')
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    { title: '规则编码', dataIndex: 'rule_code', key: 'rule_code', width: 150 },
    { title: '规则名称', dataIndex: 'rule_name', key: 'rule_name' },
    {
      title: '类型', dataIndex: 'rule_type', key: 'rule_type',
      render: t => {
        const colors = { prohibited: 'red', restricted: 'orange', required: 'blue', warn: 'gold' }
        const labels = { prohibited: '禁止', restricted: '限制', required: '要求', warn: '警告' }
        return <Tag color={colors[t]}>{labels[t] || t}</Tag>
      }
    },
    {
      title: '严重度', dataIndex: 'severity', key: 'severity',
      render: s => {
        const colors = { low: 'green', medium: 'orange', high: 'red', critical: 'red' }
        return <Tag color={colors[s]}>{s}</Tag>
      }
    },
    { title: '关键词', dataIndex: 'keywords', key: 'keywords', render: k => (k || []).slice(0, 5).map(kw => <Tag key={kw}>{kw}</Tag>) },
    {
      title: '审核状态', dataIndex: 'review_status', key: 'review_status',
      render: s => s === 'approved'
        ? <Tag color="green" icon={<CheckCircleOutlined />}>已审核</Tag>
        : <Tag color="orange" icon={<ExclamationCircleOutlined />}>待审核</Tag>
    },
    { title: '来源', dataIndex: 'source_url', key: 'source_url', render: u => u ? <a href={u} target="_blank" rel="noreferrer">原文链接</a> : '-' }
  ]

  return (
    <div>
      <Title level={4}><AlertOutlined /> 法规规则库</Title>
      <Paragraph type="secondary">
        所有法规规则均经过三重校验+人工复核，确保数据准确无误，杜绝AI幻觉
      </Paragraph>

      <Card
        extra={
          <Space>
            <Select
              placeholder="选择法域"
              style={{ width: 150 }}
              allowClear
              value={selectedRegion}
              onChange={handleRegionChange}
              options={Object.entries(REGIONS_MAP).map(([k, v]) => ({ value: k, label: v }))}
            />
            <Button type="primary" onClick={() => { setValidateModal(true); setValidateResult(null) }}>
              新规则校验
            </Button>
          </Space>
        }
      >
        <Table columns={columns} dataSource={rules} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
      </Card>

      <Modal
        title="新规则校验（防幻觉）"
        open={validateModal}
        onCancel={() => setValidateModal(false)}
        footer={null}
        width={700}
      >
        <Alert
          message="三重校验机制"
          description="所有新规则必须通过：1.来源真实性校验 2.内容准确性校验 3.逻辑一致性校验，再经人工复核后才能入库"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Form form={form} layout="vertical" onFinish={handleValidate}>
          <Form.Item name="region_code" label="法域" rules={[{ required: true }]}>
            <Select options={Object.entries(REGIONS_MAP).map(([k, v]) => ({ value: k, label: v }))} />
          </Form.Item>
          <Form.Item name="rule_code" label="规则编码" rules={[{ required: true }]}>
            <Input placeholder="例如：SG_PROHIBITED_003" />
          </Form.Item>
          <Form.Item name="rule_name" label="规则名称" rules={[{ required: true }]}>
            <Input placeholder="规则名称" />
          </Form.Item>
          <Form.Item name="keywords" label="关键词（逗号分隔）" rules={[{ required: true }]}>
            <Input placeholder="关键词必须能在原文中找到，否则会被判定为幻觉" />
          </Form.Item>
          <Form.Item name="description" label="规则描述" rules={[{ required: true }]}>
            <TextArea rows={3} placeholder="规则的详细描述，必须有原文依据" />
          </Form.Item>
          <Form.Item name="source_url" label="来源URL（必须是官方域名）" rules={[{ required: true }]}>
            <Input placeholder="https://www.csa.org.sg/..." />
          </Form.Item>
          <Form.Item name="source_content" label="原文内容片段" rules={[{ required: true }]}>
            <TextArea rows={4} placeholder="粘贴法规原文片段，系统将验证关键词是否在原文中" />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>运行校验</Button>
              <Button onClick={() => setValidateModal(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>

        {validateResult && (
          <Card title="校验结果" style={{ marginTop: 16 }}>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="来源校验">
                {validateResult.source_valid
                  ? <Tag color="green">通过</Tag>
                  : <Tag color="red">未通过</Tag>}
              </Descriptions.Item>
              <Descriptions.Item label="内容校验">
                {validateResult.content_valid
                  ? <Tag color="green">通过</Tag>
                  : <Tag color="red">未通过</Tag>}
              </Descriptions.Item>
              <Descriptions.Item label="逻辑校验">
                {validateResult.logic_valid
                  ? <Tag color="green">通过</Tag>
                  : <Tag color="red">未通过</Tag>}
              </Descriptions.Item>
            </Descriptions>

            {validateResult.issues && validateResult.issues.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Title level={5}>发现问题：</Title>
                {validateResult.issues.map((issue, idx) => (
                  <Alert
                    key={idx}
                    type={issue.level === 'critical' ? 'error' : 'warning'}
                    message={`[${issue.type}] ${issue.message}`}
                    style={{ marginBottom: 8 }}
                    showIcon
                  />
                ))}
              </div>
            )}

            {validateResult.passed && (
              <Alert
                message="校验通过，可以进入人工复核流程"
                type="success"
                showIcon
                style={{ marginTop: 16 }}
              />
            )}
          </Card>
        )}
      </Modal>
    </div>
  )
}

export default Rules

import React, { useState } from 'react'
import {
  Card, Form, Input, Button, Select, Space, Tag, Result, Spin, Typography,
  List, Alert, Divider, Steps, Badge, message, Table, Collapse, Descriptions
} from 'antd'
import {
  AuditOutlined, CheckCircleOutlined, ExclamationCircleOutlined,
  CloseCircleOutlined, SafetyCertificateOutlined, FileProtectOutlined,
  ExperimentOutlined, WarningOutlined, InfoCircleOutlined
} from '@ant-design/icons'
import { advancedAuditAPI } from '../services/api'

const { TextArea } = Input
const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse

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

const AdvancedAudit = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [r01Result, setR01Result] = useState(null)
  const [r02Loading, setR02Loading] = useState(false)
  const [r02Result, setR02Result] = useState(null)
  const [evidenceList, setEvidenceList] = useState([])

  // R01: 文案扫描
  const onR01Finish = async (values) => {
    setLoading(true)
    setR02Result(null)
    try {
      const response = await advancedAuditAPI.auditR01({
        text: values.text,
        regions: values.regions || ['SG'],
        category: values.category || '小家电'
      })
      setR01Result(response)
      message.success('R01 扫描完成')
    } catch (error) {
      message.error('审核失败: ' + (error.message || '未知错误'))
    } finally {
      setLoading(false)
    }
  }

  // R02: 证据审查
  const onR02Submit = async () => {
    if (!evidenceList.length) {
      message.warning('请至少添加一份证据文件')
      return
    }
    setR02Loading(true)
    try {
      const response = await advancedAuditAPI.auditR02({
        r01_result: r01Result,
        evidence_files: evidenceList
      })
      setR02Result(response)
      message.success('R02 证据审查完成')
    } catch (error) {
      message.error('审查失败: ' + (error.message || '未知错误'))
    } finally {
      setR02Loading(false)
    }
  }

  const addEvidence = (values) => {
    setEvidenceList([...evidenceList, {
      name: values.name,
      type: values.type || '',
      date: values.date || '',
      covers: values.covers || []
    }])
    message.success('证据已添加')
  }

  const delEvidence = (idx) => {
    setEvidenceList(evidenceList.filter((_, i) => i !== idx))
  }

  const riskInfo = r01Result ? (RISK_COLORS[r01Result.overall_risk] || RISK_COLORS.low) : null

  return (
    <div>
      <Title level={4}>
        <SafetyCertificateOutlined /> 高级审核（R01/R02 双轮）
      </Title>
      <Paragraph type="secondary">
        基于 ad-claim-review skill v4，采用 A-K 十一类风险体系 + 文字质检 + 证据充分性审查
      </Paragraph>

      <Steps current={r01Result ? (r02Result ? 2 : 1) : 0} size="small" style={{ marginBottom: 24 }}>
        <Steps.Step title="R01 文案扫描" description="A-K 风险分类" icon={<AuditOutlined />} />
        <Steps.Step title="R02 证据审查" description="五维度评估" icon={<ExperimentOutlined />} />
        <Steps.Step title="合规结论" description="可上线/修改后上线/不可上线" icon={<FileProtectOutlined />} />
      </Steps>

      {/* R01 输入区 */}
      <Card title="R01: 文案扫描" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" onFinish={onR01Finish} initialValues={{ regions: ['SG'], category: '小家电' }}>
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
          <Form.Item name="text" label="广告文案" rules={[{ required: true, message: '请输入广告文案' }]}>
            <TextArea rows={6} placeholder="输入待审核的广告文案、PDP描述、产品详情页文案等..." />
          </Form.Item>
          <Form.Item name="regions" label="目标法域" rules={[{ required: true }]}>
            <Select mode="multiple" options={REGIONS} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} size="large" icon={<AuditOutlined />}>
              开始 R01 扫描
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {loading && <Spin size="large" style={{ display: 'block', margin: '40px auto' }} tip="正在扫描 A-K 风险..." />}

      {/* R01 结果 */}
      {r01Result && !loading && (
        <div>
          <Card style={{ marginBottom: 16, borderLeft: `4px solid ${riskInfo?.color === 'error' ? '#ff4d4f' : riskInfo?.color === 'warning' ? '#faad14' : '#52c41a'}` }}>
            <Result
              status={r01Result.overall_risk === 'critical' || r01Result.overall_risk === 'high' ? 'error' : r01Result.overall_risk === 'medium' ? 'warning' : 'success'}
              title={`R01 扫描完成 — ${riskInfo?.text}`}
              subTitle={`共发现 ${r01Result.summary.total_issues} 个问题: 🔴${r01Result.summary.forced_count} 强制修改 / 🟡${r01Result.summary.biz_confirm_count} 业务确认 / 🟢${r01Result.summary.reminder_count} 仅提醒 / ✏️${r01Result.summary.text_quality_count} 文字质检`}
            />
          </Card>

          {/* 🔴 强制修改 */}
          {r01Result.forced_changes?.length > 0 && (
            <Card
              title={<Space><CloseCircleOutlined style={{ color: '#ff4d4f' }} /> 🔴 强制修改（{r01Result.forced_changes.length} 条）</Space>}
              style={{ marginBottom: 16, borderLeft: '4px solid #ff4d4f' }}
            >
              <List
                dataSource={r01Result.forced_changes}
                renderItem={(item, idx) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Tag color="red">{item.category}</Tag>}
                      title={
                        <Space>
                          <Text strong>{item.category_name}</Text>
                          <Tag color="volcano">{item.matched_keyword}</Tag>
                        </Space>
                      }
                      description={
                        <div>
                          <Paragraph>{item.description}</Paragraph>
                          <Alert message={`修改建议: ${item.suggestion}`} type="error" showIcon size="small" />
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}

          {/* 🟡 业务确认 */}
          {r01Result.biz_confirm?.length > 0 && (
            <Card
              title={<Space><ExclamationCircleOutlined style={{ color: '#faad14' }} /> 🟡 业务确认（{r01Result.biz_confirm.length} 条）</Space>}
              style={{ marginBottom: 16, borderLeft: '4px solid #faad14' }}
            >
              <List
                dataSource={r01Result.biz_confirm}
                renderItem={(item, idx) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Tag color="orange">{item.category}</Tag>}
                      title={
                        <Space>
                          <Text strong>{item.category_name}</Text>
                          <Tag color="gold">{item.matched_keyword}</Tag>
                        </Space>
                      }
                      description={
                        <div>
                          <Paragraph>{item.description}</Paragraph>
                          <Alert message={`修改建议: ${item.suggestion}`} type="warning" showIcon size="small" />
                          {item.evidence_required && (
                            <Alert
                              message={`需要提供的证据: ${item.evidence_required}`}
                              type="info"
                              showIcon
                              size="small"
                              style={{ marginTop: 8 }}
                            />
                          )}
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}

          {/* ✏️ 文字质检 */}
          {r01Result.text_quality?.length > 0 && (
            <Card
              title={<Space><WarningOutlined style={{ color: '#ff7a45' }} /> ✏️ 文字质检（{r01Result.text_quality.length} 条）</Space>}
              style={{ marginBottom: 16, borderLeft: '4px solid #ff7a45' }}
            >
              <List
                dataSource={r01Result.text_quality}
                renderItem={(item, idx) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Tag color="orange">{item.category}</Tag>}
                      title={item.category_name}
                      description={
                        <Space>
                          <Tag color="volcano">{item.matched_keyword}</Tag>
                          <Text>{item.suggestion}</Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}

          <Divider>R02 证据审查</Divider>

          {/* R02 证据上传区 */}
          <Card title="添加证据材料" style={{ marginBottom: 16 }}>
            <Form layout="inline" onFinish={addEvidence}>
              <Form.Item name="name" label="文件名称" rules={[{ required: true }]}>
                <Input placeholder="如: SGS涂层测试报告.pdf" />
              </Form.Item>
              <Form.Item name="type" label="机构类型">
                <Select style={{ width: 160 }} options={[
                  { value: 'SGS', label: 'SGS' },
                  { value: 'Intertek', label: 'Intertek' },
                  { value: 'TÜV', label: 'TÜV' },
                  { value: 'Bureau Veritas', label: 'Bureau Veritas' },
                  { value: '内部测试', label: '内部测试' },
                  { value: '其他', label: '其他' },
                ]} />
              </Form.Item>
              <Form.Item name="date" label="日期">
                <Input placeholder="如: 2025-06-01" />
              </Form.Item>
              <Form.Item name="covers" label="覆盖风险类别">
                <Select mode="multiple" style={{ width: 200 }} options={[
                  { value: 'I', label: 'I-涂层材料' },
                  { value: 'J', label: 'J-绿色声明' },
                  { value: 'K', label: 'K-促销定价' },
                  { value: 'B', label: 'B-健康功能' },
                  { value: 'D', label: 'D-绝对化用词' },
                  { value: 'F', label: 'F-专利商标' },
                  { value: 'G', label: 'G-中国认证' },
                ]} />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" icon={<ExperimentOutlined />}>添加证据</Button>
              </Form.Item>
            </Form>

            {evidenceList.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Table
                  dataSource={evidenceList.map((e, i) => ({ ...e, key: i }))}
                  columns={[
                    { title: '文件名', dataIndex: 'name', key: 'name' },
                    { title: '机构', dataIndex: 'type', key: 'type' },
                    { title: '日期', dataIndex: 'date', key: 'date' },
                    { title: '覆盖类别', dataIndex: 'covers', key: 'covers', render: (v) => v?.join(', ') || '-' },
                    { title: '操作', key: 'action', render: (_, __, idx) => (
                      <Button type="link" danger onClick={() => delEvidence(idx)}>删除</Button>
                    )}
                  ]}
                  size="small"
                  pagination={false}
                />
              </div>
            )}

            {r01Result.biz_confirm?.length > 0 && (
              <Button
                type="primary"
                size="large"
                icon={<ExperimentOutlined />}
                onClick={onR02Submit}
                loading={r02Loading}
                style={{ marginTop: 16 }}
                block
              >
                开始 R02 证据审查
              </Button>
            )}
          </Card>

          {/* R02 结果 */}
          {r02Result && (
            <Card
              title={<Space><FileProtectOutlined /> R02 证据充分性审查结果</Space>}
              style={{ borderLeft: '4px solid #1890ff' }}
            >
              <Result
                status={r02Result.conclusion === '可上线' ? 'success' : 'warning'}
                title={r02Result.conclusion}
                subTitle={r02Result.conclusion_detail}
              />

              <Table
                dataSource={r02Result.evidence_review?.map((e, i) => ({ ...e, key: i })) || []}
                columns={[
                  { title: '类别', dataIndex: 'category', key: 'category', width: 60 },
                  { title: '风险名称', dataIndex: 'category_name', key: 'category_name', width: 120 },
                  { title: '原始宣称', dataIndex: 'original_claim', key: 'original_claim', width: 100 },
                  { title: '证据文件', dataIndex: 'evidence_files', key: 'evidence_files', render: (v) => v?.join(', ') || '无' },
                  { title: '评级', dataIndex: 'rating', key: 'rating', render: (v) => {
                    const color = v?.includes('✅') ? 'green' : v?.includes('⚠️') ? 'orange' : 'red'
                    return <Tag color={color}>{v}</Tag>
                  }},
                  { title: '说明', dataIndex: 'reason', key: 'reason' },
                  { title: '处理', dataIndex: 'action', key: 'action' },
                ]}
                size="small"
                pagination={false}
              />

              <Descriptions bordered size="small" style={{ marginTop: 16 }}>
                <Descriptions.Item label="✅ 充分">{r02Result.summary?.sufficient}</Descriptions.Item>
                <Descriptions.Item label="⚠️ 部分充分">{r02Result.summary?.partial}</Descriptions.Item>
                <Descriptions.Item label="❌ 不充分">{r02Result.summary?.insufficient}</Descriptions.Item>
              </Descriptions>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

export default AdvancedAudit
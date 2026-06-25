import React, { useState } from 'react'
import {
  Card, Form, Input, Button, Select, Space, Tag, Result, Spin, Typography,
  Divider, List, Alert, message, Collapse, Descriptions, Badge, Segmented, Table, Steps
} from 'antd'
import {
  AuditOutlined, CheckCircleOutlined, ExclamationCircleOutlined, CloseCircleOutlined,
  BookOutlined, FileTextOutlined, BugOutlined, ApiOutlined, ThunderboltOutlined,
  SafetyCertificateOutlined, ExperimentOutlined, FileProtectOutlined, WarningOutlined
} from '@ant-design/icons'
import { auditAPI, advancedAuditAPI } from '../services/api'

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

const TextAudit = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [mode, setMode] = useState('quick')

  // 高级审核状态
  const [r01Result, setR01Result] = useState(null)
  const [r02Loading, setR02Loading] = useState(false)
  const [r02Result, setR02Result] = useState(null)
  const [evidenceList, setEvidenceList] = useState([])

  const onFinish = async (values) => {
    setLoading(true)
    if (mode === 'advanced') {
      setR01Result(null)
      setR02Result(null)
      setEvidenceList([])
    }
    try {
      if (mode === 'quick') {
        const response = await auditAPI.auditText({
          text: values.text,
          regions: values.regions || ['SG', 'MY'],
          advert_name: values.advertName,
          category: values.category || '小家电'
        })
        setResult(response)
      } else {
        const response = await advancedAuditAPI.auditR01({
          text: values.text,
          regions: values.regions || ['SG'],
          category: values.category || '小家电'
        })
        setR01Result(response)
        setResult(null)
      }
      message.success(mode === 'quick' ? '审核完成' : 'R01 扫描完成')
    } catch (error) {
      message.error('审核失败: ' + (error.message || '未知错误'))
    } finally {
      setLoading(false)
    }
  }

  const onR02Submit = async () => {
    if (!evidenceList.length) { message.warning('请至少添加一份证据'); return }
    setR02Loading(true)
    try {
      const response = await advancedAuditAPI.auditR02({ r01_result: r01Result, evidence_files: evidenceList })
      setR02Result(response)
      message.success('R02 证据审查完成')
    } catch (error) { message.error('审查失败: ' + (error.message || '未知错误')) }
    finally { setR02Loading(false) }
  }

  const addEvidence = (values) => {
    setEvidenceList([...evidenceList, {
      name: values.name, type: values.type || '', date: values.date || '', covers: values.covers || []
    }])
    message.success('证据已添加')
  }

  const getStatus = (status) => {
    const map = {
      passed: { status: 'success', title: '通过', subTitle: '广告内容合规' },
      warning: { status: 'warning', title: '需要关注', subTitle: '有风险提示，建议修改' },
      rejected: { status: 'error', title: '未通过', subTitle: '存在强制违规项，必须修改' }
    }
    return map[status] || map.passed
  }

  return (
    <div>
      <Title level={4}><AuditOutlined /> 文字审核</Title>
      <Paragraph type="secondary">支持中英文广告文案合规审核</Paragraph>

      {/* 模式切换 */}
      <Segmented
        value={mode}
        onChange={setMode}
        style={{ marginBottom: 16 }}
        options={[
          { value: 'quick', icon: <ThunderboltOutlined />, label: '快速审核' },
          { value: 'advanced', icon: <SafetyCertificateOutlined />, label: '高级审核 (R01/R02)' }
        ]}
      />

      {mode === 'advanced' && (
        <Steps current={r01Result ? (r02Result ? 2 : 1) : 0} size="small" style={{ marginBottom: 16 }}>
          <Steps.Step title="R01 A-K扫描" icon={<AuditOutlined />} />
          <Steps.Step title="R02 证据审查" icon={<ExperimentOutlined />} />
          <Steps.Step title="合规结论" icon={<FileProtectOutlined />} />
        </Steps>
      )}

      {/* 输入区 */}
      <Card title="输入广告内容" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ regions: ['SG', 'MY'], category: '小家电' }}>
          <Form.Item name="advertName" label="广告名称（选填）">
            <Input placeholder="例如：XX品牌空气净化器新品广告" />
          </Form.Item>
          <Form.Item name="category" label="产品品类">
            <Select options={[
              { value: '小家电', label: '小家电' }, { value: '美妆个护', label: '美妆个护' },
              { value: '婴童', label: '婴童' }, { value: '保健食品', label: '保健食品' },
              { value: '服装', label: '服装' }, { value: '数码', label: '数码' },
            ]} />
          </Form.Item>
          <Form.Item name="text" label="广告文案" rules={[{ required: true, message: '请输入广告文案' }]}>
            <TextArea rows={6} placeholder="请输入待审核的广告文案..." />
          </Form.Item>
          <Form.Item name="regions" label="目标法域" rules={[{ required: true }]}>
            <Select mode="multiple" options={REGIONS} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} size="large" icon={<AuditOutlined />}>
              {mode === 'quick' ? '快速审核' : '开始 R01 扫描'}
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {loading && <div style={{ textAlign: 'center', padding: 40 }}><Spin size="large" tip="审核中..." /></div>}

      {/* ========== 快速审核结果 ========== */}
      {result && !loading && mode === 'quick' && (
        <div>
          <Card title="审核结果" style={{ marginBottom: 24 }}>
            <Result
              status={getStatus(result.overall_status).status}
              title={getStatus(result.overall_status).title}
              subTitle={getStatus(result.overall_status).subTitle}
              extra={<Tag color={RISK_COLORS[result.overall_risk]?.color}>{RISK_COLORS[result.overall_risk]?.text}</Tag>}
            />
          </Card>

          {result.hard_violations?.length > 0 && (
            <Card title={<Space><CloseCircleOutlined style={{ color: '#ff4d4f' }} /> 强制违规 ({result.hard_violations.length}条)</Space>}
              style={{ marginBottom: 16, borderLeft: '4px solid #ff4d4f' }}>
              <List dataSource={result.hard_violations} renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Tag color="red">{item.source === 'official' ? '官方' : '自定义'}</Tag>}
                    title={<Space><Text strong>{item.rule_name}</Text>{item.matched_text && <Tag color="volcano">{item.matched_text}</Tag>}</Space>}
                    description={<div><Paragraph>{item.violation_desc}</Paragraph>{item.suggestion && <Alert message={`建议: ${item.suggestion}`} type="warning" showIcon size="small" />}</div>}
                  />
                </List.Item>
              )} />
            </Card>
          )}

          {result.similar_cases?.length > 0 && (
            <Card title={<Space><FileTextOutlined style={{ color: '#722ed1' }} /> 相似案例 ({result.similar_cases.length})</Space>}
              style={{ borderLeft: '4px solid #722ed1' }}>
              <List dataSource={result.similar_cases} renderItem={(item) => (
                <List.Item><List.Item.Meta avatar={<Tag color="purple">案例</Tag>} title={item.title} description={<Tag color="blue">{item.decision}</Tag>} /></List.Item>
              )} />
            </Card>
          )}

          {/* 调试面板 */}
          <Card size="small" style={{ marginTop: 16 }}
            title={<Space><BugOutlined /><span>调试信息</span><Badge status={result.overall_status === 'rejected' ? 'error' : 'success'} text={`${result.hard_violations?.length || 0}违规 / ${result.similar_cases?.length || 0}案例`} /></Space>}>
            <Descriptions column={2} size="small" bordered>
              <Descriptions.Item label="风险等级">{result.overall_risk}</Descriptions.Item>
              <Descriptions.Item label="审核状态">{result.overall_status}</Descriptions.Item>
              <Descriptions.Item label="违规数">{result.hard_violations?.length || 0}</Descriptions.Item>
              <Descriptions.Item label="案例数">{result.similar_cases?.length || 0}</Descriptions.Item>
            </Descriptions>
            <Collapse ghost style={{ marginTop: 8 }}>
              <Panel header={<Space><ApiOutlined />原始 JSON</Space>} key="raw">
                <pre style={{ background: '#1e1e1e', color: '#d4d4d4', padding: 16, borderRadius: 8, maxHeight: 400, overflow: 'auto', fontSize: 12 }}>
                  {JSON.stringify(result, null, 2)}
                </pre>
              </Panel>
            </Collapse>
          </Card>
        </div>
      )}

      {/* ========== 高级审核 R01/R02 结果 ========== */}
      {r01Result && !loading && mode === 'advanced' && (
        <div>
          <Card style={{ marginBottom: 16, borderLeft: '4px solid ' + (r01Result.overall_risk === 'critical' || r01Result.overall_risk === 'high' ? '#ff4d4f' : r01Result.overall_risk === 'medium' ? '#faad14' : '#52c41a') }}>
            <Result
              status={r01Result.overall_risk === 'critical' || r01Result.overall_risk === 'high' ? 'error' : r01Result.overall_risk === 'medium' ? 'warning' : 'success'}
              title={`R01 扫描完成 — ${RISK_COLORS[r01Result.overall_risk]?.text}`}
              subTitle={`共 ${r01Result.summary.total_issues} 个问题: 🔴${r01Result.summary.forced_count}强制 / 🟡${r01Result.summary.biz_confirm_count}待确认 / 🟢${r01Result.summary.reminder_count}提醒 / ✏️${r01Result.summary.text_quality_count}质检`}
            />
          </Card>

          {r01Result.forced_changes?.length > 0 && (
            <Card title={<Space><CloseCircleOutlined style={{ color: '#ff4d4f' }} /> 🔴 强制修改 ({r01Result.forced_changes.length}条)</Space>}
              style={{ marginBottom: 16, borderLeft: '4px solid #ff4d4f' }}>
              <List dataSource={r01Result.forced_changes} renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Tag color="red">{item.category}</Tag>}
                    title={<Space><Text strong>{item.category_name}</Text><Tag color="volcano">{item.matched_keyword}</Tag></Space>}
                    description={<div><Paragraph>{item.description}</Paragraph><Alert message={`建议: ${item.suggestion}`} type="error" showIcon size="small" /></div>}
                  />
                </List.Item>
              )} />
            </Card>
          )}

          {r01Result.biz_confirm?.length > 0 && (
            <Card title={<Space><ExclamationCircleOutlined style={{ color: '#faad14' }} /> 🟡 业务确认 ({r01Result.biz_confirm.length}条)</Space>}
              style={{ marginBottom: 16, borderLeft: '4px solid #faad14' }}>
              <List dataSource={r01Result.biz_confirm} renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Tag color="orange">{item.category}</Tag>}
                    title={<Space><Text strong>{item.category_name}</Text><Tag color="gold">{item.matched_keyword}</Tag></Space>}
                    description={<div><Paragraph>{item.description}</Paragraph><Alert message={`建议: ${item.suggestion}`} type="warning" showIcon size="small" />
                      {item.evidence_required && <Alert message={`需提供: ${item.evidence_required}`} type="info" showIcon size="small" style={{ marginTop: 8 }} />}</div>}
                  />
                </List.Item>
              )} />
            </Card>
          )}

          {r01Result.text_quality?.length > 0 && (
            <Card title={<Space><WarningOutlined style={{ color: '#ff7a45' }} /> ✏️ 文字质检 ({r01Result.text_quality.length}条)</Space>}
              style={{ marginBottom: 16, borderLeft: '4px solid #ff7a45' }}>
              <List dataSource={r01Result.text_quality} renderItem={(item) => (
                <List.Item><List.Item.Meta avatar={<Tag color="orange">{item.category}</Tag>} title={item.category_name} description={<Tag color="volcano">{item.matched_keyword}</Tag>} /></List.Item>
              )} />
            </Card>
          )}

          <Divider>R02 证据审查</Divider>

          <Card title="添加证据材料" style={{ marginBottom: 16 }}>
            <Form layout="inline" onFinish={addEvidence}>
              <Form.Item name="name" label="文件名" rules={[{ required: true }]}><Input placeholder="SGS报告.pdf" /></Form.Item>
              <Form.Item name="type" label="机构">
                <Select style={{ width: 140 }} options={[
                  { value: 'SGS', label: 'SGS' }, { value: 'Intertek', label: 'Intertek' },
                  { value: 'TÜV', label: 'TÜV' }, { value: 'Bureau Veritas', label: 'BV' },
                  { value: '内部测试', label: '内部测试' }, { value: '其他', label: '其他' },
                ]} />
              </Form.Item>
              <Form.Item name="date" label="日期"><Input placeholder="2025-06-01" /></Form.Item>
              <Form.Item name="covers" label="覆盖类别">
                <Select mode="multiple" style={{ width: 200 }} options={[
                  { value: 'I', label: 'I-涂层' }, { value: 'J', label: 'J-绿色' },
                  { value: 'K', label: 'K-促销' }, { value: 'B', label: 'B-健康' },
                  { value: 'D', label: 'D-绝对化' }, { value: 'F', label: 'F-专利' }, { value: 'G', label: 'G-中国认证' },
                ]} />
              </Form.Item>
              <Form.Item><Button type="primary" htmlType="submit" icon={<ExperimentOutlined />}>添加</Button></Form.Item>
            </Form>
            {evidenceList.length > 0 && (
              <Table style={{ marginTop: 16 }} dataSource={evidenceList.map((e, i) => ({ ...e, key: i }))} size="small" pagination={false}
                columns={[
                  { title: '文件名', dataIndex: 'name' }, { title: '机构', dataIndex: 'type' },
                  { title: '日期', dataIndex: 'date' }, { title: '覆盖', dataIndex: 'covers', render: v => v?.join(', ') || '-' },
                  { title: '操作', render: (_, __, idx) => <Button type="link" danger onClick={() => setEvidenceList(evidenceList.filter((_, i) => i !== idx))}>删除</Button> }
                ]} />
            )}
            {r01Result.biz_confirm?.length > 0 && (
              <Button type="primary" size="large" icon={<ExperimentOutlined />} onClick={onR02Submit} loading={r02Loading} style={{ marginTop: 16 }} block>开始 R02 证据审查</Button>
            )}
          </Card>

          {r02Result && (
            <Card title={<Space><FileProtectOutlined /> R02 证据审查结果</Space>} style={{ borderLeft: '4px solid #1890ff' }}>
              <Result status={r02Result.conclusion === '可上线' ? 'success' : 'warning'} title={r02Result.conclusion} subTitle={r02Result.conclusion_detail} />
              <Table dataSource={r02Result.evidence_review?.map((e, i) => ({ ...e, key: i })) || []} size="small" pagination={false}
                columns={[
                  { title: '类别', dataIndex: 'category', width: 50 },
                  { title: '风险名称', dataIndex: 'category_name', width: 100 },
                  { title: '宣称', dataIndex: 'original_claim', width: 80 },
                  { title: '证据', dataIndex: 'evidence_files', render: v => v?.join(', ') || '无' },
                  { title: '评级', dataIndex: 'rating', render: v => {
                    const c = v?.includes('✅') ? 'green' : v?.includes('⚠️') ? 'orange' : 'red'; return <Tag color={c}>{v}</Tag>
                  }},
                  { title: '说明', dataIndex: 'reason' },
                  { title: '处理', dataIndex: 'action' },
                ]} />
              <Descriptions bordered size="small" style={{ marginTop: 16 }}>
                <Descriptions.Item label="✅ 充分">{r02Result.summary?.sufficient}</Descriptions.Item>
                <Descriptions.Item label="⚠️ 部分">{r02Result.summary?.partial}</Descriptions.Item>
                <Descriptions.Item label="❌ 不充分">{r02Result.summary?.insufficient}</Descriptions.Item>
              </Descriptions>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

export default TextAudit
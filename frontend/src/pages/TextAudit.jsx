import React, { useState } from 'react'
import { Card, Form, Input, Button, Select, Space, Alert, Tag, Result, Spin, Typography, Divider, List, message, Collapse, Descriptions, Badge } from 'antd'
import { AuditOutlined, CheckCircleOutlined, ExclamationCircleOutlined, CloseCircleOutlined, BookOutlined, FileTextOutlined, BugOutlined, ApiOutlined } from '@ant-design/icons'
import { auditAPI } from '../services/api'

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

const TextAudit = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const onFinish = async (values) => {
    setLoading(true)
    try {
      const response = await auditAPI.auditText({
        text: values.text,
        regions: values.regions || ['SG', 'MY'],
        advert_name: values.advertName
      })
      setResult(response)
      message.success('审核完成')
    } catch (error) {
      message.error('审核失败: ' + (error.message || '未知错误'))
    } finally {
      setLoading(false)
    }
  }

  const getRiskLevel = (level) => {
    const map = {
      low: { color: 'success', text: '低风险', icon: <CheckCircleOutlined /> },
      medium: { color: 'warning', text: '中等风险', icon: <ExclamationCircleOutlined /> },
      high: { color: 'error', text: '高风险', icon: <CloseCircleOutlined /> },
      critical: { color: 'error', text: '严重违规', icon: <CloseCircleOutlined /> }
    }
    return map[level] || map.low
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
      <Title level={4}>
        <AuditOutlined /> 文字广告审核
      </Title>

      <Card title="输入广告内容" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ regions: ['SG', 'MY'] }}>
          <Form.Item name="advertName" label="广告名称（选填）">
            <Input placeholder="例如：XX品牌空气净化器新品广告" />
          </Form.Item>
          <Form.Item
            name="text"
            label="广告文案"
            rules={[{ required: true, message: '请输入广告文案' }]}
          >
            <TextArea rows={6} placeholder="请输入待审核的广告文案，例如：本品牌空气净化器最节能，顶级净化效果..." />
          </Form.Item>
          <Form.Item name="regions" label="目标法域" rules={[{ required: true, message: '请选择至少一个目标市场' }]}>
            <Select mode="multiple" placeholder="选择目标市场" options={REGIONS} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} size="large" icon={<AuditOutlined />}>
              开始审核
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {loading && (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" tip="正在审核中..." />
          </div>
        </Card>
      )}

      {result && !loading && (
        <div>
          <Card title="审核结果" style={{ marginBottom: 24 }}>
            <Result
              status={getStatus(result.overall_status).status}
              title={getStatus(result.overall_status).title}
              subTitle={getStatus(result.overall_status).subTitle}
              extra={
                <Space>
                  <Tag color={getRiskLevel(result.overall_risk).color} icon={getRiskLevel(result.overall_risk).icon}>
                    风险等级: {getRiskLevel(result.overall_risk).text}
                  </Tag>
                </Space>
              }
            />
          </Card>

          {result.hard_violations && result.hard_violations.length > 0 && (
            <Card
              title={<Space><CloseCircleOutlined style={{ color: '#ff4d4f' }} /> 强制违规项 ({result.hard_violations.length})</Space>}
              style={{ marginBottom: 16, borderLeft: '4px solid #ff4d4f' }}
            >
              <List
                dataSource={result.hard_violations}
                renderItem={(item, idx) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Tag color="red">{item.source === 'official' ? '官方法规' : '自定义规则'}</Tag>}
                      title={
                        <Space>
                          <Text strong>{item.rule_name || '违规项'}</Text>
                          {item.matched_text && <Tag color="volcano">{item.matched_text}</Tag>}
                        </Space>
                      }
                      description={
                        <div>
                          <Paragraph style={{ marginBottom: 8 }}>{item.violation_desc}</Paragraph>
                          {item.suggestion && (
                            <Alert message={`修改建议: ${item.suggestion}`} type="warning" showIcon size="small" />
                          )}
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}

          {result.soft_references && result.soft_references.length > 0 && (
            <Card
              title={<Space><ExclamationCircleOutlined style={{ color: '#faad14' }} /> 经验提示 ({result.soft_references.length})</Space>}
              style={{ marginBottom: 16, borderLeft: '4px solid #faad14' }}
            >
              <List
                dataSource={result.soft_references}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Tag color="orange">经验</Tag>}
                      title={item.rule_name || '提示'}
                      description={item.violation_desc}
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}

          {result.knowledge_references && result.knowledge_references.length > 0 && (
            <Card
              title={<Space><BookOutlined style={{ color: '#1890ff' }} /> 知识库参考 ({result.knowledge_references.length})</Space>}
              style={{ marginBottom: 16, borderLeft: '4px solid #1890ff' }}
            >
              <List
                dataSource={result.knowledge_references}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Tag color="blue">知识</Tag>}
                      title={item.doc_title}
                      description={
                        <div>
                          <Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 4 }}>
                            {item.relevant_content}
                          </Paragraph>
                          <Text type="secondary">相似度: {(item.similarity * 100).toFixed(1)}%</Text>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}

          {result.similar_cases && result.similar_cases.length > 0 && (
            <Card
              title={<Space><FileTextOutlined style={{ color: '#722ed1' }} /> 相似案例 ({result.similar_cases.length})</Space>}
              style={{ borderLeft: '4px solid #722ed1' }}
            >
              <List
                dataSource={result.similar_cases}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Tag color="purple">案例</Tag>}
                      title={item.title}
                      description={
                        <div>
                          {item.before && item.after && (
                            <Space direction="vertical" size="small">
                              <Text delete type="danger">修改前: {item.before}</Text>
                              <Text mark type="success">修改后: {item.after}</Text>
                            </Space>
                          )}
                          <div style={{ marginTop: 8 }}>处理结果: <Tag color="blue">{item.decision}</Tag></div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          )}

          <Card
            size="small"
            style={{ marginTop: 16 }}
            title={
              <Space>
                <BugOutlined />
                <span>调试信息（API 原始返回）</span>
                <Badge
                  status={result.overall_status === 'rejected' ? 'error' : result.overall_status === 'warning' ? 'warning' : 'success'}
                  text={`${result.hard_violations?.length || 0}项违规 / ${result.soft_references?.length || 0}项提示 / ${result.knowledge_references?.length || 0}条知识 / ${result.similar_cases?.length || 0}个案例`}
                />
              </Space>
            }
          >
            <Descriptions column={2} size="small" bordered>
              <Descriptions.Item label="风险等级">{result.overall_risk}</Descriptions.Item>
              <Descriptions.Item label="审核状态">{result.overall_status}</Descriptions.Item>
              <Descriptions.Item label="强制违规数">{result.hard_violations?.length || 0}</Descriptions.Item>
              <Descriptions.Item label="经验提示数">{result.soft_references?.length || 0}</Descriptions.Item>
              <Descriptions.Item label="知识库匹配数">{result.knowledge_references?.length || 0}</Descriptions.Item>
              <Descriptions.Item label="相似案例数">{result.similar_cases?.length || 0}</Descriptions.Item>
            </Descriptions>
            <Collapse ghost style={{ marginTop: 8 }}>
              <Panel header={<Space><ApiOutlined /> 查看原始 JSON 响应</Space>} key="raw">
                <pre style={{
                  background: '#1e1e1e', color: '#d4d4d4', padding: 16, borderRadius: 8,
                  maxHeight: 400, overflow: 'auto', fontSize: 12, lineHeight: 1.5
                }}>
                  {JSON.stringify(result, null, 2)}
                </pre>
              </Panel>
            </Collapse>
          </Card>
        </div>
      )}
    </div>
  )
}

export default TextAudit
